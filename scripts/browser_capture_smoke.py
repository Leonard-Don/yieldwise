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
PWCLI_COMMAND_TIMEOUT_SECONDS = float(os.environ.get("ATLAS_PWCLI_COMMAND_TIMEOUT", "120"))
# Per-eval cap: each pwcli invocation has ~5s baseline overhead from
# `npx --yes --package @playwright/cli`, so the cap below must leave
# enough headroom for the actual page.evaluate work. Override via
# ATLAS_PWCLI_EVAL_TIMEOUT env var when running on slower machines.
PWCLI_EVAL_TIMEOUT_SECONDS = float(os.environ.get("ATLAS_PWCLI_EVAL_TIMEOUT", "30"))


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


def is_retryable_playwright_command_error(text: str) -> bool:
    retryable_markers = (
        "Execution context was destroyed",
        "Cannot find context with specified id",
        "Target page, context or browser has been closed",
        "Target closed",
        "Session closed",
        "is not open",
    )
    return any(marker in text for marker in retryable_markers)


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


def eval_json(session: str, script: str, *, timeout_seconds: float = 30.0):
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            return extract_playwright_result(
                run_pwcli(session, "eval", script, timeout_seconds=min(remaining, PWCLI_EVAL_TIMEOUT_SECONDS))
            )
        except subprocess.TimeoutExpired as error:
            last_error = error
            time.sleep(0.5)
        except subprocess.CalledProcessError as error:
            message = command_error_text(error)
            if not is_retryable_playwright_command_error(message):
                raise
            last_error = RuntimeError(message)
            time.sleep(0.5)
        except RuntimeError as error:
            message = str(error)
            if not is_retryable_playwright_command_error(message):
                raise
            last_error = error
            time.sleep(0.5)
    if last_error:
        raise last_error
    raise RuntimeError("Playwright eval 超时，且没有可用结果。")


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
        snapshot_captured = False
        for _ in range(3):
            try:
                run_pwcli(session, "snapshot", "--filename", str(staged_target))
                snapshot_captured = True
                break
            except subprocess.TimeoutExpired as error:
                last_error = error
                time.sleep(0.5)
            except subprocess.CalledProcessError as error:
                combined = command_error_text(error)
                if "File access denied" in combined:
                    last_error = error
                    break
                if is_retryable_playwright_command_error(combined):
                    last_error = error
                    time.sleep(0.5)
                    continue
                raise
        if not snapshot_captured:
            continue
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
          const relay = document.querySelector('[data-browser-post-submit-action]');
          const currentTaskRun = document.querySelector('[data-browser-capture-current-task-runs] [data-browser-capture-run-id]');
          const recentRun = document.querySelector('[data-browser-capture-recent-runs] [data-browser-capture-run-id]');
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
            relay: relay
              ? {
                  action: relay.dataset.browserPostSubmitAction || null,
                  taskId: relay.dataset.browserPostSubmitTaskId || null,
                  workflowTaskId: relay.dataset.browserPostSubmitWorkflowTaskId || null,
                  workflowTaskProvided: relay.dataset.browserPostSubmitWorkflowTaskProvided === 'true',
                  resolution: relay.dataset.browserPostSubmitResolution || null,
                  sourceTaskId: relay.dataset.browserPostSubmitSourceTaskId || null,
                  attentionCount: Number(relay.dataset.browserPostSubmitAttentionCount || 0),
                  reason: relay.dataset.browserPostSubmitReason || null,
                  status: relay.dataset.browserPostSubmitStatus || null,
                  text: (relay.textContent || '').trim(),
                }
              : null,
            currentTaskRecentRun: currentTaskRun
              ? {
                  captureRunId: currentTaskRun.dataset.browserCaptureRunId || null,
                  importRunId: currentTaskRun.dataset.browserCaptureImportRunId || null,
                  metricsRunId: currentTaskRun.dataset.browserCaptureMetricsRunId || null,
                }
              : null,
            recentRun: recentRun
              ? {
                  captureRunId: recentRun.dataset.browserCaptureRunId || null,
                  importRunId: recentRun.dataset.browserCaptureImportRunId || null,
                  metricsRunId: recentRun.dataset.browserCaptureMetricsRunId || null,
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
    last_timeout: subprocess.TimeoutExpired | None = None
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
        except subprocess.TimeoutExpired as error:
            last_timeout = error
            if attempt + 1 < max_attempts:
                time.sleep(0.5)
                continue
            raise RuntimeError(
                f"Timed out opening browser session {session!r} for {url} after {attempt + 1} attempts"
            ) from error
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
            if is_retryable_playwright_command_error(error_text) and attempt + 1 < max_attempts:
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
            "limit": "100",
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


def browser_sampling_task_granularity(item: dict | None) -> str:
    if not item:
        return ""
    granularity = str(item.get("targetGranularity") or "").strip().lower()
    if granularity:
        return granularity
    task_id = str(item.get("taskId") or "").strip()
    if task_id.startswith("browser-community::"):
        return "community"
    if task_id.startswith("browser-building::"):
        return "building"
    if task_id.startswith("browser-floor::"):
        return "floor"
    return ""


def resolve_browser_sampling_task(
    atlas_url: str,
    *,
    task_id: str | None = None,
    expected_workflow_action: str | None = None,
) -> tuple[dict, list[dict], str]:
    items = fetch_browser_sampling_pack(atlas_url)
    if not items:
        raise RuntimeError("当前 browser_sampling_pack 为空，无法执行公开页采样 smoke。")

    normalized_task_id = str(task_id or "").strip()
    if normalized_task_id:
        target = next((item for item in items if str(item.get("taskId") or "") == normalized_task_id), None)
        if not target:
            preview = ", ".join(str(item.get("taskId") or "") for item in items[:8])
            raise RuntimeError(
                f"当前 browser_sampling_pack 中找不到任务：{normalized_task_id}。"
                f" 当前可用任务示例：{preview}"
            )
        return target, items, "explicit_task_id"

    normalized_action = str(expected_workflow_action or "").strip()
    if normalized_action == "review_current_capture":
        target = next((item for item in items if browser_sampling_task_granularity(item) == "community"), None)
        if target:
            return target, items, "auto_review_community_task"
    elif normalized_action == "advance_next_capture":
        advance_candidates = [item for item in items if browser_sampling_task_granularity(item) in {"floor", "building"}]
        if advance_candidates:
            target = sorted(
                advance_candidates,
                key=lambda item: (
                    sum(
                        1
                        for peer in items
                        if peer.get("taskId") != item.get("taskId")
                        and peer.get("districtId") == item.get("districtId")
                    ),
                    1 if browser_sampling_task_granularity(item) == "floor" else 0,
                    float(item.get("priorityScore") or 0),
                ),
                reverse=True,
            )[0]
            return target, items, "auto_advance_capture_task"
    elif normalized_action == "stay_current":
        raise RuntimeError("自动选择 stay_current 的任务不可靠，请显式传入 --task-id。")

    return items[0], items, "pack_first_item"


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


def navigate_to_browser_sampling_task(session: str, target: dict) -> dict:
    normalized_task_id = str((target or {}).get("taskId") or "").strip()
    if not normalized_task_id:
        raise RuntimeError("browser capture smoke 缺少有效的目标任务。")
    return eval_json(
        session,
        f"""() => {{
          const target = {json.dumps(target, ensure_ascii=False)};
          if (typeof state === 'undefined') {{
            throw new Error('missing atlas state');
          }}
          state.districtFilter = target.districtId || state.districtFilter || 'all';
          if (!(state.browserSamplingPackItems ?? []).some((item) => item.taskId === target.taskId)) {{
            state.browserSamplingPackItems = [target, ...(state.browserSamplingPackItems ?? [])];
          }}
          selectBrowserSamplingTask(target.taskId, {{
            resetDraft: true,
          }});
          if (typeof render === 'function') {{
            render();
          }}
          const panel = document.querySelector('[data-browser-capture-panel]');
          return {{
            selectedTaskId: state.selectedBrowserSamplingTaskId ?? null,
            districtFilter: state.districtFilter ?? null,
            panelTaskId: panel?.dataset.browserCaptureTaskId || null,
          }};
        }}""",
    )


def wait_for_post_submit_state(
    session: str,
    *,
    expected_source_task_id: str | None = None,
    previous_import_run_id: str | None = None,
    timeout_seconds: float = 120.0,
    interval_seconds: float = 1.0,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_state: dict | None = None
    while time.time() < deadline:
        last_state = browser_capture_dom_state(session)
        submit_button = last_state.get("submitButton") if last_state else {}
        if (
            last_state
            and last_state.get("result")
            and last_state.get("relay")
            and submit_button
            and not submit_button.get("disabled")
            and "生成采样批次并刷新" in submit_button.get("text", "")
        ):
            result = last_state.get("result") or {}
            relay = last_state.get("relay") or {}
            relay_action = relay.get("action")
            relay_task_id = relay.get("taskId")
            relay_source_task_id = relay.get("sourceTaskId")
            current_task_id = last_state.get("taskId")
            result_import_run_id = result.get("importRunId")
            result_task_id = result.get("taskId")
            result_capture_run_id = result.get("captureRunId")
            recent_run = last_state.get("recentRun") or {}
            if expected_source_task_id and (
                relay_source_task_id != expected_source_task_id or result_task_id != expected_source_task_id
            ):
                time.sleep(interval_seconds)
                continue
            if previous_import_run_id and result_import_run_id == previous_import_run_id:
                time.sleep(interval_seconds)
                continue
            if result_capture_run_id and recent_run.get("captureRunId") != result_capture_run_id:
                time.sleep(interval_seconds)
                continue
            if relay_action == "advance_next_capture":
                if relay_task_id and relay_task_id != relay_source_task_id and current_task_id == relay_task_id:
                    return last_state
            elif relay_task_id and current_task_id == relay_task_id:
                return last_state
        time.sleep(interval_seconds)
    raise RuntimeError(f"等待采样提交后的 relay 状态超时。最后状态：{json.dumps(last_state or {}, ensure_ascii=False)}")


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


def clear_browser_capture_feedback(session: str) -> dict:
    return eval_json(
        session,
        """() => {
          if (typeof state === 'undefined') {
            return { cleared: false, reason: 'missing-state' };
          }
          state.lastBrowserCaptureSubmission = null;
          state.lastBrowserCaptureReviewAction = null;
          if (typeof render === 'function') {
            render();
          }
          return { cleared: true };
        }""",
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
    parser.add_argument("--url", default="http://127.0.0.1:8013/backstage/", help="Atlas URL")
    parser.add_argument("--session", default="atlas-smoke", help="Playwright browser session name")
    parser.add_argument("--label", default=None, help="Artifact label prefix. Defaults to timestamp plus session name.")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window. Default is headless.")
    parser.add_argument("--fresh-session", action="store_true", help="Force a new browser session instead of reusing an existing one.")
    parser.add_argument("--navigate", action="store_true", help="Navigate the current browser session to --url before running.")
    parser.add_argument("--sale-price-wan", type=int, default=323)
    parser.add_argument("--rent-price-yuan", type=int, default=12200)
    parser.add_argument("--published-at", default="2026-04-14 14:50:00")
    parser.add_argument("--task-id", default=None, help="Optional browser sampling task id to target explicitly.")
    parser.add_argument(
        "--expected-workflow-action",
        choices=["review_current_capture", "advance_next_capture", "stay_current"],
        default=None,
        help="Optionally assert the post-submit workflow action.",
    )
    parser.add_argument("--keep-session-open", action="store_true", help="Keep the Playwright browser session open after the smoke test.")
    args = parser.parse_args()
    if not args.label:
        session_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(args.session or "atlas-smoke")).strip("-") or "atlas-smoke"
        args.label = f"atlas-browser-capture-smoke-{datetime.now().strftime('%Y%m%d%H%M%S')}-{session_slug}"

    import_before = newest_run_name(IMPORT_RUNS_DIR, "public-browser-sampling-ui-")
    metrics_before = newest_run_name(METRICS_RUNS_DIR, metrics_capture_prefix())
    opened_session = False
    session_meta = None
    selected_task_meta: dict | None = None

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
        target_task = None
        task_selection_reason = None
        if args.task_id or args.expected_workflow_action:
            target_task, _, task_selection_reason = resolve_browser_sampling_task(
                args.url,
                task_id=args.task_id,
                expected_workflow_action=args.expected_workflow_action,
            )
            selected_task_meta = {
                "taskId": target_task.get("taskId"),
                "selectionReason": task_selection_reason,
                "granularity": browser_sampling_task_granularity(target_task),
                "districtId": target_task.get("districtId"),
                "districtName": target_task.get("districtName"),
                "communityName": target_task.get("communityName"),
                "buildingName": target_task.get("buildingName"),
                "floorNo": target_task.get("floorNo"),
            }
        if target_task and pre_state.get("taskId") != target_task.get("taskId"):
            navigate_result = navigate_to_browser_sampling_task(args.session, target_task)
            if navigate_result.get("panelTaskId") != target_task.get("taskId"):
                raise RuntimeError(
                    f"切换公开页采样任务失败：预期 {target_task.get('taskId')}，"
                    f" 实际 {navigate_result.get('panelTaskId') or 'unknown'}"
                )
            rerender_page(args.session)
            pre_snapshot, pre_text, pre_state = wait_for_capture_panel(args.session, args.label, attempts=6)

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

        clear_browser_capture_feedback(args.session)
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
        success_state = wait_for_post_submit_state(
            args.session,
            expected_source_task_id=task.get("taskId"),
            previous_import_run_id=import_before,
        )
        success_6s = take_snapshot(args.session, args.label, "after-6s")
        success_text = snapshot_text(success_6s)
        console_errors = run_pwcli(args.session, "console", "error")

        import_after = newest_run_name(IMPORT_RUNS_DIR, "public-browser-sampling-ui-")
        metrics_after = newest_run_name(METRICS_RUNS_DIR, metrics_capture_prefix())
        latest_result = success_state.get("result") if success_state else None
        relay_state = success_state.get("relay") if success_state else None
        current_task_run = success_state.get("currentTaskRecentRun") if success_state else None
        button_state = success_state.get("submitButton") if success_state else {}
        attention_count = int(latest_result.get("attentionCount") or 0) if latest_result else None

        result = {
            "url": args.url,
            "session": args.session,
            "sessionMeta": session_meta,
            "selectedTask": selected_task_meta,
            "task": task,
            "importRunBefore": import_before,
            "importRunAfter": import_after,
            "metricsRunBefore": metrics_before,
            "metricsRunAfter": metrics_after,
            "domResult": latest_result,
            "relay": relay_state,
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
        if not relay_state:
            raise RuntimeError("提交后没有看到采样接力条。")
        if args.expected_workflow_action and relay_state.get("action") != args.expected_workflow_action:
            raise RuntimeError(
                f"提交后的 workflow action 不符合预期：{relay_state.get('action')} != {args.expected_workflow_action}"
            )
        if not relay_state.get("workflowTaskProvided"):
            raise RuntimeError("采样接力条没有记录后端 workflow.task contract。")
        if relay_state.get("resolution") != "workflow_task":
            raise RuntimeError(f"采样接力条没有使用后端指定的接力目标：{relay_state.get('resolution')}")
        if relay_state.get("workflowTaskId") != relay_state.get("taskId"):
            raise RuntimeError(
                "采样接力条里的 workflow.taskId 与最终接力任务不一致："
                f"{relay_state.get('workflowTaskId')} != {relay_state.get('taskId')}"
            )
        if relay_state.get("attentionCount") != attention_count:
            raise RuntimeError("采样接力条里的 attention 数与结果卡不一致。")
        if relay_state.get("sourceTaskId") and relay_state.get("sourceTaskId") != task.get("taskId"):
            raise RuntimeError(
                f"采样接力条记录的 source task 与提交前任务不一致：{relay_state.get('sourceTaskId')} != {task.get('taskId')}"
            )
        if attention_count:
            if relay_state.get("action") != "review_current_capture":
                raise RuntimeError(f"有 attention 时应停留当前任务回看，实际为：{relay_state.get('action')}")
            if relay_state.get("reason") != "attention_detected":
                raise RuntimeError(f"attention 回看原因不符合预期：{relay_state.get('reason')}")
            if success_state.get("taskId") != task.get("taskId"):
                raise RuntimeError("进入 review_current_capture 后，工作台不应跳离原任务。")
        elif relay_state.get("action") == "advance_next_capture":
            if success_state.get("taskId") != relay_state.get("taskId"):
                raise RuntimeError("自动接力后，当前工作台任务和接力条目标任务不一致。")
            if task.get("taskId") and success_state.get("taskId") == task.get("taskId"):
                raise RuntimeError("自动接力已触发，但工作台仍停留在原任务。")
            if relay_state.get("reason") not in {"same_district_queue_available", "global_queue_available"}:
                raise RuntimeError(f"自动接力原因不符合预期：{relay_state.get('reason')}")
        elif relay_state.get("action") == "stay_current":
            if relay_state.get("reason") != "no_pending_task":
                raise RuntimeError(f"留在当前任务时的原因不符合预期：{relay_state.get('reason')}")
            if success_state.get("taskId") != task.get("taskId"):
                raise RuntimeError("接力条显示 stay_current，但工作台已经跳到了别的任务。")
        else:
            raise RuntimeError(f"未知的采样接力动作：{relay_state.get('action')}")
        if latest_result and not run_id_matches(latest_result.get("importRunId"), import_after):
            raise RuntimeError(f"页面结果里的 import run 与落盘结果不一致：{latest_result.get('importRunId')} != {import_after}")
        if latest_result and not run_id_matches(latest_result.get("metricsRunId"), metrics_after):
            raise RuntimeError(f"页面结果里的 metrics run 与落盘结果不一致：{latest_result.get('metricsRunId')} != {metrics_after}")
        if "Total messages: 0" not in result["consoleErrors"] and "Returning 0 messages" not in result["consoleErrors"]:
            raise RuntimeError("提交后浏览器 console 仍然存在 error。")

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        if opened_session and not args.keep_session_open:
            close_session_quietly(args.session)


if __name__ == "__main__":
    raise SystemExit(main())
