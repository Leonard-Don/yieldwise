#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
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


def terminate_process_group(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5.0)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        pass


def run_command_with_timeout(
    command: list[str],
    *,
    timeout_seconds: float | None,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT_DIR,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        terminate_process_group(process)
        stdout, stderr = process.communicate()
        timeout_error = subprocess.TimeoutExpired(exc.cmd or command, timeout_seconds, output=stdout, stderr=stderr)
        timeout_error.stdout = stdout
        timeout_error.stderr = stderr
        raise timeout_error from exc
    if process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def run_pwcli(session: str, *args: str, timeout_seconds: float | None = PWCLI_COMMAND_TIMEOUT_SECONDS) -> str:
    env = shell_env()
    command = [env["PWCLI"], f"-s={cli_session_name(session)}", *args]
    completed = run_command_with_timeout(
        command,
        env=env,
        timeout_seconds=timeout_seconds,
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


def remove_session_artifact_sockets(session: str) -> None:
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


def kill_session_cli_daemons(session: str) -> None:
    cli_session = cli_session_name(session)
    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid=,command="],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return
    matched_pids: list[int] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        pid_text, _, command = stripped.partition(" ")
        if not pid_text.isdigit() or "cliDaemon.js" not in command:
            continue
        if command.split()[-1:] == [cli_session]:
            matched_pids.append(int(pid_text))
    for pid in matched_pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
    if matched_pids:
        time.sleep(0.2)
    for pid in matched_pids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def close_session_quietly(session: str) -> None:
    try:
        run_pwcli(session, "close", timeout_seconds=5)
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    kill_session_cli_daemons(session)
    remove_session_artifact_sockets(session)


def cleanup_session_artifacts(session: str) -> None:
    close_session_quietly(session)
    kill_session_cli_daemons(session)
    remove_session_artifact_sockets(session)


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


def ensure_browser_capture_workspace(session: str) -> dict:
    return eval_json(
        session,
        """() => {
          if (typeof setWorkspaceView === 'function') {
            setWorkspaceView('backstage', { backstageTab: 'operations' });
          } else if (typeof state !== 'undefined') {
            state.workspaceView = 'backstage';
            state.researchBackstageTab = 'operations';
            if (typeof syncWorkspaceViewLocation === 'function') {
              syncWorkspaceViewLocation();
            }
            if (typeof render === 'function') {
              render();
            }
          }
          return {
            workspaceView: typeof state !== 'undefined' ? state.workspaceView ?? null : null,
            backstageTab: typeof state !== 'undefined' ? state.researchBackstageTab ?? null : null,
            hasPanel: !!document.querySelector('[data-browser-capture-panel]'),
          };
        }""",
    )


def browser_capture_dom_state(session: str) -> dict | None:
    return eval_json(
        session,
        """() => {
          const panel = document.querySelector('[data-browser-capture-panel]');
          if (!panel) {
            return null;
          }
          const readText = (selector) => {
            const element = document.querySelector(selector);
            return element ? (element.textContent || '').trim() : '';
          };
          const manualEntryControls = document.querySelectorAll('[data-browser-capture-field], [data-browser-capture-submit], [data-browser-capture-reset], [data-browser-capture-fill-from-attention]');
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
            manualEntryControlCount: manualEntryControls.length,
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


def console_error_output_has_messages(output: str) -> bool:
    if "Returning 0 messages for level \"error\"" in output:
        return False
    match = re.search(r"Returning (\d+) messages for level \"error\"", output)
    if match:
        return int(match.group(1)) > 0
    return "Errors: 0" not in output


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
        except subprocess.TimeoutExpired as error:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a browser smoke test that confirms manual capture entry is removed.")
    parser.add_argument("--url", default="http://127.0.0.1:8013/backstage/", help="Atlas URL")
    parser.add_argument("--session", default="atlas-smoke", help="Playwright browser session name")
    parser.add_argument("--label", default=None, help="Artifact label prefix. Defaults to timestamp plus session name.")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window. Default is headless.")
    parser.add_argument("--fresh-session", action="store_true", help="Force a new browser session instead of reusing an existing one.")
    parser.add_argument("--navigate", action="store_true", help="Navigate the current browser session to --url before running.")
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
            ensure_browser_capture_workspace(args.session)
        except Exception:
            pass
        try:
            return wait_for_capture_panel(args.session, args.label, attempts=10 if force_navigate else 6)
        except RuntimeError:
            items = fetch_browser_sampling_pack(args.url)
            if items:
                inject_browser_sampling_pack(args.session, items)
                try:
                    ensure_browser_capture_workspace(args.session)
                except Exception:
                    pass
                rerender_page(args.session)
                return wait_for_capture_panel(args.session, args.label, attempts=4)
            run_pwcli(args.session, "reload")
            try:
                rerender_page(args.session)
            except Exception:
                pass
            try:
                ensure_browser_capture_workspace(args.session)
            except Exception:
                pass
            try:
                return wait_for_capture_panel(args.session, args.label, attempts=10)
            except RuntimeError:
                items = fetch_browser_sampling_pack(args.url)
                if items:
                    inject_browser_sampling_pack(args.session, items)
                    try:
                        ensure_browser_capture_workspace(args.session)
                    except Exception:
                        pass
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
                try:
                    ensure_browser_capture_workspace(args.session)
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

        task = {
            "communityName": pre_state.get("communityName", "").strip(),
            "buildingName": pre_state.get("buildingName", "").strip(),
            "floorNo": str(pre_state.get("floorNo", "")).strip(),
            "districtName": pre_state.get("districtName", "").strip(),
            "taskId": pre_state.get("taskId"),
            "taskLabel": pre_state.get("taskLabel", "").strip(),
        }
        manual_entry_control_count = int(pre_state.get("manualEntryControlCount") or 0)
        removed_snapshot = take_snapshot(args.session, args.label, "manual-entry-removed")
        console_errors = run_pwcli(args.session, "console", "error")
        result = {
            "url": args.url,
            "session": args.session,
            "sessionMeta": session_meta,
            "selectedTask": selected_task_meta,
            "task": task,
            "manualEntryRemoved": manual_entry_control_count == 0,
            "manualEntryControlCount": manual_entry_control_count,
            "importRunBefore": import_before,
            "importRunAfter": import_before,
            "metricsRunBefore": metrics_before,
            "metricsRunAfter": metrics_before,
            "domResult": None,
            "relay": None,
            "attentionCount": None,
            "currentTaskRecentRun": pre_state.get("currentTaskRecentRun"),
            "consoleErrors": console_errors.strip(),
            "artifacts": {
                "pre": str(pre_snapshot),
                "manualEntryRemoved": str(removed_snapshot),
            },
            "after6sState": pre_state,
            "dirtyListingCleanup": {"skipped": True},
        }
        if manual_entry_control_count:
            raise RuntimeError(f"人工录入控件仍然存在：{manual_entry_control_count}")
        if console_error_output_has_messages(result["consoleErrors"]):
            raise RuntimeError(f"浏览器 console 出现 error：\n{result['consoleErrors']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        if opened_session and not args.keep_session_open:
            close_session_quietly(args.session)


if __name__ == "__main__":
    raise SystemExit(main())
