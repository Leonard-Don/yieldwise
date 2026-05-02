#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import browser_capture_smoke as pw  # noqa: E402


def browser_review_inbox_url(atlas_url: str) -> str:
    parsed = urlparse(atlas_url)
    query = urlencode({"district": "all", "limit": "200"})
    return urlunparse((parsed.scheme, parsed.netloc, "/api/browser-review-inbox", "", query, ""))


def browser_sampling_pack_url(atlas_url: str) -> str:
    parsed = urlparse(atlas_url)
    query = urlencode({"district": "all", "limit": "100"})
    return urlunparse((parsed.scheme, parsed.netloc, "/api/browser-sampling-pack", "", query, ""))


def review_current_task_fixture_url(atlas_url: str) -> str:
    parsed = urlparse(atlas_url)
    return urlunparse((parsed.scheme, parsed.netloc, "/api/dev/browser-review-fixtures/review-current-task", "", "", ""))


def review_fixture_restore_url(atlas_url: str, fixture_id: str) -> str:
    parsed = urlparse(atlas_url)
    return urlunparse(
        (parsed.scheme, parsed.netloc, f"/api/dev/browser-review-fixtures/{fixture_id}", "", "", "")
    )


def fetch_json(url: str) -> dict:
    try:
        return json.load(urlopen(url))
    except Exception:
        completed = subprocess.run(
            ["curl", "-fsSL", url],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)


def request_json(url: str, *, method: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        method=method.upper(),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        curl_command = ["curl", "-fsSL", "-X", method.upper(), "-H", "Accept: application/json"]
        if payload is not None:
            curl_command.extend(["-H", "Content-Type: application/json", "-d", json.dumps(payload, ensure_ascii=False)])
        curl_command.append(url)
        completed = subprocess.run(
            curl_command,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(completed.stdout)


def fetch_browser_review_inbox(atlas_url: str) -> dict:
    return fetch_json(browser_review_inbox_url(atlas_url))


def fetch_browser_sampling_pack(atlas_url: str) -> dict:
    return fetch_json(browser_sampling_pack_url(atlas_url))


def create_review_current_task_fixture(atlas_url: str) -> dict:
    return request_json(review_current_task_fixture_url(atlas_url), method="POST", payload={})


def restore_review_fixture(atlas_url: str, fixture_id: str) -> dict:
    return request_json(review_fixture_restore_url(atlas_url, fixture_id), method="DELETE")


def is_retryable_playwright_error(message: str) -> bool:
    retryable_markers = (
        "Execution context was destroyed",
        "Cannot find context with specified id",
        "Target page, context or browser has been closed",
        "Target closed",
        "Session closed",
        "is not open",
    )
    return any(marker in message for marker in retryable_markers)


def eval_json_with_timeout(session: str, script: str, *, timeout_seconds: float):
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            return pw.extract_playwright_result(
                pw.run_pwcli(session, "eval", script, timeout_seconds=min(remaining, pw.PWCLI_EVAL_TIMEOUT_SECONDS))
            )
        except subprocess.TimeoutExpired as error:
            last_error = error
            time.sleep(0.5)
        except subprocess.CalledProcessError as error:
            message = pw.command_error_text(error)
            if not is_retryable_playwright_error(message):
                raise
            last_error = RuntimeError(message)
            time.sleep(0.5)
        except RuntimeError as error:
            message = str(error)
            if not is_retryable_playwright_error(message):
                raise
            last_error = error
            time.sleep(0.5)
    if last_error:
        raise last_error
    raise RuntimeError("Playwright eval 超时，且没有可用结果。")


def build_review_groups(items: list[dict]) -> tuple[list[dict], dict[str, list[dict]], list[dict]]:
    groups: list[dict] = []
    groups_by_run: dict[str, dict] = {}
    items_by_task: dict[str, list[dict]] = {}
    normalized_items: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        run_id = str(item.get("runId") or "").strip()
        queue_id = str(item.get("queueId") or "").strip()
        task_id = str(item.get("taskId") or "").strip()
        if not run_id or not queue_id or not task_id:
            continue
        normalized_items.append(item)
        group = groups_by_run.get(run_id)
        if group is None:
            group = {
                "runId": run_id,
                "taskId": task_id,
                "districtId": item.get("districtId"),
                "districtName": item.get("districtName"),
                "taskLabel": item.get("taskLabel"),
                "items": [],
            }
            groups_by_run[run_id] = group
            groups.append(group)
        group["items"].append(item)
        items_by_task.setdefault(task_id, []).append(item)
    return groups, items_by_task, normalized_items


def next_same_run_items(group: dict, source_item: dict) -> list[dict]:
    source_queue_id = str(source_item.get("queueId") or "")
    return [item for item in group.get("items") or [] if str(item.get("queueId") or "") != source_queue_id]


def next_same_task_other_run_items(items_by_task: dict[str, list[dict]], source_item: dict) -> list[dict]:
    source_task_id = str(source_item.get("taskId") or "")
    source_run_id = str(source_item.get("runId") or "")
    return [
        item
        for item in items_by_task.get(source_task_id, [])
        if str(item.get("runId") or "") != source_run_id
    ]


def next_other_task_items(items: list[dict], source_item: dict) -> list[dict]:
    source_task_id = str(source_item.get("taskId") or "")
    return [item for item in items if str(item.get("taskId") or "") != source_task_id]


def build_selection(
    source_item: dict,
    *,
    expected_target_item: dict,
    expected_reason: str,
    selection_reason: str,
) -> dict:
    return {
        "sourceItem": source_item,
        "expectedTargetItem": expected_target_item,
        "expectedReason": expected_reason,
        "selectionReason": selection_reason,
    }


def task_supports_review_current_task(pack_by_task: dict[str, dict], source_item: dict) -> bool:
    task_snapshot = pack_by_task.get(str(source_item.get("taskId") or ""))
    return bool(task_snapshot) and int(task_snapshot.get("pendingAttentionCount") or 0) > 0


def resolve_browser_review_target(
    atlas_url: str,
    *,
    expected_workflow_action: str,
    run_id: str | None = None,
    queue_id: str | None = None,
    task_id: str | None = None,
) -> tuple[dict, dict]:
    inbox_payload = fetch_browser_review_inbox(atlas_url)
    pack_payload = fetch_browser_sampling_pack(atlas_url)
    items = [item for item in (inbox_payload.get("items") or []) if isinstance(item, dict)]
    groups, items_by_task, ordered_items = build_review_groups(items)
    pack_by_task = {
        str(item.get("taskId") or ""): item
        for item in (pack_payload.get("items") or [])
        if isinstance(item, dict) and item.get("taskId")
    }
    if not ordered_items:
        raise RuntimeError("当前 browser review inbox 为空，无法执行 review smoke。")

    def explicit_source_item() -> dict | None:
        normalized_run_id = str(run_id or "").strip()
        normalized_queue_id = str(queue_id or "").strip()
        normalized_task_id = str(task_id or "").strip()
        if not normalized_run_id and not normalized_queue_id and not normalized_task_id:
            return None
        for item in ordered_items:
            if normalized_run_id and str(item.get("runId") or "") != normalized_run_id:
                continue
            if normalized_queue_id and str(item.get("queueId") or "") != normalized_queue_id:
                continue
            if normalized_task_id and str(item.get("taskId") or "") != normalized_task_id:
                continue
            return item
        raise RuntimeError(
            "显式指定的 review 目标不存在："
            f" run_id={normalized_run_id or '-'} queue_id={normalized_queue_id or '-'} task_id={normalized_task_id or '-'}"
        )

    def selection_for_source(source_item: dict, *, selection_reason: str) -> dict:
        source_run_id = str(source_item.get("runId") or "")
        source_group = next((group for group in groups if str(group.get("runId") or "") == source_run_id), None)
        if source_group is None:
            raise RuntimeError(f"找不到 source run group：{source_run_id}")
        same_run_items = next_same_run_items(source_group, source_item)
        remaining_same_task_items = [
            item
            for item in items_by_task.get(str(source_item.get("taskId") or ""), [])
            if str(item.get("queueId") or "") != str(source_item.get("queueId") or "")
        ]
        same_task_other_run_items = [
            item for item in remaining_same_task_items if str(item.get("runId") or "") != source_run_id
        ]
        other_task_items = next_other_task_items(ordered_items, source_item)
        same_district_other_task_items = [
            item for item in other_task_items if str(item.get("districtId") or "") == str(source_item.get("districtId") or "")
        ]
        supports_current_task = task_supports_review_current_task(pack_by_task, source_item)

        if expected_workflow_action == "review_current_run":
            if not same_run_items:
                raise RuntimeError("目标不满足 review_current_run：当前 run 只有一条 pending item。")
            return build_selection(
                source_item,
                expected_target_item=same_run_items[0],
                expected_reason="current_run_pending_remaining",
                selection_reason=selection_reason,
            )

        if expected_workflow_action == "review_current_task":
            if same_run_items:
                raise RuntimeError("目标不满足 review_current_task：当前 run 还有其他 pending item，会先命中 review_current_run。")
            if not same_task_other_run_items:
                raise RuntimeError("目标不满足 review_current_task：当前任务没有其他 run 的 pending item。")
            if not supports_current_task:
                raise RuntimeError("目标不满足 review_current_task：当前任务不在 live browser_sampling_pack 的待复核范围内。")
            return build_selection(
                source_item,
                expected_target_item=remaining_same_task_items[0],
                expected_reason="current_task_pending_remaining",
                selection_reason=selection_reason,
            )

        if expected_workflow_action == "advance_next_review":
            if same_run_items:
                raise RuntimeError("目标不满足 advance_next_review：当前 run 还有其他 pending item，会先命中 review_current_run。")
            if same_task_other_run_items and supports_current_task:
                raise RuntimeError("目标不满足 advance_next_review：当前任务还有其他 run 的 pending item，会先命中 review_current_task。")
            if not other_task_items:
                raise RuntimeError("目标不满足 advance_next_review：收件箱里没有其他任务可接力。")
            expected_target_item = same_district_other_task_items[0] if same_district_other_task_items else other_task_items[0]
            return build_selection(
                source_item,
                expected_target_item=expected_target_item,
                expected_reason="same_district_review_available" if same_district_other_task_items else "global_review_available",
                selection_reason=selection_reason,
            )

        raise RuntimeError(f"暂不支持的 review workflow action: {expected_workflow_action}")

    source_item = explicit_source_item()
    if source_item is not None:
        return selection_for_source(source_item, selection_reason="explicit_review_target"), inbox_payload

    if expected_workflow_action == "review_current_run":
        for group in groups:
            group_items = group.get("items") or []
            if len(group_items) > 1:
                return selection_for_source(group_items[0], selection_reason="auto_review_current_run"), inbox_payload
        raise RuntimeError("当前收件箱里没有满足 review_current_run 的 run。")

    if expected_workflow_action == "review_current_task":
        for group in groups:
            group_items = group.get("items") or []
            if len(group_items) != 1:
                continue
            source_item = group_items[0]
            if (
                next_same_task_other_run_items(items_by_task, source_item)
                and task_supports_review_current_task(pack_by_task, source_item)
            ):
                return selection_for_source(source_item, selection_reason="auto_review_current_task"), inbox_payload
        raise RuntimeError("当前收件箱里没有满足 review_current_task 的任务。")

    if expected_workflow_action == "advance_next_review":
        for group in groups:
            group_items = group.get("items") or []
            if len(group_items) != 1:
                continue
            source_item = group_items[0]
            if next_same_task_other_run_items(items_by_task, source_item) and task_supports_review_current_task(pack_by_task, source_item):
                continue
            if next_other_task_items(ordered_items, source_item):
                return selection_for_source(source_item, selection_reason="auto_advance_next_review"), inbox_payload
        raise RuntimeError("当前收件箱里没有满足 advance_next_review 的任务。")

    raise RuntimeError(f"暂不支持的 review workflow action: {expected_workflow_action}")


def browser_review_dom_state(session: str) -> dict | None:
    return eval_json_with_timeout(
        session,
        """() => {
          const panel = document.querySelector('[data-browser-capture-panel]');
          const reviewPanel = document.querySelector('[data-browser-review-current-run-id]');
          const reviewRelay = document.querySelector('[data-browser-review-action]');
          const inbox = document.querySelector('[data-browser-review-inbox-count]');
          const queueCards = [...document.querySelectorAll('[data-browser-capture-review-queue-item]')];
          return {
            taskId: panel?.dataset.browserCaptureTaskId || null,
            taskLabel: document.querySelector('[data-browser-capture-task-label="true"]')?.textContent?.trim() || null,
            reviewPanelRunId: reviewPanel?.dataset.browserReviewCurrentRunId || null,
            reviewPanelPendingCount: Number(reviewPanel?.dataset.browserReviewCurrentPendingCount || 0),
            reviewInboxCount: Number(inbox?.dataset.browserReviewInboxCount || 0),
            reviewInboxVisibleCount: document.querySelectorAll('[data-browser-review-inbox-item-id]').length,
            reviewInboxActiveItemId: document.querySelector('[data-browser-review-inbox-item-id].is-active')?.dataset.browserReviewInboxItemId || null,
            selectedReviewQueueId: document.querySelector('[data-browser-capture-review-queue-item].is-related')?.dataset.browserCaptureReviewQueueItem || null,
            visibleReviewQueueIds: queueCards.map((item) => item.dataset.browserCaptureReviewQueueItem || null).filter(Boolean),
            reviewRelay: reviewRelay
              ? {
                  action: reviewRelay.dataset.browserReviewAction || null,
                  runId: reviewRelay.dataset.browserReviewRunId || null,
                  queueId: reviewRelay.dataset.browserReviewQueueId || null,
                  workflowRunId: reviewRelay.dataset.browserReviewWorkflowRunId || null,
                  workflowQueueId: reviewRelay.dataset.browserReviewWorkflowQueueId || null,
                  workflowTaskId: reviewRelay.dataset.browserReviewWorkflowTaskId || null,
                  workflowItemProvided: reviewRelay.dataset.browserReviewWorkflowItemProvided === 'true',
                  resolution: reviewRelay.dataset.browserReviewResolution || null,
                  reason: reviewRelay.dataset.browserReviewReason || null,
                  targetTaskId: reviewRelay.dataset.browserReviewTargetTaskId || null,
                  targetRunId: reviewRelay.dataset.browserReviewTargetRunId || null,
                  targetQueueId: reviewRelay.dataset.browserReviewTargetQueueId || null,
                  pendingCount: Number(reviewRelay.dataset.browserReviewPendingCount || 0),
                  text: (reviewRelay.textContent || '').trim(),
                }
              : null,
          };
        }""",
        timeout_seconds=30.0,
    )


def wait_for_review_ready(session: str, *, timeout_seconds: float = 30.0, interval_seconds: float = 1.0) -> dict:
    deadline = time.time() + timeout_seconds
    last_state: dict | None = None
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            last_state = browser_review_dom_state(session)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, RuntimeError) as error:
            last_error = error
            time.sleep(interval_seconds)
            continue
        if (
            last_state
            and last_state.get("taskId")
            and (last_state.get("reviewInboxCount") or 0) > 0
            and (last_state.get("reviewInboxVisibleCount") or 0) > 0
        ):
            return last_state
        time.sleep(interval_seconds)
    if last_error:
        raise RuntimeError(
            f"等待 review inbox 加载超时。最后状态：{json.dumps(last_state or {}, ensure_ascii=False)} last_error={last_error}"
        ) from last_error
    raise RuntimeError(f"等待 review inbox 加载超时。最后状态：{json.dumps(last_state or {}, ensure_ascii=False)}")


def open_and_wait_review_page(
    session: str,
    url: str,
    label: str,
    *,
    headed: bool,
    fresh_session: bool,
    navigate: bool,
) -> tuple[bool, dict, dict, Path]:
    initial_force_navigate = navigate or session != "default"
    opened_session, session_meta = pw.ensure_browser_session(
        session,
        url,
        headed=headed,
        navigate=initial_force_navigate,
        fresh_session=fresh_session,
    )

    def open_and_wait(force_navigate: bool) -> tuple[dict, Path]:
        if force_navigate:
            pw.run_pwcli(session, "goto", url)
            try:
                pw.rerun_atlas_init(session)
            except Exception:
                pass
        try:
            pw.rerender_page(session)
        except Exception:
            pass
        try:
            pre_snapshot, _, _ = pw.wait_for_capture_panel(session, label, attempts=10 if force_navigate else 6)
        except RuntimeError:
            items = pw.fetch_browser_sampling_pack(url)
            if items:
                pw.inject_browser_sampling_pack(session, items)
                pw.rerender_page(session)
                pre_snapshot, _, _ = pw.wait_for_capture_panel(session, label, attempts=4)
            else:
                pw.run_pwcli(session, "reload")
                try:
                    pw.rerender_page(session)
                except Exception:
                    pass
                pre_snapshot, _, _ = pw.wait_for_capture_panel(session, label, attempts=10)
        try:
            pre_state = wait_for_review_ready(session)
        except RuntimeError:
            pw.run_pwcli(session, "reload")
            try:
                pw.rerun_atlas_init(session)
            except Exception:
                pass
            try:
                pw.rerender_page(session)
            except Exception:
                pass
            pre_snapshot, _, _ = pw.wait_for_capture_panel(session, label, attempts=10)
            pre_state = wait_for_review_ready(session)
        return pre_state, pre_snapshot

    try:
        pre_state, pre_snapshot = open_and_wait(initial_force_navigate)
    except RuntimeError:
        pre_state, pre_snapshot = open_and_wait(True)

    return opened_session, session_meta, pre_state, pre_snapshot


def task_snapshot_from_review_item(item: dict) -> dict:
    task = dict(item.get("task") or {})
    task.setdefault("taskId", item.get("taskId"))
    task.setdefault("districtId", item.get("districtId"))
    task.setdefault("districtName", item.get("districtName"))
    task.setdefault("communityId", item.get("communityId"))
    task.setdefault("communityName", item.get("communityName"))
    task.setdefault("buildingId", item.get("buildingId"))
    task.setdefault("buildingName", item.get("buildingName"))
    task.setdefault("floorNo", item.get("floorNo"))
    task.setdefault("taskType", item.get("taskType"))
    task.setdefault("taskTypeLabel", item.get("taskTypeLabel"))
    task.setdefault("targetGranularity", item.get("targetGranularity"))
    task.setdefault("focusScope", item.get("focusScope"))
    task.setdefault("priorityScore", item.get("priorityScore"))
    task.setdefault("priorityLabel", item.get("priorityLabel"))
    task.setdefault("pendingReviewRunId", item.get("runId"))
    task.setdefault("pendingReviewQueueId", item.get("queueId"))
    task.setdefault("pendingAttentionCount", item.get("taskPendingAttentionCount"))
    task.setdefault("taskLifecycleStatus", item.get("taskLifecycleStatus") or "needs_review")
    task.setdefault("taskLifecycleLabel", item.get("taskLifecycleLabel") or "已采待复核")
    return task


def select_source_review_task(session: str, item: dict) -> dict:
    task = task_snapshot_from_review_item(item)
    navigate_result = pw.navigate_to_browser_sampling_task(session, task)
    review_result = eval_json_with_timeout(
        session,
        f"""async () => {{
          const runId = {json.dumps(str(item.get("runId") or ""))};
          const queueId = {json.dumps(str(item.get("queueId") or ""))};
          if (typeof loadSelectedBrowserCaptureRunDetail !== 'function') {{
            throw new Error('missing loadSelectedBrowserCaptureRunDetail');
          }}
          await loadSelectedBrowserCaptureRunDetail(runId, {{
            preferredQueueId: queueId,
          }});
          return {{
            reviewPanelRunId: document.querySelector('[data-browser-review-current-run-id]')?.dataset.browserReviewCurrentRunId || null,
            selectedReviewQueueId: document.querySelector('[data-browser-capture-review-queue-item].is-related')?.dataset.browserCaptureReviewQueueItem || null,
          }};
        }}""",
        timeout_seconds=180.0,
    )
    return {
        **navigate_result,
        **review_result,
    }


def wait_for_selected_task(
    session: str,
    *,
    target_task_id: str,
    target_run_id: str,
    target_queue_id: str,
    timeout_seconds: float = 30.0,
    interval_seconds: float = 0.5,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_state: dict | None = None
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            last_state = browser_review_dom_state(session)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, RuntimeError) as error:
            last_error = error
            time.sleep(interval_seconds)
            continue
        if (
            last_state
            and last_state.get("taskId") == target_task_id
            and last_state.get("reviewPanelRunId") == target_run_id
            and target_queue_id in (last_state.get("visibleReviewQueueIds") or [])
        ):
            return last_state
        time.sleep(interval_seconds)
    if last_error:
        raise RuntimeError(
            "等待 source review queue 展开超时："
            f" task={target_task_id} run={target_run_id} queue={target_queue_id}"
            f" state={json.dumps(last_state or {}, ensure_ascii=False)} last_error={last_error}"
        ) from last_error
    raise RuntimeError(
        "等待 source review queue 展开超时："
        f" task={target_task_id} run={target_run_id} queue={target_queue_id}"
        f" state={json.dumps(last_state or {}, ensure_ascii=False)}"
    )


def clear_browser_review_feedback(session: str) -> dict:
    try:
        return eval_json_with_timeout(
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
            timeout_seconds=180.0,
        )
    except Exception as error:
        return {
            "cleared": False,
            "reason": f"best_effort_failed:{error.__class__.__name__}",
        }


def apply_review_action(session: str, *, run_id: str, queue_id: str, review_status: str) -> dict:
    resolution_note = (
        "review smoke: 已由脚本验证并标记已修正。"
        if review_status == "resolved"
        else "review smoke: 已由脚本验证并标记豁免。"
    )
    return eval_json_with_timeout(
        session,
        f"""async () => {{
          const runId = {json.dumps(run_id)};
          const queueId = {json.dumps(queue_id)};
          const reviewStatus = {json.dumps(review_status)};
          const resolutionNotes = {json.dumps(resolution_note)};
          if (typeof reviewBrowserCaptureQueueItem !== 'function') {{
            throw new Error('missing reviewBrowserCaptureQueueItem');
          }}
          const result = await reviewBrowserCaptureQueueItem(runId, queueId, {{
            status: reviewStatus,
            resolutionNotes,
          }});
          return {{
            clicked: true,
            runId,
            queueId,
            status: reviewStatus,
            result: result || null,
            taskId: document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null,
          }};
        }}""",
        timeout_seconds=180.0,
    )


def wait_for_post_review_state(
    session: str,
    *,
    expected_workflow_action: str,
    expected_reason: str,
    source_item: dict,
    expected_target_item: dict,
    timeout_seconds: float = 30.0,
    interval_seconds: float = 0.5,
) -> dict:
    deadline = time.time() + timeout_seconds
    last_state: dict | None = None
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            last_state = browser_review_dom_state(session)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, RuntimeError) as error:
            last_error = error
            time.sleep(interval_seconds)
            continue
        relay = (last_state or {}).get("reviewRelay") or {}
        if (
            relay.get("action") != expected_workflow_action
            or relay.get("reason") != expected_reason
            or relay.get("runId") != source_item.get("runId")
            or relay.get("queueId") != source_item.get("queueId")
            or relay.get("resolution") != "workflow_item"
            or relay.get("workflowItemProvided") is not True
            or relay.get("workflowTaskId") != expected_target_item.get("taskId")
            or relay.get("workflowRunId") != expected_target_item.get("runId")
            or relay.get("workflowQueueId") != expected_target_item.get("queueId")
            or relay.get("targetTaskId") != expected_target_item.get("taskId")
            or relay.get("targetRunId") != expected_target_item.get("runId")
            or relay.get("targetQueueId") != expected_target_item.get("queueId")
        ):
            time.sleep(interval_seconds)
            continue

        if expected_workflow_action == "review_current_run":
            if last_state.get("taskId") == source_item.get("taskId"):
                return last_state
        elif expected_workflow_action == "review_current_task":
            if last_state.get("taskId") == source_item.get("taskId"):
                return last_state
        elif expected_workflow_action == "advance_next_review":
            if (
                last_state.get("taskId") == expected_target_item.get("taskId")
                and last_state.get("taskId") != source_item.get("taskId")
            ):
                return last_state
        time.sleep(interval_seconds)
    if last_error:
        raise RuntimeError(
            f"等待 review relay 状态超时。最后状态：{json.dumps(last_state or {}, ensure_ascii=False)} last_error={last_error}"
        ) from last_error
    raise RuntimeError(f"等待 review relay 状态超时。最后状态：{json.dumps(last_state or {}, ensure_ascii=False)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a browser smoke test for the browser review relay workflow.")
    parser.add_argument("--url", default="http://127.0.0.1:8013/backstage/", help="Atlas URL")
    parser.add_argument("--session", default="atlas-review-smoke", help="Playwright browser session name")
    parser.add_argument("--label", default=None, help="Artifact label prefix. Defaults to timestamp plus session name.")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window. Default is headless.")
    parser.add_argument("--fresh-session", action="store_true", help="Force a new browser session instead of reusing an existing one.")
    parser.add_argument("--navigate", action="store_true", help="Navigate the current browser session to --url before running.")
    parser.add_argument("--run-id", default=None, help="Optional run id to target explicitly.")
    parser.add_argument("--queue-id", default=None, help="Optional queue id to target explicitly.")
    parser.add_argument("--task-id", default=None, help="Optional task id to target explicitly.")
    parser.add_argument(
        "--expected-workflow-action",
        choices=["review_current_run", "review_current_task", "advance_next_review"],
        required=True,
        help="Assert the review relay workflow action.",
    )
    parser.add_argument(
        "--review-status",
        choices=["resolved", "waived"],
        default="resolved",
        help="Review action to apply. Default is resolved to avoid prompt-driven variance.",
    )
    parser.add_argument("--keep-session-open", action="store_true", help="Keep the Playwright browser session open after the smoke test.")
    args = parser.parse_args()

    if not args.label:
        session_slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(args.session or "atlas-review-smoke")).strip("-") or "atlas-review-smoke"
        args.label = f"atlas-browser-review-smoke-{datetime.now().strftime('%Y%m%d%H%M%S')}-{session_slug}"

    opened_session = False
    session_meta = None
    selection: dict | None = None
    inbox_payload: dict | None = None
    fixture_payload: dict | None = None
    result: dict | None = None
    try:
        if (
            args.expected_workflow_action == "review_current_task"
            and not any([args.run_id, args.queue_id, args.task_id])
        ):
            fixture_payload = create_review_current_task_fixture(args.url)
            selection = {
                "sourceItem": fixture_payload["sourceItem"],
                "expectedTargetItem": fixture_payload["expectedTargetItem"],
                "expectedReason": "current_task_pending_remaining",
                "selectionReason": fixture_payload.get("selectionReason") or "seeded_review_current_task_fixture",
            }
            inbox_payload = {
                "summary": fixture_payload.get("reviewInboxSummary") or {},
                "items": [],
            }
        else:
            selection, inbox_payload = resolve_browser_review_target(
                args.url,
                expected_workflow_action=args.expected_workflow_action,
                run_id=args.run_id,
                queue_id=args.queue_id,
                task_id=args.task_id,
            )

        source_item = selection["sourceItem"]
        expected_target_item = selection["expectedTargetItem"]
        opened_session, session_meta, pre_state, pre_snapshot = open_and_wait_review_page(
            args.session,
            args.url,
            args.label,
            headed=args.headed,
            fresh_session=args.fresh_session,
            navigate=args.navigate,
        )
        focus_result = select_source_review_task(args.session, source_item)
        focused_state = wait_for_selected_task(
            args.session,
            target_task_id=str(source_item.get("taskId") or ""),
            target_run_id=str(source_item.get("runId") or ""),
            target_queue_id=str(source_item.get("queueId") or ""),
        )
        clear_browser_review_feedback(args.session)
        focused_snapshot = pw.take_snapshot(args.session, args.label, "focused")

        action_result = apply_review_action(
            args.session,
            run_id=str(source_item.get("runId") or ""),
            queue_id=str(source_item.get("queueId") or ""),
            review_status=args.review_status,
        )
        if not action_result.get("clicked"):
            raise RuntimeError(f"触发 review 动作失败：{json.dumps(action_result, ensure_ascii=False)}")

        time.sleep(2)
        after_2s_snapshot = pw.take_snapshot(args.session, args.label, "after-2s")
        after_2s_state = browser_review_dom_state(args.session)
        final_state = wait_for_post_review_state(
            args.session,
            expected_workflow_action=args.expected_workflow_action,
            expected_reason=selection["expectedReason"],
            source_item=source_item,
            expected_target_item=expected_target_item,
        )
        after_6s_snapshot = pw.take_snapshot(args.session, args.label, "after-6s")
        console_errors = pw.run_pwcli(args.session, "console", "error")

        relay = (final_state or {}).get("reviewRelay") or {}
        inbox_before = int(focused_state.get("reviewInboxCount") or 0)
        inbox_after = int(final_state.get("reviewInboxCount") or 0)

        if relay.get("action") != args.expected_workflow_action:
            raise RuntimeError(
                f"review relay action 不符合预期：{relay.get('action')} != {args.expected_workflow_action}"
            )
        if relay.get("reason") != selection["expectedReason"]:
            raise RuntimeError(
                f"review relay reason 不符合预期：{relay.get('reason')} != {selection['expectedReason']}"
            )
        if relay.get("resolution") != "workflow_item" or relay.get("workflowItemProvided") is not True:
            raise RuntimeError(f"review relay 没有使用后端 workflow.item：{json.dumps(relay, ensure_ascii=False)}")
        if relay.get("runId") != source_item.get("runId") or relay.get("queueId") != source_item.get("queueId"):
            raise RuntimeError("review relay 记录的 source run / queue 与实际处理目标不一致。")
        if relay.get("targetTaskId") != expected_target_item.get("taskId"):
            raise RuntimeError("review relay 的目标 task 与预期不一致。")
        if relay.get("targetRunId") != expected_target_item.get("runId"):
            raise RuntimeError("review relay 的目标 run 与预期不一致。")
        if relay.get("targetQueueId") != expected_target_item.get("queueId"):
            raise RuntimeError("review relay 的目标 queue 与预期不一致。")
        if relay.get("workflowTaskId") != expected_target_item.get("taskId"):
            raise RuntimeError("review relay 的 workflow.taskId 与预期不一致。")
        if relay.get("workflowRunId") != expected_target_item.get("runId"):
            raise RuntimeError("review relay 的 workflow.runId 与预期不一致。")
        if relay.get("workflowQueueId") != expected_target_item.get("queueId"):
            raise RuntimeError("review relay 的 workflow.queueId 与预期不一致。")
        if inbox_after != max(inbox_before - 1, 0):
            raise RuntimeError(f"review inbox 数量没有按预期减少：{inbox_before} -> {inbox_after}")
        if "Total messages: 0" not in console_errors and "Returning 0 messages" not in console_errors:
            raise RuntimeError("review smoke 后浏览器 console 仍然存在 error。")

        result = {
            "url": args.url,
            "session": args.session,
            "sessionMeta": session_meta,
            "inboxSummary": (inbox_payload or {}).get("summary") or {},
            "selectionReason": selection["selectionReason"],
            "fixtureApplied": bool(fixture_payload),
            "fixtureId": fixture_payload.get("fixtureId") if fixture_payload else None,
            "reviewStatus": args.review_status,
            "expectedWorkflowAction": args.expected_workflow_action,
            "expectedWorkflowReason": selection["expectedReason"],
            "sourceItem": source_item,
            "expectedTargetItem": expected_target_item,
            "preState": pre_state,
            "focusedState": focused_state,
            "focusResult": focus_result,
            "actionResult": action_result,
            "after2sState": after_2s_state,
            "after6sState": final_state,
            "relay": relay,
            "reviewInboxCountBefore": inbox_before,
            "reviewInboxCountAfter": inbox_after,
            "consoleErrors": console_errors.strip(),
            "artifacts": {
                "pre": str(pre_snapshot),
                "focused": str(focused_snapshot),
                "after2s": str(after_2s_snapshot),
                "after6s": str(after_6s_snapshot),
            },
        }
    finally:
        if fixture_payload and fixture_payload.get("fixtureId"):
            restore_review_fixture(args.url, str(fixture_payload.get("fixtureId")))
        if opened_session and not args.keep_session_open:
            pw.close_session_quietly(args.session)

    if result is None:
        raise RuntimeError("review smoke 没有生成结果。")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
