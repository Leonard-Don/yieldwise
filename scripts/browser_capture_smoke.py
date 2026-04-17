#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "playwright"
IMPORT_RUNS_DIR = ROOT_DIR / "tmp" / "import-runs"
METRICS_RUNS_DIR = ROOT_DIR / "tmp" / "metrics-runs"
PWCLI_MAX_SESSION_LENGTH = 17
PWCLI_COMMAND_TIMEOUT_SECONDS = 60.0


def snapshot_stage_candidates(session: str, target_name: str) -> list[Path]:
    preferred = []
    env_stage_dir = os.environ.get("PWCLI_STAGE_DIR")
    if env_stage_dir:
        preferred.append(Path(env_stage_dir) / target_name)
    if session == "default":
        preferred.extend(
            [
                Path.home() / "paper" / ".playwright-cli" / target_name,
                ROOT_DIR / ".playwright-cli" / target_name,
            ]
        )
    else:
        preferred.extend(
            [
                ROOT_DIR / ".playwright-cli" / target_name,
                Path.home() / "paper" / ".playwright-cli" / target_name,
            ]
        )
    deduped: list[Path] = []
    for candidate in preferred:
        if candidate not in deduped:
            deduped.append(candidate)
    return deduped


def shell_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("CODEX_HOME", str(Path.home() / ".codex"))
    env.setdefault("PWCLI", str(Path(env["CODEX_HOME"]) / "skills" / "playwright" / "scripts" / "playwright_cli.sh"))
    return env


def cli_session_name(session: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", session).strip("-") or "default"
    if len(sanitized) <= PWCLI_MAX_SESSION_LENGTH:
        return sanitized
    digest = hashlib.sha1(sanitized.encode("utf-8")).hexdigest()[:6]
    prefix = sanitized[: PWCLI_MAX_SESSION_LENGTH - len(digest) - 1].rstrip("-") or "pw"
    return f"{prefix}-{digest}"


def run_pwcli(session: str, *args: str, timeout_seconds: float | None = PWCLI_COMMAND_TIMEOUT_SECONDS) -> str:
    env = shell_env()
    command = [env["PWCLI"], f"-s={cli_session_name(session)}", *args]
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return completed.stdout


def command_error_text(error: subprocess.CalledProcessError) -> str:
    return f"{error.stdout or ''}\n{error.stderr or ''}".strip()


def is_session_not_open_error(error: subprocess.CalledProcessError) -> bool:
    return "is not open" in command_error_text(error)


def close_session_quietly(session: str) -> None:
    try:
        run_pwcli(session, "close", timeout_seconds=5)
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass


def cleanup_session_artifacts(session: str) -> None:
    close_session_quietly(session)
    cli_session = cli_session_name(session)
    temp_root = Path(tempfile.gettempdir())
    patterns = [
        f"pw-*/cli/*-{cli_session}.sock",
        f"pw-*/cli/*-{cli_session}-*.sock",
    ]
    for pattern in patterns:
        for socket_path in temp_root.glob(pattern):
            try:
                socket_path.unlink(missing_ok=True)
            except OSError:
                pass


def extract_playwright_result(output: str):
    match = re.search(r"### Result\n(.*?)\n### Ran Playwright code", output, re.S)
    if not match:
        raise RuntimeError(f"无法解析 Playwright eval 返回结果：\n{output}")
    return json.loads(match.group(1))


def eval_json(session: str, script: str):
    return extract_playwright_result(run_pwcli(session, "eval", script))


def newest_run_name(directory: Path, prefix: str) -> str | None:
    candidates = [item for item in directory.glob(f"{prefix}*") if item.is_dir()]
    if not candidates:
        return None
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0].name


def metrics_capture_prefix(snapshot_date: str | None = None) -> str:
    date_value = snapshot_date or datetime.now().date().isoformat()
    return f"staged-metrics-{date_value}-capture-"


def snapshot_path(label: str, suffix: str) -> Path:
    return OUTPUT_DIR / f"{label}-{suffix}.yaml"


def take_snapshot(session: str, label: str, suffix: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    target = snapshot_path(label, suffix)
    last_error: Exception | None = None
    for staged_target in snapshot_stage_candidates(session, target.name):
        staged_target.parent.mkdir(parents=True, exist_ok=True)
        try:
            run_pwcli(session, "snapshot", "--filename", str(staged_target))
        except subprocess.CalledProcessError as error:
            combined = f"{error.stdout}\n{error.stderr}"
            if "File access denied" in combined:
                last_error = error
                continue
            raise
        for _ in range(20):
            if staged_target.exists():
                shutil.copy2(staged_target, target)
                return target
            time.sleep(0.1)
        last_error = FileNotFoundError(f"快照命令已返回，但文件未落盘：{staged_target}")
    if last_error:
        raise last_error
    return target


def snapshot_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def rerun_atlas_init(session: str) -> dict:
    return eval_json(session, "() => { void init(); return { retriggered: true, bootError: window.__atlasBootError ?? null }; }")


def rerender_page(session: str) -> dict:
    return eval_json(
        session,
        "() => { render(); return { rendered: true, hasPanel: !!document.querySelector('[data-browser-capture-panel]') }; }",
    )


def browser_capture_dom_state(session: str) -> dict | None:
    return eval_json(
        session,
        """() => {
          const panel = document.querySelector('[data-browser-capture-panel]');
          if (!panel) {
            return null;
          }
          const readValue = (selector) => {
            const element = document.querySelector(selector);
            return element ? element.value ?? '' : '';
          };
          const readText = (selector) => {
            const element = document.querySelector(selector);
            return element ? (element.textContent || '').trim() : '';
          };
          const submitButton = document.querySelector('[data-browser-capture-submit-button]');
          const result = document.querySelector('[data-browser-capture-result="success"]');
          const currentTaskRun = document.querySelector('[data-browser-capture-run-id]');
          return {
            taskId: panel.dataset.browserCaptureTaskId || null,
            communityName: panel.dataset.browserCaptureCommunityName || '',
            buildingName: panel.dataset.browserCaptureBuildingName || '',
            floorNo: panel.dataset.browserCaptureFloorNo || '',
            districtName: panel.dataset.browserCaptureDistrictName || '',
            taskLabel: readText('[data-browser-capture-task-label="true"]'),
            submitButton: {
              text: submitButton ? (submitButton.textContent || '').trim() : '',
              disabled: submitButton ? Boolean(submitButton.disabled) : false,
            },
            draft: {
              saleSourceListingId: readValue('[data-browser-capture-input="sale-sourceListingId"]'),
              rentSourceListingId: readValue('[data-browser-capture-input="rent-sourceListingId"]'),
            },
            result: result
              ? {
                  taskId: result.dataset.browserCaptureResultTaskId || null,
                  importRunId: result.dataset.browserCaptureResultImportRunId || null,
                  captureRunId: result.dataset.browserCaptureResultCaptureRunId || null,
                  metricsRunId: result.dataset.browserCaptureResultMetricsRunId || null,
                  createdAt: result.dataset.browserCaptureResultCreatedAt || null,
                  attentionCount: Number(result.dataset.browserCaptureResultAttentionCount || 0),
                  text: (result.textContent || '').trim(),
                }
              : null,
            currentTaskRecentRun: currentTaskRun
              ? {
                  captureRunId: currentTaskRun.dataset.browserCaptureRunId || null,
                  importRunId: currentTaskRun.dataset.browserCaptureImportRunId || null,
                  metricsRunId: currentTaskRun.dataset.browserCaptureMetricsRunId || null,
                }
              : null,
          };
        }""",
    )


def run_id_matches(reported: str | None, actual: str | None) -> bool:
    if not reported or not actual:
        return True
    return reported == actual or reported.startswith(f"{actual}-")


def open_browser_session(session: str, url: str, *, headed: bool, max_attempts: int = 3) -> dict:
    open_args = [url, "--headed"] if headed else [url]
    actual_session = cli_session_name(session)
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(max_attempts):
        cleanup_session_artifacts(session)
        try:
            run_pwcli(session, "open", *open_args)
            return {
                "requestedSession": session,
                "actualSession": actual_session,
                "attempt": attempt + 1,
                "openedNewSession": True,
                "reusedExistingSession": False,
                "headed": headed,
            }
        except subprocess.CalledProcessError as error:
            last_error = error
            error_text = command_error_text(error)
            if "EADDRINUSE" in error_text and attempt + 1 < max_attempts:
                socket_match = re.search(r"address already in use (/.+?\.sock)", error_text)
                if socket_match:
                    socket_path = Path(socket_match.group(1))
                    try:
                        socket_path.unlink(missing_ok=True)
                    except OSError:
                        pass
                time.sleep(0.5)
                continue
            raise
    assert last_error is not None
    raise last_error


def ensure_browser_session(
    session: str,
    url: str,
    *,
    headed: bool,
    navigate: bool,
    fresh_session: bool = False,
) -> tuple[bool, dict]:
    actual_session = cli_session_name(session)
    if not fresh_session:
        try:
            if navigate:
                run_pwcli(session, "goto", url)
            else:
                run_pwcli(session, "tab-list")
            return False, {
                "requestedSession": session,
                "actualSession": actual_session,
                "attempt": 1,
                "openedNewSession": False,
                "reusedExistingSession": True,
                "headed": headed,
            }
        except subprocess.CalledProcessError as error:
            if not is_session_not_open_error(error):
                raise
    return True, open_browser_session(session, url, headed=headed)


def browser_sampling_pack_url(atlas_url: str) -> str:
    parsed = urlparse(atlas_url)
    query = urlencode(
        {
            "district": "all",
            "min_yield": "0",
            "max_budget": "10000",
            "min_samples": "1",
        }
    )
    return urlunparse((parsed.scheme, parsed.netloc, "/api/browser-sampling-pack", "", query, ""))


def fetch_browser_sampling_pack(atlas_url: str) -> list[dict]:
    url = browser_sampling_pack_url(atlas_url)
    try:
        payload = json.load(urlopen(url))
    except Exception:
        completed = subprocess.run(
            ["curl", "-fsSL", url],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
    return payload.get("items", [])


def inject_browser_sampling_pack(session: str, items: list[dict]) -> dict:
    return eval_json(
        session,
        f"""() => {{
          const items = {json.dumps(items, ensure_ascii=False)};
          state.districtFilter = 'all';
          state.minYield = 0;
          state.maxBudget = 10000;
          state.minSamples = 1;
          state.browserSamplingPackItems = items;
          if (!state.selectedBrowserSamplingTaskId || !items.some((item) => item.taskId === state.selectedBrowserSamplingTaskId)) {{
            state.selectedBrowserSamplingTaskId = items[0]?.taskId ?? null;
          }}
          render();
          return {{
            injected: true,
            count: items.length,
            selectedTaskId: state.selectedBrowserSamplingTaskId,
            hasPanel: !!document.querySelector('[data-browser-capture-panel]'),
          }};
        }}""",
    )


def wait_for_capture_panel(
    session: str,
    label: str,
    *,
    attempts: int = 8,
    delay_seconds: float = 1.0,
) -> tuple[Path, str, dict]:
    last_path: Path | None = None
    last_text = ""
    last_state: dict | None = None
    for attempt in range(1, attempts + 1):
        last_path = take_snapshot(session, label, f"wait-{attempt}")
        last_text = snapshot_text(last_path)
        last_state = browser_capture_dom_state(session)
        if last_state and last_state.get("taskId"):
            return last_path, last_text, last_state
        time.sleep(delay_seconds)
    raise RuntimeError(f"等待页面进入公开页采样工作台超时。最后快照：{last_path}\n{last_text[:500]}")


def fill_capture_form(session: str, values: dict[str, str]) -> dict:
    return eval_json(
        session,
        f"""() => {{
          const values = {json.dumps(values, ensure_ascii=False)};
          for (const [key, value] of Object.entries(values)) {{
            const element = document.querySelector(`[data-browser-capture-input="${{key}}"]`);
            if (!element) {{
              throw new Error(`找不到输入框: ${{key}}`);
            }}
            element.focus();
            element.value = value;
            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
            element.dispatchEvent(new Event('change', {{ bubbles: true }}));
          }}
          return {{ ok: true, filledKeys: Object.keys(values) }};
        }}""",
    )


def click_submit(session: str) -> dict:
    return eval_json(
        session,
        """() => {
          const button = document.querySelector('[data-browser-capture-submit-button]');
          if (!button) {
            throw new Error('找不到公开页采样提交按钮。');
          }
          const beforeText = (button.textContent || '').trim();
          button.click();
          return { clicked: true, beforeText };
        }""",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a browser smoke test for the public browser capture write path.")
    parser.add_argument("--url", default="http://127.0.0.1:8013/", help="Atlas URL")
    parser.add_argument("--session", default="atlas-smoke", help="Playwright browser session name")
    parser.add_argument("--label", default=f"atlas-browser-capture-smoke-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window. Default is headless.")
    parser.add_argument("--fresh-session", action="store_true", help="Force a new browser session instead of reusing an existing one.")
    parser.add_argument("--navigate", action="store_true", help="Navigate the current browser session to --url before running.")
    parser.add_argument("--sale-price-wan", type=int, default=323)
    parser.add_argument("--rent-price-yuan", type=int, default=12200)
    parser.add_argument("--published-at", default="2026-04-14 14:50:00")
    parser.add_argument("--keep-session-open", action="store_true", help="Keep the Playwright browser session open after the smoke test.")
    args = parser.parse_args()

    import_before = newest_run_name(IMPORT_RUNS_DIR, "public-browser-sampling-ui-")
    metrics_before = newest_run_name(METRICS_RUNS_DIR, metrics_capture_prefix())
    opened_session = False
    session_meta = None

    initial_force_navigate = args.navigate or args.session != "default"
    opened_session, session_meta = ensure_browser_session(
        args.session,
        args.url,
        headed=args.headed,
        navigate=initial_force_navigate,
        fresh_session=args.fresh_session,
    )

    def open_and_wait(force_navigate: bool) -> tuple[Path, str, dict]:
        if force_navigate:
            run_pwcli(args.session, "goto", args.url)
            try:
                rerun_atlas_init(args.session)
            except Exception:
                pass
        try:
            rerender_page(args.session)
        except Exception:
            pass
        try:
            return wait_for_capture_panel(args.session, args.label, attempts=10 if force_navigate else 6)
        except RuntimeError:
            items = fetch_browser_sampling_pack(args.url)
            if items:
                inject_browser_sampling_pack(args.session, items)
                rerender_page(args.session)
                return wait_for_capture_panel(args.session, args.label, attempts=4)
            run_pwcli(args.session, "reload")
            try:
                rerender_page(args.session)
            except Exception:
                pass
            try:
                return wait_for_capture_panel(args.session, args.label, attempts=10)
            except RuntimeError:
                items = fetch_browser_sampling_pack(args.url)
                if items:
                    inject_browser_sampling_pack(args.session, items)
                    rerender_page(args.session)
                    return wait_for_capture_panel(args.session, args.label, attempts=4)
                try:
                    rerun_atlas_init(args.session)
                except Exception:
                    pass
                try:
                    rerender_page(args.session)
                except Exception:
                    pass
                return wait_for_capture_panel(args.session, args.label, attempts=10)

    try:
        try:
            pre_snapshot, pre_text, pre_state = open_and_wait(initial_force_navigate)
        except RuntimeError:
            pre_snapshot, pre_text, pre_state = open_and_wait(True)

        timestamp_slug = datetime.now().strftime("%Y%m%d%H%M%S")
        sale_id = f"browser-smoke-sale-{timestamp_slug}"
        rent_id = f"browser-smoke-rent-{timestamp_slug}"
        sale_url = f"https://example.com/sale/{sale_id}"
        rent_url = f"https://example.com/rent/{rent_id}"
        task = {
            "communityName": pre_state.get("communityName", "").strip(),
            "buildingName": pre_state.get("buildingName", "").strip(),
            "floorNo": str(pre_state.get("floorNo", "")).strip(),
            "districtName": pre_state.get("districtName", "").strip(),
            "taskId": pre_state.get("taskId"),
            "taskLabel": pre_state.get("taskLabel", "").strip(),
        }
        floor_label = f"{task['floorNo']}层" if task["floorNo"] else "中层"
        building_label = task["buildingName"] or "待补楼栋"
        sale_raw = f"上海 {task['districtName']} {task['communityName']} {building_label} {floor_label}/16层 89平米 2室2厅 南向 精装 挂牌总价{args.sale_price_wan}万"
        rent_raw = f"上海 {task['districtName']} {task['communityName']} {building_label} {floor_label}/16层 89平米 2室2厅 南向 精装 月租{args.rent_price_yuan}元"

        fill_capture_form(
            args.session,
            {
                "sale-sourceListingId": sale_id,
                "sale-url": sale_url,
                "sale-publishedAt": args.published_at,
                "sale-rawText": sale_raw,
                "rent-sourceListingId": rent_id,
                "rent-url": rent_url,
                "rent-publishedAt": args.published_at,
                "rent-rawText": rent_raw,
            },
        )

        filled_snapshot = take_snapshot(args.session, args.label, "filled")
        click_submit(args.session)

        time.sleep(2)
        success_2s = take_snapshot(args.session, args.label, "after-2s")
        success_state_2s = browser_capture_dom_state(args.session)
        time.sleep(4)
        success_6s = take_snapshot(args.session, args.label, "after-6s")
        success_text = snapshot_text(success_6s)
        success_state = browser_capture_dom_state(args.session)
        console_errors = run_pwcli(args.session, "console", "error")

        import_after = newest_run_name(IMPORT_RUNS_DIR, "public-browser-sampling-ui-")
        metrics_after = newest_run_name(METRICS_RUNS_DIR, metrics_capture_prefix())
        latest_result = success_state.get("result") if success_state else None
        current_task_run = success_state.get("currentTaskRecentRun") if success_state else None
        button_state = success_state.get("submitButton") if success_state else {}
        attention_count = int(latest_result.get("attentionCount") or 0) if latest_result else None

        result = {
            "url": args.url,
            "session": args.session,
            "sessionMeta": session_meta,
            "task": task,
            "importRunBefore": import_before,
            "importRunAfter": import_after,
            "metricsRunBefore": metrics_before,
            "metricsRunAfter": metrics_after,
            "domResult": latest_result,
            "attentionCount": attention_count,
            "currentTaskRecentRun": current_task_run,
            "recentSamplingCount": None if not success_text else None,
            "buttonRecovered": bool(button_state) and not button_state.get("disabled") and "生成采样批次并刷新" in button_state.get("text", ""),
            "consoleErrors": console_errors.strip(),
            "artifacts": {
                "pre": str(pre_snapshot),
                "filled": str(filled_snapshot),
                "after2s": str(success_2s),
                "after6s": str(success_6s),
            },
            "after2sState": success_state_2s,
            "after6sState": success_state,
        }

        if import_after == import_before:
            raise RuntimeError("公开页采样提交后，没有生成新的 import run。")
        if metrics_after == metrics_before:
            raise RuntimeError("公开页采样提交后，没有生成新的 staged metrics run。")
        if not result["buttonRecovered"]:
            raise RuntimeError("提交后按钮没有从“导入中...”恢复。")
        if attention_count:
            raise RuntimeError(f"提交后不应出现 attention，当前为 {attention_count} 条：{latest_result.get('text') if latest_result else ''}")
        if latest_result and not run_id_matches(latest_result.get("importRunId"), import_after):
            raise RuntimeError(f"页面结果里的 import run 与落盘结果不一致：{latest_result.get('importRunId')} != {import_after}")
        if latest_result and not run_id_matches(latest_result.get("metricsRunId"), metrics_after):
            raise RuntimeError(f"页面结果里的 metrics run 与落盘结果不一致：{latest_result.get('metricsRunId')} != {metrics_after}")
        if current_task_run and current_task_run.get("captureRunId") and latest_result and latest_result.get("captureRunId") and current_task_run.get("captureRunId") != latest_result.get("captureRunId"):
            raise RuntimeError("当前任务最近采样的 capture run 与结果卡不一致。")
        if "Total messages: 0" not in result["consoleErrors"] and "Returning 0 messages" not in result["consoleErrors"]:
            raise RuntimeError("提交后浏览器 console 仍然存在 error。")

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        if opened_session and not args.keep_session_open:
            close_session_quietly(args.session)


if __name__ == "__main__":
    raise SystemExit(main())
