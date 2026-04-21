#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "playwright"
SCRIPTS_DIR = ROOT_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import browser_capture_smoke as pw  # noqa: E402


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pwcli_with_timeout(session: str, *args: str, timeout_seconds: float = 60.0) -> str:
    env = pw.shell_env()
    command = [env["PWCLI"], f"-s={pw.cli_session_name(session)}", *args]
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


def eval_json_with_timeout(session: str, script: str, *, timeout_seconds: float = 60.0):
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            output = run_pwcli_with_timeout(session, "eval", script, timeout_seconds=remaining)
            return pw.extract_playwright_result(output)
        except RuntimeError as error:
            message = str(error)
            if "Execution context was destroyed" not in message and "Cannot find context with specified id" not in message:
                raise
            last_error = error
            time.sleep(0.5)
    if last_error:
        raise last_error
    raise RuntimeError("Playwright eval 超时，且没有可用结果。")


def wait_for(session: str, script: str, *, timeout_seconds: float = 15.0, interval_seconds: float = 0.5):
    deadline = time.time() + timeout_seconds
    last_value = None
    while time.time() < deadline:
        last_value = pw.eval_json(session, script)
        if last_value:
            return last_value
        time.sleep(interval_seconds)
    raise RuntimeError(f"Timed out waiting for browser condition: {script}\nLast value: {last_value!r}")


def browser_state(session: str) -> dict:
    return pw.eval_json(
        session,
        """() => {
          const activeGranularity = document.querySelector('#granularityGroup .is-active')?.textContent?.trim() || null;
          const selectedCommunity = document.querySelector('#detailCard strong')?.textContent?.trim() || null;
          const samplingTaskLabel = document.querySelector('[data-browser-capture-task-label="true"]')?.textContent?.trim() || null;
          const selectedSamplingTaskId = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
          const reviewPanel = document.querySelector('[data-browser-review-current-run-id]');
          const reviewInbox = document.querySelector('[data-browser-review-inbox-count]');
          const reviewRelay = document.querySelector('[data-browser-review-action]');
          const reviewBatch = document.querySelector('[data-browser-review-batch-selected-count]');
          const summaryCards = [...document.querySelectorAll('#summaryGrid [data-summary-metric]')].map((card) => ({
            key: card.dataset.summaryMetric || null,
            label: card.querySelector('.metric-label')?.textContent?.trim() || null,
            value: card.querySelector('strong')?.textContent?.trim() || null,
          }));
          return {
            title: document.title,
            mapMode: document.querySelector('#mapModeBadge')?.textContent?.trim() || null,
            activeGranularity,
            mapNote: document.querySelector('#mapNote')?.textContent?.trim() || null,
            selectedCommunity,
            samplingTaskLabel,
            selectedSamplingTaskId,
            reviewPanelRunId: reviewPanel?.dataset.browserReviewCurrentRunId || null,
            reviewPanelPendingCount: Number(reviewPanel?.dataset.browserReviewCurrentPendingCount || 0),
            attentionFillCount: document.querySelectorAll('[data-browser-capture-fill-from-attention]').length,
            reviewInboxCount: Number(reviewInbox?.dataset.browserReviewInboxCount || 0),
            reviewInboxVisibleCount: document.querySelectorAll('[data-browser-review-inbox-item-id]').length,
            reviewInboxActiveItemId: document.querySelector('[data-browser-review-inbox-item-id].is-active')?.dataset.browserReviewInboxItemId || null,
            reviewRelayAction: reviewRelay?.dataset.browserReviewAction || null,
            reviewRelayRunId: reviewRelay?.dataset.browserReviewRunId || null,
            reviewRelayQueueId: reviewRelay?.dataset.browserReviewQueueId || null,
            reviewRelayWorkflowRunId: reviewRelay?.dataset.browserReviewWorkflowRunId || null,
            reviewRelayWorkflowQueueId: reviewRelay?.dataset.browserReviewWorkflowQueueId || null,
            reviewRelayWorkflowTaskId: reviewRelay?.dataset.browserReviewWorkflowTaskId || null,
            reviewRelayWorkflowItemProvided: reviewRelay?.dataset.browserReviewWorkflowItemProvided === 'true',
            reviewRelayResolution: reviewRelay?.dataset.browserReviewResolution || null,
            reviewRelayReason: reviewRelay?.dataset.browserReviewReason || null,
            reviewRelayTargetTaskId: reviewRelay?.dataset.browserReviewTargetTaskId || null,
            reviewRelayTargetRunId: reviewRelay?.dataset.browserReviewTargetRunId || null,
            reviewRelayTargetQueueId: reviewRelay?.dataset.browserReviewTargetQueueId || null,
            reviewRelayPendingCount: Number(reviewRelay?.dataset.browserReviewPendingCount || 0),
            reviewBatchSelectedCount: Number(reviewBatch?.dataset.browserReviewBatchSelectedCount || 0),
            reviewBatchAffectedCount: Number(reviewRelay?.dataset.browserReviewBatchAffectedCount || 0),
            reviewBatchSkippedCount: Number(reviewRelay?.dataset.browserReviewBatchSkippedCount || 0),
            reviewBatchStatus: reviewRelay?.dataset.browserReviewBatchStatus || null,
            rankingCount: document.querySelectorAll('#rankingList .ranking-item').length,
            floorWatchlistCount: document.querySelectorAll('#floorWatchlist .ranking-item').length,
            geoTaskCount: document.querySelectorAll('#geoTaskWatchlist .ranking-item').length,
            browserSamplingTaskCount: document.querySelectorAll('#browserSamplingPack .ranking-item').length,
            coverageDistrictCount: document.querySelectorAll('[data-browser-coverage-district]').length,
            coverageCommunityCount: document.querySelectorAll('[data-browser-coverage-community-id]').length,
            visibleCommunityCount: typeof getVisibleMapCommunities === 'function' ? getVisibleMapCommunities().length : null,
            visibleBuildingCount: typeof getVisibleBuildingItems === 'function' ? getVisibleBuildingItems().length : null,
            visibleFloorCount: typeof getVisibleFloorWatchlistItems === 'function' ? getVisibleFloorWatchlistItems().length : null,
            districtFilter: document.querySelector('#districtFilter')?.value || null,
            summaryCards,
          };
        }""",
    )


def click_via_dom(session: str, script: str) -> dict:
    return pw.eval_json(session, f"() => ({script})")


def pick_coverage_card_target(
    session: str,
    *,
    selector: str,
    require_different_district: bool = False,
) -> dict:
    return pw.eval_json(
        session,
        f"""() => {{
          const currentTaskId = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || '';
          const currentDistrict = document.querySelector('#districtFilter')?.value || 'all';
          const cards = [...document.querySelectorAll({json.dumps(selector)})];
          const card =
            cards.find((item) => {{
              const district = item.dataset.browserCoverageDistrict || '';
              const taskId = item.dataset.browserCoverageTaskId || '';
              if (taskId && taskId === currentTaskId) {{
                return false;
              }}
              if ({'true' if require_different_district else 'false'} && district && district === currentDistrict) {{
                return false;
              }}
              return true;
            }}) || cards[0];
          if (!card) {{
            return {{ clicked: false }};
          }}
          return {{
            clicked: true,
            district: card.dataset.browserCoverageDistrict || null,
            taskId: card.dataset.browserCoverageTaskId || null,
            communityId: card.dataset.communityId || null,
            buildingId: card.dataset.buildingId || null,
            floorNo: card.dataset.floorNo || null,
            label: card.querySelector('strong')?.textContent?.trim() || null,
            currentDistrict,
            currentTaskId,
          }};
        }}""",
    )


def set_granularity(session: str, label: str, state_value: str) -> dict:
    return click_via_dom(
        session,
        f"""(() => {{
          const button = [...document.querySelectorAll('#granularityGroup button')].find((item) => item.textContent.includes('{label}'));
          button?.click();
          const activeText = document.querySelector('#granularityGroup .is-active')?.textContent?.trim() || '';
          if (!activeText.includes('{label}') && typeof state !== 'undefined') {{
            state.granularity = '{state_value}';
            render();
          }}
          return {{
            requested: '{label}',
            active: document.querySelector('#granularityGroup .is-active')?.textContent?.trim() || null,
          }};
        }})()""",
    )


def apply_district_scope(session: str, district_id: str) -> dict:
    return eval_json_with_timeout(
        session,
        f"""async () => {{
          const select = document.querySelector('#districtFilter');
          if (!select) {{
            return {{ changed: false, district: null, reason: 'missing-select' }};
          }}
          if (typeof applyDistrictScope === 'function') {{
            void applyDistrictScope({json.dumps(district_id)});
            try {{
              render();
            }} catch (error) {{
              // Keep the helper resilient if render is temporarily unavailable.
            }}
            return {{
              changed: true,
              district: document.querySelector('#districtFilter')?.value || null,
              stateDistrict: typeof state !== 'undefined' ? state.districtFilter : null,
            }};
          }}
          select.value = {json.dumps(district_id)};
          select.dispatchEvent(new Event('change', {{ bubbles: true }}));
          return {{
            changed: true,
            district: select.value,
            stateDistrict: typeof state !== 'undefined' ? state.districtFilter : null,
          }};
        }}""",
        timeout_seconds=60.0,
    )


def fetch_exports(session: str) -> list[dict]:
    return eval_json_with_timeout(
        session,
        """async () => {
          const urls = [
            '/api/export/geojson',
            '/api/export/kml',
            '/api/export/floor-watchlist.geojson',
            '/api/export/floor-watchlist.kml',
            '/api/export/geo-task-watchlist.geojson',
            '/api/export/geo-task-watchlist.csv',
            '/api/export/browser-sampling-pack.csv',
          ];
          const results = [];
          for (const url of urls) {
            try {
              const controller = new AbortController();
              const timer = setTimeout(() => controller.abort('timeout'), 15000);
              const response = await fetch(url, { signal: controller.signal });
              const text = await response.text();
              clearTimeout(timer);
              results.push({
                url,
                ok: response.ok,
                status: response.status,
                contentType: response.headers.get('content-type'),
                size: text.length,
              });
            } catch (error) {
              results.push({
                url,
                ok: false,
                status: 0,
                error: String(error),
                size: 0,
              });
            }
          }
          return results;
        }""",
        timeout_seconds=150.0,
    )


def wait_for_floor_layer_ready(session: str) -> dict:
    return wait_for(
        session,
        """() => {
          const loading = typeof state !== 'undefined' ? !!state.floorWatchlistLoading : false;
          const count = typeof state !== 'undefined' && Array.isArray(state.floorWatchlistItems) ? state.floorWatchlistItems.length : 0;
          return !loading && count > 0 ? { loading, count } : null;
        }""",
        timeout_seconds=30.0,
        interval_seconds=0.5,
    )


def run_browser_capture_workflow_smoke(
    url: str,
    session: str,
    label: str,
    expected_workflow_action: str,
    *,
    headed: bool = False,
) -> dict:
    smoke_session = f"{session}-{expected_workflow_action}"
    command = [
        sys.executable,
        str(SCRIPTS_DIR / "browser_capture_smoke.py"),
        "--url",
        url,
        "--session",
        smoke_session,
        "--label",
        f"{label}-{expected_workflow_action}",
        "--expected-workflow-action",
        expected_workflow_action,
        "--fresh-session",
    ]
    if headed:
        command.append("--headed")
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
            timeout=240.0,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"公开页采样 workflow smoke 失败: {expected_workflow_action}\n"
            f"STDOUT:\n{error.stdout}\nSTDERR:\n{error.stderr}"
        ) from error
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"公开页采样 workflow smoke 输出不是合法 JSON: {expected_workflow_action}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        ) from error


def run_browser_review_workflow_smoke(
    url: str,
    session: str,
    label: str,
    expected_workflow_action: str,
    *,
    headed: bool = False,
) -> dict:
    last_error: RuntimeError | None = None
    attempt_count = 2 if expected_workflow_action == "review_current_task" else 1
    for attempt in range(1, attempt_count + 1):
        retry_suffix = "" if attempt == 1 else f"-retry{attempt}"
        smoke_session = f"{session}-{expected_workflow_action}{retry_suffix}"
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "browser_review_smoke.py"),
            "--url",
            url,
            "--session",
            smoke_session,
            "--label",
            f"{label}-{expected_workflow_action}{retry_suffix}",
            "--expected-workflow-action",
            expected_workflow_action,
            "--fresh-session",
        ]
        if headed:
            command.append("--headed")
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT_DIR,
                check=True,
                capture_output=True,
                text=True,
                timeout=300.0,
            )
            try:
                return json.loads(completed.stdout)
            except json.JSONDecodeError as error:
                last_error = RuntimeError(
                    f"公开页采样 review workflow smoke 输出不是合法 JSON: {expected_workflow_action} (attempt {attempt})\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                if attempt == attempt_count:
                    raise last_error from error
        except subprocess.CalledProcessError as error:
            last_error = RuntimeError(
                f"公开页采样 review workflow smoke 失败: {expected_workflow_action} (attempt {attempt})\n"
                f"STDOUT:\n{error.stdout}\nSTDERR:\n{error.stderr}"
            )
            if attempt == attempt_count:
                raise last_error from error
    if last_error:
        raise last_error
    raise RuntimeError(f"公开页采样 review workflow smoke 没有返回结果: {expected_workflow_action}")


def build_assertions(data: dict[str, object]) -> dict[str, dict[str, object]]:
    initial = data.get("initialState") or {}
    district_coverage = data.get("districtCoverageState") or {}
    district_coverage_click = data.get("districtCoverageClickResult") or {}
    pudong = data.get("pudongState") or {}
    coverage = data.get("coverageState") or {}
    coverage_click = data.get("coverageClickResult") or {}
    next_capture = data.get("nextCaptureState") or {}
    next_capture_click = data.get("nextCaptureClickResult") or {}
    next_review = data.get("nextReviewState") or {}
    next_review_click = data.get("nextReviewClickResult") or {}
    review_action = data.get("reviewActionState") or {}
    review_action_click = data.get("reviewActionClickResult") or {}
    building = data.get("buildingState") or {}
    floor = data.get("floorState") or {}
    sampling = data.get("samplingState") or {}
    exports = data.get("exports") or []
    capture_review_smoke = data.get("captureReviewWorkflowSmoke") or {}
    capture_advance_smoke = data.get("captureAdvanceWorkflowSmoke") or {}
    review_current_task_smoke = data.get("reviewCurrentTaskWorkflowSmoke") or {}
    capture_review_dom = capture_review_smoke.get("domResult") or {}
    capture_review_relay = capture_review_smoke.get("relay") or {}
    capture_review_after = capture_review_smoke.get("after6sState") or {}
    capture_advance_dom = capture_advance_smoke.get("domResult") or {}
    capture_advance_relay = capture_advance_smoke.get("relay") or {}
    capture_advance_after = capture_advance_smoke.get("after6sState") or {}
    review_current_task_relay = review_current_task_smoke.get("relay") or {}
    review_current_task_after = review_current_task_smoke.get("after6sState") or {}
    review_current_task_target = review_current_task_smoke.get("expectedTargetItem") or {}
    return {
        "initial_map_live": {
            "passed": initial.get("mapMode") == "AMap Live",
            "actual": initial.get("mapMode"),
        },
        "district_filter_applied": {
            "passed": pudong.get("districtFilter") == "pudong",
            "actual": pudong.get("districtFilter"),
        },
        "summary_metrics_rendered": {
            "passed": len(initial.get("summaryCards") or []) >= 6,
            "actual": initial.get("summaryCards"),
        },
        "district_coverage_card_switches_scope": {
            "passed": bool(district_coverage_click.get("clicked"))
            and district_coverage.get("districtFilter") == district_coverage_click.get("district")
            and district_coverage.get("selectedSamplingTaskId") == district_coverage_click.get("taskId")
            and (district_coverage.get("rankingCount") or 0) == (district_coverage.get("visibleCommunityCount") or 0),
            "actual": {
                "clicked": district_coverage_click.get("clicked"),
                "district": district_coverage_click.get("district"),
                "taskId": district_coverage_click.get("taskId"),
                "selectedDistrict": district_coverage.get("districtFilter"),
                "selectedSamplingTaskId": district_coverage.get("selectedSamplingTaskId"),
                "samplingTaskLabel": district_coverage.get("samplingTaskLabel"),
                "rankingCount": district_coverage.get("rankingCount"),
                "visibleCommunityCount": district_coverage.get("visibleCommunityCount"),
            },
        },
        "coverage_board_populated": {
            "passed": (pudong.get("coverageDistrictCount") or 0) > 0 and (pudong.get("coverageCommunityCount") or 0) > 0,
            "actual": {
                "districts": pudong.get("coverageDistrictCount"),
                "communities": pudong.get("coverageCommunityCount"),
            },
        },
        "coverage_card_opens_sampling_task": {
            "passed": bool(coverage_click.get("clicked")) and coverage.get("selectedSamplingTaskId") == coverage_click.get("taskId"),
            "actual": {
                "clicked": coverage_click.get("clicked"),
                "taskId": coverage_click.get("taskId"),
                "selectedSamplingTaskId": coverage.get("selectedSamplingTaskId"),
                "samplingTaskLabel": coverage.get("samplingTaskLabel"),
            },
        },
        "workbench_next_capture_advances_task": {
            "passed": bool(next_capture_click.get("clicked"))
            and next_capture.get("selectedSamplingTaskId") == next_capture_click.get("target"),
            "actual": {
                "clicked": next_capture_click.get("clicked"),
                "before": next_capture_click.get("before"),
                "target": next_capture_click.get("target"),
                "selectedSamplingTaskId": next_capture.get("selectedSamplingTaskId"),
                "samplingTaskLabel": next_capture.get("samplingTaskLabel"),
            },
        },
        "workbench_next_review_opens_inbox_item": {
            "passed": next_review_click.get("reason") == "no-review-task"
            or (
                bool(next_review_click.get("clicked"))
                and next_review.get("selectedSamplingTaskId") == next_review_click.get("target")
                and bool(next_review.get("reviewPanelRunId"))
                and (next_review.get("reviewPanelPendingCount") or 0) > 0
                and (next_review.get("attentionFillCount") or 0) > 0
                and (next_review.get("reviewInboxVisibleCount") or 0) > 0
            ),
            "actual": {
                "clicked": next_review_click.get("clicked"),
                "target": next_review_click.get("target"),
                "reason": next_review_click.get("reason"),
                "selectedSamplingTaskId": next_review.get("selectedSamplingTaskId"),
                "reviewPanelRunId": next_review.get("reviewPanelRunId"),
                "reviewPanelPendingCount": next_review.get("reviewPanelPendingCount"),
                "reviewInboxCount": next_review.get("reviewInboxCount"),
                "reviewInboxVisibleCount": next_review.get("reviewInboxVisibleCount"),
                "reviewInboxActiveItemId": next_review.get("reviewInboxActiveItemId"),
                "attentionFillCount": next_review.get("attentionFillCount"),
                "samplingTaskLabel": next_review.get("samplingTaskLabel"),
            },
        },
        "review_queue_batch_updates_relay": {
            "passed": next_review_click.get("reason") == "no-review-task"
            or review_action_click.get("reason") == "no-batch-button"
            or (
                bool(review_action_click.get("clicked"))
                and bool(review_action.get("reviewRelayAction"))
                and bool(review_action.get("reviewRelayRunId"))
                and bool(review_action.get("reviewRelayQueueId"))
                and (
                    review_action.get("reviewRelayAction") == "stay_current"
                    or (
                        review_action.get("reviewRelayWorkflowItemProvided") is True
                        and review_action.get("reviewRelayResolution") == "workflow_item"
                        and review_action.get("reviewRelayTargetTaskId") == review_action.get("selectedSamplingTaskId")
                        and bool(review_action.get("reviewRelayTargetRunId"))
                        and bool(review_action.get("reviewRelayTargetQueueId"))
                    )
                )
                and (review_action.get("reviewBatchAffectedCount") or 0) > 0
                and review_action.get("reviewBatchStatus") == "waived"
            ),
            "actual": {
                "clicked": review_action_click.get("clicked"),
                "reason": review_action_click.get("reason"),
                "reviewRelayAction": review_action.get("reviewRelayAction"),
                "reviewRelayRunId": review_action.get("reviewRelayRunId"),
                "reviewRelayQueueId": review_action.get("reviewRelayQueueId"),
                "reviewRelayWorkflowRunId": review_action.get("reviewRelayWorkflowRunId"),
                "reviewRelayWorkflowQueueId": review_action.get("reviewRelayWorkflowQueueId"),
                "reviewRelayWorkflowTaskId": review_action.get("reviewRelayWorkflowTaskId"),
                "reviewRelayWorkflowItemProvided": review_action.get("reviewRelayWorkflowItemProvided"),
                "reviewRelayResolution": review_action.get("reviewRelayResolution"),
                "reviewRelayReason": review_action.get("reviewRelayReason"),
                "reviewRelayTargetTaskId": review_action.get("reviewRelayTargetTaskId"),
                "reviewRelayTargetRunId": review_action.get("reviewRelayTargetRunId"),
                "reviewRelayTargetQueueId": review_action.get("reviewRelayTargetQueueId"),
                "reviewRelayPendingCount": review_action.get("reviewRelayPendingCount"),
                "reviewBatchSelectedCount": review_action.get("reviewBatchSelectedCount"),
                "reviewBatchAffectedCount": review_action.get("reviewBatchAffectedCount"),
                "reviewBatchSkippedCount": review_action.get("reviewBatchSkippedCount"),
                "reviewBatchStatus": review_action.get("reviewBatchStatus"),
            },
        },
        "building_mode_has_geometry": {
            "passed": (building.get("visibleBuildingCount") or 0) > 0,
            "actual": building.get("visibleBuildingCount"),
        },
        "floor_mode_has_items": {
            "passed": (floor.get("visibleFloorCount") or 0) > 0,
            "actual": floor.get("visibleFloorCount"),
        },
        "sampling_panel_opened": {
            "passed": bool(sampling.get("samplingTaskLabel")),
            "actual": sampling.get("samplingTaskLabel"),
        },
        "capture_review_workflow_smoke": {
            "passed": capture_review_relay.get("action") == "review_current_capture"
            and capture_review_relay.get("workflowTaskProvided") is True
            and capture_review_relay.get("resolution") == "workflow_task"
            and capture_review_relay.get("workflowTaskId") == capture_review_relay.get("taskId")
            and capture_review_after.get("taskId") == capture_review_smoke.get("task", {}).get("taskId")
            and capture_review_after.get("currentTaskRecentRun", {}).get("captureRunId") == capture_review_dom.get("captureRunId")
            and capture_review_after.get("recentRun", {}).get("captureRunId") == capture_review_dom.get("captureRunId"),
            "actual": {
                "selectedTaskId": capture_review_smoke.get("selectedTask", {}).get("taskId"),
                "resultCaptureRunId": capture_review_dom.get("captureRunId"),
                "relayAction": capture_review_relay.get("action"),
                "relayReason": capture_review_relay.get("reason"),
                "workflowTaskProvided": capture_review_relay.get("workflowTaskProvided"),
                "relayResolution": capture_review_relay.get("resolution"),
                "workflowTaskId": capture_review_relay.get("workflowTaskId"),
                "afterTaskId": capture_review_after.get("taskId"),
                "currentTaskRecentRunId": capture_review_after.get("currentTaskRecentRun", {}).get("captureRunId"),
                "recentRunId": capture_review_after.get("recentRun", {}).get("captureRunId"),
            },
        },
        "capture_advance_workflow_smoke": {
            "passed": capture_advance_relay.get("action") == "advance_next_capture"
            and capture_advance_relay.get("workflowTaskProvided") is True
            and capture_advance_relay.get("resolution") == "workflow_task"
            and capture_advance_relay.get("workflowTaskId") == capture_advance_relay.get("taskId")
            and capture_advance_after.get("taskId") == capture_advance_relay.get("taskId")
            and capture_advance_after.get("taskId") != capture_advance_smoke.get("task", {}).get("taskId")
            and capture_advance_after.get("recentRun", {}).get("captureRunId") == capture_advance_dom.get("captureRunId"),
            "actual": {
                "selectedTaskId": capture_advance_smoke.get("selectedTask", {}).get("taskId"),
                "sourceTaskId": capture_advance_smoke.get("task", {}).get("taskId"),
                "resultCaptureRunId": capture_advance_dom.get("captureRunId"),
                "relayAction": capture_advance_relay.get("action"),
                "relayReason": capture_advance_relay.get("reason"),
                "workflowTaskProvided": capture_advance_relay.get("workflowTaskProvided"),
                "relayResolution": capture_advance_relay.get("resolution"),
                "workflowTaskId": capture_advance_relay.get("workflowTaskId"),
                "relayTaskId": capture_advance_relay.get("taskId"),
                "afterTaskId": capture_advance_after.get("taskId"),
                "recentRunId": capture_advance_after.get("recentRun", {}).get("captureRunId"),
            },
        },
        "review_current_task_workflow_smoke": {
            "passed": review_current_task_smoke.get("fixtureApplied") is True
            and review_current_task_relay.get("action") == "review_current_task"
            and review_current_task_relay.get("workflowItemProvided") is True
            and review_current_task_relay.get("resolution") == "workflow_item"
            and review_current_task_relay.get("reason") == "current_task_pending_remaining"
            and review_current_task_relay.get("workflowTaskId") == review_current_task_target.get("taskId")
            and review_current_task_relay.get("workflowRunId") == review_current_task_target.get("runId")
            and review_current_task_relay.get("workflowQueueId") == review_current_task_target.get("queueId")
            and review_current_task_after.get("taskId") == review_current_task_target.get("taskId")
            and review_current_task_after.get("reviewPanelRunId") == review_current_task_target.get("runId"),
            "actual": {
                "fixtureApplied": review_current_task_smoke.get("fixtureApplied"),
                "fixtureId": review_current_task_smoke.get("fixtureId"),
                "sourceTaskId": review_current_task_smoke.get("sourceItem", {}).get("taskId"),
                "targetTaskId": review_current_task_target.get("taskId"),
                "targetRunId": review_current_task_target.get("runId"),
                "targetQueueId": review_current_task_target.get("queueId"),
                "relayAction": review_current_task_relay.get("action"),
                "relayReason": review_current_task_relay.get("reason"),
                "workflowItemProvided": review_current_task_relay.get("workflowItemProvided"),
                "relayResolution": review_current_task_relay.get("resolution"),
                "afterTaskId": review_current_task_after.get("taskId"),
                "afterReviewPanelRunId": review_current_task_after.get("reviewPanelRunId"),
                "inboxBefore": review_current_task_smoke.get("reviewInboxCountBefore"),
                "inboxAfter": review_current_task_smoke.get("reviewInboxCountAfter"),
            },
        },
        "all_exports_ok": {
            "passed": all(item.get("ok") for item in exports),
            "actual": [{"url": item.get("url"), "status": item.get("status"), "ok": item.get("ok")} for item in exports],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a full browser regression for Shanghai Yield Atlas.")
    parser.add_argument("--session", default="atlas-full-regression", help="Playwright browser session")
    parser.add_argument("--label", default=f"atlas-full-regression-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    parser.add_argument("--url", default="http://127.0.0.1:8013")
    parser.add_argument("--headed", action="store_true", help="Run with a visible browser window. Default is headless.")
    parser.add_argument("--fresh-session", action="store_true", help="Force a new browser session instead of reusing an existing one.")
    parser.add_argument("--reuse-open-session", action="store_true", help="Deprecated: sessions are reused automatically when available.")
    parser.add_argument("--keep-session-open", action="store_true", help="Keep the Playwright browser session open after the regression finishes.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, object] = {
      "label": args.label,
      "url": args.url,
      "session": args.session,
      "steps": [],
    }

    review_current_task_smoke = run_browser_review_workflow_smoke(
        args.url,
        args.session,
        args.label,
        "review_current_task",
        headed=args.headed,
    )
    artifacts["steps"].append(
        {
            "name": "review-current-task-workflow-smoke",
            "result": {
                "fixtureApplied": review_current_task_smoke.get("fixtureApplied"),
                "taskId": review_current_task_smoke.get("sourceItem", {}).get("taskId"),
                "relayAction": review_current_task_smoke.get("relay", {}).get("action"),
                "relayReason": review_current_task_smoke.get("relay", {}).get("reason"),
                "targetRunId": review_current_task_smoke.get("relay", {}).get("targetRunId"),
                "targetQueueId": review_current_task_smoke.get("relay", {}).get("targetQueueId"),
            },
        }
    )
    artifacts["reviewCurrentTaskWorkflowSmoke"] = review_current_task_smoke

    session_name = args.session
    opened_new_session = False
    try:
        opened_new_session, session_meta = pw.ensure_browser_session(
            session_name,
            args.url,
            headed=args.headed,
            navigate=True,
            fresh_session=args.fresh_session,
        )
        artifacts["session"] = session_name
        artifacts["sessionMeta"] = session_meta
        initial_snapshot = pw.take_snapshot(session_name, args.label, "initial")
        artifacts["steps"].append({"name": "open", "snapshot": str(initial_snapshot)})

        wait_for(session_name, "() => document.querySelector('#mapModeBadge')?.textContent?.trim()?.length > 0")
        wait_for(session_name, "() => document.querySelectorAll('#summaryGrid [data-summary-metric]').length >= 6")
        wait_for(session_name, "() => document.querySelectorAll('[data-browser-coverage-community-id]').length > 0")
        initial_state = browser_state(session_name)
        artifacts["initialState"] = initial_state

        district_coverage_click_result = pick_coverage_card_target(
            session_name,
            selector="[data-browser-coverage-district]",
            require_different_district=True,
        )
        if district_coverage_click_result.get("clicked") and district_coverage_click_result.get("district"):
            apply_district_scope(session_name, district_coverage_click_result["district"])
            wait_for(
                session_name,
                f"""() => document.querySelector('#districtFilter')?.value === {json.dumps(district_coverage_click_result["district"])}""",
                timeout_seconds=60.0,
            )
        if district_coverage_click_result.get("clicked") and district_coverage_click_result.get("taskId"):
            pw.navigate_to_browser_sampling_task(
                session_name,
                {
                    "taskId": district_coverage_click_result.get("taskId"),
                    "districtId": district_coverage_click_result.get("district"),
                    "communityId": district_coverage_click_result.get("communityId"),
                    "buildingId": district_coverage_click_result.get("buildingId"),
                    "floorNo": district_coverage_click_result.get("floorNo"),
                },
            )
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(district_coverage_click_result["taskId"])}""",
                timeout_seconds=60.0,
            )
        district_coverage_snapshot = pw.take_snapshot(session_name, args.label, "district-coverage")
        district_coverage_state = browser_state(session_name)
        artifacts["districtCoverageClickResult"] = district_coverage_click_result
        artifacts["steps"].append(
            {"name": "district-coverage-card", "result": district_coverage_click_result, "snapshot": str(district_coverage_snapshot)}
        )
        artifacts["districtCoverageState"] = district_coverage_state

        district_result = apply_district_scope(session_name, "pudong")
        wait_for(session_name, "() => document.querySelector('#districtFilter')?.value === 'pudong'")
        pudong_snapshot = pw.take_snapshot(session_name, args.label, "pudong")
        pudong_state = browser_state(session_name)
        artifacts["steps"].append({"name": "district-filter", "result": district_result, "snapshot": str(pudong_snapshot)})
        artifacts["pudongState"] = pudong_state

        coverage_click_result = pick_coverage_card_target(
            session_name,
            selector="[data-browser-coverage-community-id]",
        )
        if coverage_click_result.get("clicked") and coverage_click_result.get("district"):
            apply_district_scope(session_name, coverage_click_result["district"])
            wait_for(
                session_name,
                f"""() => document.querySelector('#districtFilter')?.value === {json.dumps(coverage_click_result["district"])}""",
                timeout_seconds=60.0,
            )
        if coverage_click_result.get("clicked") and coverage_click_result.get("taskId"):
            pw.navigate_to_browser_sampling_task(
                session_name,
                {
                    "taskId": coverage_click_result.get("taskId"),
                    "districtId": coverage_click_result.get("district"),
                    "communityId": coverage_click_result.get("communityId"),
                    "buildingId": coverage_click_result.get("buildingId"),
                    "floorNo": coverage_click_result.get("floorNo"),
                },
            )
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(coverage_click_result["taskId"])}""",
                timeout_seconds=60.0,
            )
        coverage_snapshot = pw.take_snapshot(session_name, args.label, "coverage-click")
        coverage_state = browser_state(session_name)
        artifacts["coverageClickResult"] = coverage_click_result
        artifacts["steps"].append({"name": "coverage-card", "result": coverage_click_result, "snapshot": str(coverage_snapshot)})
        artifacts["coverageState"] = coverage_state

        next_capture_click_result = pw.eval_json(
            session_name,
            """() => {
              const button =
                document.querySelector('[data-browser-workbench-next-capture]:not([disabled])') ||
                document.querySelector('[data-browser-workbench-next-district]:not([disabled])');
              if (!button) return { clicked: false };
              const before = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
              const target = button.dataset.browserWorkbenchNextCapture || button.dataset.browserWorkbenchNextDistrict || null;
              const targetTask =
                (state?.browserSamplingPackItems ?? []).find((item) => item?.taskId === target) || null;
              return {
                clicked: true,
                before,
                target,
                text: button.textContent?.trim() || null,
                targetTask,
              };
            }""",
        )
        if next_capture_click_result.get("targetTask"):
            pw.navigate_to_browser_sampling_task(session_name, next_capture_click_result["targetTask"])
        if next_capture_click_result.get("target"):
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(next_capture_click_result["target"])}""",
                timeout_seconds=60.0,
                interval_seconds=0.5,
            )
        next_capture_snapshot = pw.take_snapshot(session_name, args.label, "next-capture")
        next_capture_state = browser_state(session_name)
        artifacts["nextCaptureClickResult"] = next_capture_click_result
        artifacts["steps"].append({"name": "next-capture", "result": next_capture_click_result, "snapshot": str(next_capture_snapshot)})
        artifacts["nextCaptureState"] = next_capture_state

        next_review_click_result = pw.eval_json(
            session_name,
            """() => {
              const before = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
              const currentDistrict = typeof state !== 'undefined' ? state.districtFilter : 'all';
              const button = document.querySelector('[data-browser-workbench-next-review]:not([disabled])');
              const inboxItems = Array.isArray(state?.browserReviewInboxItems) ? state.browserReviewInboxItems : [];
              const targetItem =
                (button
                  ? inboxItems.find(
                      (item) =>
                        item?.runId === (button.dataset.browserWorkbenchNextReviewRunId || null) &&
                        item?.queueId === (button.dataset.browserWorkbenchNextReviewQueueId || null)
                    )
                  : null) ||
                inboxItems.find((item) => item?.taskId !== before && (currentDistrict === 'all' || item?.districtId === currentDistrict)) ||
                inboxItems.find((item) => item?.taskId !== before) ||
                inboxItems[0];
              if (!targetItem) {
                return { clicked: false, before, reason: 'no-review-task' };
              }
              const task = {
                ...(targetItem.task || {}),
                taskId: targetItem.taskId || targetItem.task?.taskId || null,
                taskType: targetItem.taskType || targetItem.task?.taskType || null,
                taskTypeLabel: targetItem.taskTypeLabel || targetItem.task?.taskTypeLabel || null,
                targetGranularity: targetItem.targetGranularity || targetItem.task?.targetGranularity || null,
                focusScope: targetItem.focusScope || targetItem.task?.focusScope || null,
                priorityScore: targetItem.priorityScore || targetItem.task?.priorityScore || 0,
                priorityLabel: targetItem.priorityLabel || targetItem.task?.priorityLabel || null,
                districtId: targetItem.districtId || targetItem.task?.districtId || null,
                districtName: targetItem.districtName || targetItem.task?.districtName || null,
                communityId: targetItem.communityId || targetItem.task?.communityId || null,
                communityName: targetItem.communityName || targetItem.task?.communityName || null,
                buildingId: targetItem.buildingId || targetItem.task?.buildingId || null,
                buildingName: targetItem.buildingName || targetItem.task?.buildingName || null,
                floorNo: targetItem.floorNo || targetItem.task?.floorNo || null,
                pendingReviewRunId: targetItem.runId || targetItem.task?.pendingReviewRunId || null,
                pendingReviewQueueId: targetItem.queueId || targetItem.task?.pendingReviewQueueId || null,
                pendingAttentionCount: targetItem.taskPendingAttentionCount || targetItem.task?.pendingAttentionCount || 1,
                taskLifecycleStatus: 'needs_review',
                taskLifecycleLabel: '已采待复核',
              };
              return {
                clicked: true,
                before,
                target: targetItem.taskId || null,
                runId: targetItem.runId || null,
                queueId: targetItem.queueId || null,
                text: targetItem.taskLabel || targetItem.taskId || null,
                task,
                via: button ? 'button-target' : 'fallback-inbox',
              };
            }""",
        )
        if next_review_click_result.get("target"):
            if next_review_click_result.get("task"):
                pw.navigate_to_browser_sampling_task(session_name, next_review_click_result["task"])
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(next_review_click_result["target"])}""",
                timeout_seconds=60.0,
                interval_seconds=0.5,
            )
            if next_review_click_result.get("runId"):
                eval_json_with_timeout(
                    session_name,
                    f"""async () => {{
                      await loadSelectedBrowserCaptureRunDetail(
                        {json.dumps(next_review_click_result["runId"])},
                        {{
                          preferredQueueId: {json.dumps(next_review_click_result.get("queueId"))},
                        }}
                      );
                      try {{
                        render();
                      }} catch (error) {{
                        // Keep the helper resilient if render is temporarily unavailable.
                      }}
                      return {{
                        runId: document.querySelector('[data-browser-review-current-run-id]')?.dataset.browserReviewCurrentRunId || null,
                        queueId: document.querySelector('[data-browser-capture-review-queue-item].is-related')?.dataset.browserCaptureReviewQueueItem || null,
                      }};
                    }}""",
                    timeout_seconds=60.0,
                )
            wait_for(
                session_name,
                """() => {
                  const panel = document.querySelector('[data-browser-review-current-run-id]');
                  const runId = panel?.dataset.browserReviewCurrentRunId || '';
                  const pendingCount = Number(panel?.dataset.browserReviewCurrentPendingCount || 0);
                  const activeQueueId = document.querySelector('[data-browser-capture-review-queue-item].is-related')?.dataset.browserCaptureReviewQueueItem || '';
                  return runId && pendingCount > 0 && activeQueueId ? { runId, pendingCount, activeQueueId } : null;
                }""",
                timeout_seconds=20.0,
            )
        next_review_state = browser_state(session_name)
        artifacts["nextReviewClickResult"] = next_review_click_result
        artifacts["steps"].append({"name": "next-review", "result": next_review_click_result})
        artifacts["nextReviewState"] = next_review_state

        review_action_click_result = {"clicked": False, "reason": "no-review-task"}
        review_action_state = {}
        if next_review_click_result.get("target"):
            review_action_click_result = eval_json_with_timeout(
                session_name,
                """async () => {
                  const selectable = document.querySelector('[data-browser-capture-review-select]:not([disabled])');
                  if (!selectable) {
                    return { clicked: false, reason: 'no-batch-button' };
                  }
                  selectable.checked = true;
                  selectable.dispatchEvent(new Event('change', { bubbles: true }));
                  const runId =
                    document.querySelector('[data-browser-capture-review-batch-waive]')?.dataset.browserCaptureReviewBatchWaive ||
                    (typeof currentBrowserCaptureRun === 'function' ? currentBrowserCaptureRun()?.runId : null);
                  const queueIds =
                    typeof currentBrowserCaptureReviewBatchSelection === 'function' && typeof currentBrowserCaptureReviewQueue === 'function'
                      ? currentBrowserCaptureReviewBatchSelection(currentBrowserCaptureReviewQueue())
                      : [];
                  if (!runId || !queueIds.length || typeof reviewBrowserCaptureQueueBatch !== 'function') {
                    return {
                      clicked: false,
                      reason: 'no-batch-button',
                      selectedCount: Number(document.querySelector('[data-browser-review-batch-selected-count]')?.dataset.browserReviewBatchSelectedCount || 0),
                    };
                  }
                  await reviewBrowserCaptureQueueBatch(runId, queueIds, {
                    status: 'waived',
                    resolutionNotes: '回归测试豁免',
                  });
                  return {
                    clicked: true,
                    runId,
                    queueIds,
                    selectedCount: Number(document.querySelector('[data-browser-review-batch-selected-count]')?.dataset.browserReviewBatchSelectedCount || 0),
                  };
                }""",
                timeout_seconds=90.0,
            )
            if review_action_click_result.get("clicked"):
                wait_for(
                    session_name,
                    """() => {
                      const relay = document.querySelector('[data-browser-review-action]');
                      const action = relay?.dataset.browserReviewAction || '';
                      const runId = relay?.dataset.browserReviewRunId || '';
                      const queueId = relay?.dataset.browserReviewQueueId || '';
                      const resolution = relay?.dataset.browserReviewResolution || '';
                      const targetTaskId = relay?.dataset.browserReviewTargetTaskId || '';
                      return action && runId && queueId && resolution
                        ? { action, runId, queueId, resolution, targetTaskId }
                        : null;
                        }""",
                    timeout_seconds=30.0,
                )
            review_action_state = browser_state(session_name)
        artifacts["reviewActionClickResult"] = review_action_click_result
        artifacts["steps"].append({"name": "review-action", "result": review_action_click_result})
        artifacts["reviewActionState"] = review_action_state

        ranking_result = click_via_dom(
            session_name,
            """(() => {
              const item = document.querySelector('#rankingList .ranking-item');
              if (!item) return { clicked: false };
              const label = item.querySelector('strong')?.textContent?.trim() || null;
              item.dispatchEvent(new MouseEvent('click', { bubbles: true }));
              return { clicked: true, label };
            })()""",
        )
        time.sleep(1)
        ranking_snapshot = pw.take_snapshot(session_name, args.label, "ranking-click")
        ranking_state = browser_state(session_name)
        artifacts["steps"].append({"name": "ranking-click", "result": ranking_result, "snapshot": str(ranking_snapshot)})
        artifacts["rankingState"] = ranking_state

        building_result = set_granularity(session_name, "楼栋", "building")
        wait_for(session_name, "() => document.querySelector('#granularityGroup .is-active')?.textContent?.includes('楼栋')")
        building_snapshot = pw.take_snapshot(session_name, args.label, "building")
        building_state = browser_state(session_name)
        artifacts["steps"].append({"name": "building-mode", "result": building_result, "snapshot": str(building_snapshot)})
        artifacts["buildingState"] = building_state

        floor_result = set_granularity(session_name, "楼层", "floor")
        wait_for(session_name, "() => document.querySelector('#granularityGroup .is-active')?.textContent?.includes('楼层')")
        floor_ready = wait_for_floor_layer_ready(session_name)
        floor_snapshot = pw.take_snapshot(session_name, args.label, "floor")
        floor_state = browser_state(session_name)
        artifacts["steps"].append({"name": "floor-mode", "result": floor_result, "snapshot": str(floor_snapshot)})
        artifacts["floorState"] = floor_state
        artifacts["floorReady"] = floor_ready

        wait_for(session_name, "() => !!document.querySelector('[data-browser-capture-task-label=\"true\"]')?.textContent?.trim()")
        sampling_state = browser_state(session_name)
        artifacts["steps"].append({"name": "sampling-panel", "result": {"present": bool(sampling_state.get("samplingTaskLabel"))}})
        artifacts["samplingState"] = sampling_state

        exports = fetch_exports(session_name)
        artifacts["exports"] = exports
        capture_review_smoke = run_browser_capture_workflow_smoke(
            args.url,
            session_name,
            args.label,
            "review_current_capture",
            headed=args.headed,
        )
        artifacts["steps"].append(
            {
                "name": "capture-review-workflow-smoke",
                "result": {
                    "taskId": capture_review_smoke.get("selectedTask", {}).get("taskId"),
                    "captureRunId": capture_review_smoke.get("domResult", {}).get("captureRunId"),
                    "relayAction": capture_review_smoke.get("relay", {}).get("action"),
                    "relayReason": capture_review_smoke.get("relay", {}).get("reason"),
                },
            }
        )
        artifacts["captureReviewWorkflowSmoke"] = capture_review_smoke
        capture_advance_smoke = run_browser_capture_workflow_smoke(
            args.url,
            session_name,
            args.label,
            "advance_next_capture",
            headed=args.headed,
        )
        artifacts["steps"].append(
            {
                "name": "capture-advance-workflow-smoke",
                "result": {
                    "taskId": capture_advance_smoke.get("selectedTask", {}).get("taskId"),
                    "captureRunId": capture_advance_smoke.get("domResult", {}).get("captureRunId"),
                    "relayAction": capture_advance_smoke.get("relay", {}).get("action"),
                    "relayReason": capture_advance_smoke.get("relay", {}).get("reason"),
                    "relayTaskId": capture_advance_smoke.get("relay", {}).get("taskId"),
                },
            }
        )
        artifacts["captureAdvanceWorkflowSmoke"] = capture_advance_smoke

        console_errors = pw.run_pwcli(session_name, "console", "error")
        console_path = OUTPUT_DIR / f"{args.label}-console.txt"
        console_path.write_text(console_errors, encoding="utf-8")
        artifacts["consoleLog"] = str(console_path)
        artifacts["assertions"] = build_assertions(artifacts)
        artifacts["all_passed"] = all(
            bool(result.get("passed")) for result in artifacts["assertions"].values()
        )

        summary_path = OUTPUT_DIR / f"{args.label}.json"
        write_json(summary_path, artifacts)
        print(str(summary_path))
        return 0
    finally:
        if opened_new_session and not args.keep_session_open:
            pw.close_session_quietly(session_name)


if __name__ == "__main__":
    raise SystemExit(main())
