#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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


def eval_json_with_timeout(session: str, script: str, *, timeout_seconds: float = 60.0):
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            output = run_pwcli_with_timeout(session, "eval", script, timeout_seconds=remaining)
            return pw.extract_playwright_result(output)
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


def wait_for(session: str, script: str, *, timeout_seconds: float = 15.0, interval_seconds: float = 0.5):
    deadline = time.time() + timeout_seconds
    last_value = None
    last_error: Exception | None = None
    while time.time() < deadline:
        remaining = max(1.0, deadline - time.time())
        try:
            last_value = eval_json_with_timeout(
                session,
                script,
                timeout_seconds=min(remaining, max(pw.PWCLI_EVAL_TIMEOUT_SECONDS, interval_seconds * 8)),
            )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, RuntimeError) as error:
            last_error = error
            time.sleep(interval_seconds)
            continue
        if last_value:
            return last_value
        time.sleep(interval_seconds)
    if last_error:
        raise RuntimeError(
            f"Timed out waiting for browser condition: {script}\nLast value: {last_value!r}\nLast error: {last_error}"
        ) from last_error
    raise RuntimeError(f"Timed out waiting for browser condition: {script}\nLast value: {last_value!r}")


def browser_state(session: str) -> dict:
    return eval_json_with_timeout(
        session,
        """() => {
          const locationUrl = new URL(window.location.href);
          const isVisible = (element) => Boolean(element) && !element.hidden && !element.closest('[hidden]');
          const activeGranularity = document.querySelector('#granularityGroup .is-active')?.textContent?.trim() || null;
          const activeFilterTab = document.querySelector('[data-filter-tab].is-active')?.dataset.filterTab || null;
          const activeBackstageTab =
            document.querySelector('[data-research-backstage-tab].is-active')?.dataset.researchBackstageTab || null;
          const activeOperationsHistoryTab =
            document.querySelector('[data-ops-history-tab].is-active')?.dataset.opsHistoryTab || null;
          const activeOperationsDetailTab =
            document.querySelector('[data-ops-detail-tab].is-active')?.dataset.opsDetailTab || null;
          const activeOperationsQualityTab =
            document.querySelector('[data-ops-quality-tab].is-active')?.dataset.opsQualityTab || null;
          const selectedCommunity = document.querySelector('#detailCard strong')?.textContent?.trim() || null;
          const samplingTaskLabel = document.querySelector('[data-browser-capture-task-label="true"]')?.textContent?.trim() || null;
          const selectedSamplingTaskId = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
          const reviewPanel = document.querySelector('[data-browser-review-current-run-id]');
          const reviewInbox = document.querySelector('[data-browser-review-inbox-count]');
          const reviewRelay = document.querySelector('[data-browser-review-action]');
          const reviewBatch = document.querySelector('[data-browser-review-batch-selected-count]');
          const visibleFilterPanels = [...document.querySelectorAll('[data-filter-panel]')]
            .filter((panel) => isVisible(panel))
            .map((panel) => panel.dataset.filterPanel || null)
            .filter(Boolean);
          const visibleBackstagePanels = [...document.querySelectorAll('[data-research-panel]')]
            .filter((panel) => isVisible(panel))
            .map((panel) => panel.dataset.researchPanel || null)
            .filter(Boolean);
          const visibleOperationsHistoryPanels = [...document.querySelectorAll('[data-ops-history-panel]')]
            .filter((panel) => isVisible(panel))
            .map((panel) => panel.dataset.opsHistoryPanel || null)
            .filter(Boolean);
          const visibleOperationsDetailPanels = [...document.querySelectorAll('[data-ops-detail-panel]')]
            .filter((panel) => isVisible(panel))
            .map((panel) => panel.dataset.opsDetailPanel || null)
            .filter(Boolean);
          const visibleOperationsQualityPanels = [...document.querySelectorAll('[data-ops-quality-panel]')]
            .filter((panel) => isVisible(panel))
            .map((panel) => panel.dataset.opsQualityPanel || null)
            .filter(Boolean);
          const summaryCards = [...document.querySelectorAll('#summaryGrid [data-summary-metric]')].map((card) => ({
            key: card.dataset.summaryMetric || null,
            label: card.querySelector('.metric-label')?.textContent?.trim() || null,
            value: card.querySelector('strong')?.textContent?.trim() || null,
          }));
          return {
            title: document.title,
            mapMode: document.querySelector('#mapModeBadge')?.textContent?.trim() || null,
            workspaceView: document.querySelector('#appShell')?.dataset.workspaceView || null,
            locationView: locationUrl.searchParams.get('view'),
            locationBackstage: locationUrl.searchParams.get('backstage'),
            locationOpsHistory: locationUrl.searchParams.get('opsHistory'),
            locationOpsDetail: locationUrl.searchParams.get('opsDetail'),
            locationOpsQuality: locationUrl.searchParams.get('opsQuality'),
            locationOpsImportRun: locationUrl.searchParams.get('opsImportRun'),
            locationOpsImportBaseline: locationUrl.searchParams.get('opsImportBaseline'),
            locationOpsGeoRun: locationUrl.searchParams.get('opsGeoRun'),
            locationOpsGeoBaseline: locationUrl.searchParams.get('opsGeoBaseline'),
            overviewBandVisible: !document.querySelector('#overviewBand')?.hidden,
            frontstageVisible: !document.querySelector('#frontstageWorkspace')?.hidden,
            backstageVisible: !document.querySelector('#backstageWorkspace')?.hidden,
            activeGranularity,
            activeFilterTab,
            visibleFilterPanels,
            activeBackstageTab,
            visibleBackstagePanels,
            activeOperationsHistoryTab,
            visibleOperationsHistoryPanels,
            activeOperationsDetailTab,
            visibleOperationsDetailPanels,
            activeOperationsQualityTab,
            visibleOperationsQualityPanels,
            selectedImportRunId: typeof state !== 'undefined' ? state.selectedImportRunId || null : null,
            selectedBaselineRunId: typeof state !== 'undefined' ? state.selectedBaselineRunId || null : null,
            selectedGeoAssetRunId: typeof state !== 'undefined' ? state.selectedGeoAssetRunId || null : null,
            selectedGeoBaselineRunId: typeof state !== 'undefined' ? state.selectedGeoBaselineRunId || null : null,
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
    return eval_json_with_timeout(session, f"() => ({script})")


def pick_coverage_card_target(
    session: str,
    *,
    selector: str,
    require_different_district: bool = False,
) -> dict:
    return eval_json_with_timeout(
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


def set_filter_panel_tab(session: str, tab: str) -> dict:
    return eval_json_with_timeout(
        session,
        f"""async () => {{
          const targetTab = {json.dumps(tab)};
          const button = document.querySelector(`[data-filter-tab="${{targetTab}}"]`);
          button?.click();
          if (typeof state !== 'undefined') {{
            state.filterPanelTab = targetTab;
          }}
          if (typeof renderFilterPanel === 'function') {{
            renderFilterPanel();
          }}
          return {{
            requested: targetTab,
            active: document.querySelector('[data-filter-tab].is-active')?.dataset.filterTab || null,
            visiblePanels: [...document.querySelectorAll('[data-filter-panel]')]
              .filter((panel) => !panel.hidden)
              .map((panel) => panel.dataset.filterPanel || null)
              .filter(Boolean),
          }};
        }}""",
        timeout_seconds=30.0,
    )


def set_workspace_view(
    session: str,
    view: str,
    *,
    backstage_tab: str | None = None,
    ops_history_tab: str | None = None,
    ops_detail_tab: str | None = None,
    ops_quality_tab: str | None = None,
) -> dict:
    return eval_json_with_timeout(
        session,
        f"""async () => {{
          const targetView = {json.dumps(view)};
          const targetBackstageTab = {json.dumps(backstage_tab)};
          const targetOpsHistoryTab = {json.dumps(ops_history_tab)};
          const targetOpsDetailTab = {json.dumps(ops_detail_tab)};
          const targetOpsQualityTab = {json.dumps(ops_quality_tab)};
          if (typeof setWorkspaceView === 'function') {{
            setWorkspaceView(targetView, {{
              backstageTab: targetBackstageTab,
              operationsHistoryTab: targetOpsHistoryTab,
              operationsDetailTab: targetOpsDetailTab,
              operationsQualityTab: targetOpsQualityTab,
            }});
          }} else {{
            document.querySelector(`[data-workspace-view="${{targetView}}"]`)?.click();
          }}
          if (targetView === 'backstage' && targetBackstageTab) {{
            if (typeof state !== 'undefined') {{
              state.researchBackstageTab = targetBackstageTab;
              if (targetBackstageTab === 'operations') {{
                if (targetOpsHistoryTab) {{
                  state.operationsHistoryTab = targetOpsHistoryTab;
                }}
                if (targetOpsDetailTab) {{
                  state.operationsDetailTab = targetOpsDetailTab;
                }}
                if (targetOpsQualityTab) {{
                  state.operationsQualityTab = targetOpsQualityTab;
                }}
              }}
            }}
            if (typeof renderResearchBackstage === 'function') {{
              renderResearchBackstage();
            }} else {{
              document.querySelector(`[data-research-backstage-tab="${{targetBackstageTab}}"]`)?.click();
            }}
            if (targetBackstageTab === 'operations' && typeof renderOperations === 'function') {{
              renderOperations();
            }}
            if (typeof syncWorkspaceViewLocation === 'function') {{
              syncWorkspaceViewLocation();
            }}
          }}
          try {{
            render();
          }} catch (error) {{
            // Keep the helper resilient if render is temporarily unavailable.
          }}
          const locationUrl = new URL(window.location.href);
          return {{
            requested: targetView,
            requestedBackstageTab: targetBackstageTab,
            requestedOpsHistoryTab: targetOpsHistoryTab,
            requestedOpsDetailTab: targetOpsDetailTab,
            requestedOpsQualityTab: targetOpsQualityTab,
            workspaceView: document.querySelector('#appShell')?.dataset.workspaceView || null,
            activeBackstageTab:
              document.querySelector('[data-research-backstage-tab].is-active')?.dataset.researchBackstageTab || null,
            activeOperationsHistoryTab:
              document.querySelector('[data-ops-history-tab].is-active')?.dataset.opsHistoryTab || null,
            activeOperationsDetailTab:
              document.querySelector('[data-ops-detail-tab].is-active')?.dataset.opsDetailTab || null,
            activeOperationsQualityTab:
              document.querySelector('[data-ops-quality-tab].is-active')?.dataset.opsQualityTab || null,
            locationView: locationUrl.searchParams.get('view'),
            locationBackstage: locationUrl.searchParams.get('backstage'),
            locationOpsHistory: locationUrl.searchParams.get('opsHistory'),
            locationOpsDetail: locationUrl.searchParams.get('opsDetail'),
            locationOpsQuality: locationUrl.searchParams.get('opsQuality'),
            frontstageVisible: !document.querySelector('#frontstageWorkspace')?.hidden,
            backstageVisible: !document.querySelector('#backstageWorkspace')?.hidden,
          }};
        }}""",
        timeout_seconds=60.0,
    )

def pick_operations_run_targets(session: str) -> dict:
    return eval_json_with_timeout(
        session,
        """() => {
          const pickCard = (selector, datasetKey) => {
            const cards = [...document.querySelectorAll(selector)];
            const activeCard = cards.find((item) => item.classList.contains('is-active')) || cards[0] || null;
            const activeValue = activeCard?.dataset?.[datasetKey] || null;
            const targetCard = cards.find((item) => item.dataset?.[datasetKey] && item.dataset[datasetKey] !== activeValue) || activeCard;
            return {
              count: cards.length,
              activeValue,
              targetValue: targetCard?.dataset?.[datasetKey] || null,
            };
          };
          return {
            import: pickCard('[data-run-id]', 'runId'),
            geo: pickCard('[data-geo-run-id]', 'geoRunId'),
          };
        }""",
        timeout_seconds=30.0,
    )


def pick_first_non_empty_select_option(session: str, selector: str) -> dict:
    return eval_json_with_timeout(
        session,
        f"""() => {{
          const select = document.querySelector({json.dumps(selector)});
          const option = select
            ? [...select.options].find((item) => item.value && item.value.trim())
            : null;
          return {{
            selector: {json.dumps(selector)},
            exists: Boolean(select),
            optionCount: select?.options?.length || 0,
            value: option?.value || null,
            label: option?.textContent?.trim() || null,
          }};
        }}""",
        timeout_seconds=30.0,
    )


def set_select_value(session: str, selector: str, value: str) -> dict:
    return eval_json_with_timeout(
        session,
        f"""async () => {{
          const select = document.querySelector({json.dumps(selector)});
          if (!select) {{
            return {{
              selector: {json.dumps(selector)},
              requestedValue: {json.dumps(value)},
              changed: false,
              reason: 'missing',
            }};
          }}
          select.value = {json.dumps(value)};
          select.dispatchEvent(new Event('change', {{ bubbles: true }}));
          return {{
            selector: {json.dumps(selector)},
            requestedValue: {json.dumps(value)},
            changed: true,
            currentValue: select.value || null,
          }};
        }}""",
        timeout_seconds=30.0,
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
              const timer = setTimeout(() => controller.abort('timeout'), 20000);
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


def reset_floor_watchlist_context(session: str) -> dict:
    return eval_json_with_timeout(
        session,
        """async () => {
          if (typeof state === 'undefined') {
            return { reset: false, reason: 'missing-state' };
          }
          state.granularity = 'floor';
          state.selectedImportRunId = null;
          state.selectedBaselineRunId = null;
          state.selectedImportRunDetail = null;
          state.selectedBaselineRunDetail = null;
          if (typeof applyDistrictScope === 'function') {
            await applyDistrictScope('all', {
              refresh: false,
              backgroundHydration: false,
            });
          } else {
            state.districtFilter = 'all';
            const select = document.querySelector('#districtFilter');
            if (select) {
              select.value = 'all';
            }
          }
          if (typeof loadFloorWatchlist === 'function') {
            await loadFloorWatchlist();
          }
          try {
            render();
          } catch (error) {
            // Keep the helper resilient if render is temporarily unavailable.
          }
          return {
            reset: true,
            district: typeof state !== 'undefined' ? state.districtFilter : null,
            selectedImportRunId: typeof state !== 'undefined' ? state.selectedImportRunId ?? null : null,
            selectedBaselineRunId: typeof state !== 'undefined' ? state.selectedBaselineRunId ?? null : null,
            loading: typeof state !== 'undefined' ? !!state.floorWatchlistLoading : null,
            count:
              typeof state !== 'undefined' && Array.isArray(state.floorWatchlistItems)
                ? state.floorWatchlistItems.length
                : null,
          };
        }""",
        timeout_seconds=90.0,
    )


def run_browser_capture_workflow_smoke(
    url: str,
    session: str,
    label: str,
    expected_workflow_action: str,
    *,
    headed: bool = False,
) -> dict:
    last_error: RuntimeError | None = None
    attempt_count = 2
    for attempt in range(1, attempt_count + 1):
        retry_suffix = "" if attempt == 1 else f"-retry{attempt}"
        smoke_session = f"{session}-{expected_workflow_action}{retry_suffix}"
        command = [
            sys.executable,
            str(SCRIPTS_DIR / "browser_capture_smoke.py"),
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
                    f"公开页采样 workflow smoke 输出不是合法 JSON: {expected_workflow_action} (attempt {attempt})\n"
                    f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
                )
                if attempt == attempt_count:
                    raise last_error from error
        except subprocess.TimeoutExpired as error:
            last_error = RuntimeError(
                f"公开页采样 workflow smoke 超时: {expected_workflow_action} (attempt {attempt})\n"
                f"STDOUT:\n{error.stdout or ''}\nSTDERR:\n{error.stderr or ''}"
            )
            if attempt == attempt_count:
                raise last_error from error
        except subprocess.CalledProcessError as error:
            last_error = RuntimeError(
                f"公开页采样 workflow smoke 失败: {expected_workflow_action} (attempt {attempt})\n"
                f"STDOUT:\n{error.stdout}\nSTDERR:\n{error.stderr}"
            )
            if attempt == attempt_count:
                raise last_error from error
    if last_error:
        raise last_error
    raise RuntimeError(f"公开页采样 workflow smoke 没有返回结果: {expected_workflow_action}")


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


def backstage_boot_url(
    base_url: str,
    *,
    backstage_tab: str,
    ops_history_tab: str | None = None,
    ops_detail_tab: str | None = None,
    ops_quality_tab: str | None = None,
    ops_import_run: str | None = None,
    ops_import_baseline: str | None = None,
    ops_geo_run: str | None = None,
    ops_geo_baseline: str | None = None,
) -> str:
    parsed = urlparse(base_url)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params["view"] = "backstage"
    params["backstage"] = backstage_tab
    if backstage_tab == "operations":
        if ops_history_tab:
            params["opsHistory"] = ops_history_tab
        if ops_detail_tab:
            params["opsDetail"] = ops_detail_tab
        if ops_quality_tab:
            params["opsQuality"] = ops_quality_tab
        if ops_import_run:
            params["opsImportRun"] = ops_import_run
        else:
            params.pop("opsImportRun", None)
        if ops_import_baseline:
            params["opsImportBaseline"] = ops_import_baseline
        else:
            params.pop("opsImportBaseline", None)
        if ops_geo_run:
            params["opsGeoRun"] = ops_geo_run
        else:
            params.pop("opsGeoRun", None)
        if ops_geo_baseline:
            params["opsGeoBaseline"] = ops_geo_baseline
        else:
            params.pop("opsGeoBaseline", None)
    else:
        params.pop("opsHistory", None)
        params.pop("opsDetail", None)
        params.pop("opsQuality", None)
        params.pop("opsImportRun", None)
        params.pop("opsImportBaseline", None)
        params.pop("opsGeoRun", None)
        params.pop("opsGeoBaseline", None)
    query = urlencode(params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, query, parsed.fragment))


def run_backstage_boot_smoke(
    url: str,
    session: str,
    label: str,
    *,
    backstage_tab: str = "schema",
    ops_history_tab: str | None = None,
    ops_detail_tab: str | None = None,
    ops_quality_tab: str | None = None,
    ops_import_run: str | None = None,
    ops_import_baseline: str | None = None,
    ops_geo_run: str | None = None,
    ops_geo_baseline: str | None = None,
    artifact_slug: str = "backstage-boot",
    headed: bool = False,
) -> dict:
    smoke_session = f"{session}-{artifact_slug}"
    smoke_url = backstage_boot_url(
        url,
        backstage_tab=backstage_tab,
        ops_history_tab=ops_history_tab,
        ops_detail_tab=ops_detail_tab,
        ops_quality_tab=ops_quality_tab,
        ops_import_run=ops_import_run,
        ops_import_baseline=ops_import_baseline,
        ops_geo_run=ops_geo_run,
        ops_geo_baseline=ops_geo_baseline,
    )
    opened_new_session = False
    try:
        opened_new_session, session_meta = pw.ensure_browser_session(
            smoke_session,
            smoke_url,
            headed=headed,
            navigate=True,
            fresh_session=True,
        )
        wait_for(
            smoke_session,
            f"""() => {{
              const params = new URL(window.location.href).searchParams;
              const activeHistory = document.querySelector('[data-ops-history-tab].is-active')?.dataset.opsHistoryTab || null;
              const activeDetail = document.querySelector('[data-ops-detail-tab].is-active')?.dataset.opsDetailTab || null;
              const activeQuality = document.querySelector('[data-ops-quality-tab].is-active')?.dataset.opsQualityTab || null;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'backstage'
                && params.get('view') === 'backstage'
                && params.get('backstage') === {json.dumps(backstage_tab)}
                && document.querySelector('#frontstageWorkspace')?.hidden === true
                && document.querySelector('#backstageWorkspace')?.hidden === false
                && document.querySelector(`[data-research-backstage-tab={json.dumps(backstage_tab)}]`)?.classList.contains('is-active')
                && (
                  {json.dumps(backstage_tab)} !== 'operations'
                  || (
                    params.get('opsHistory') === {json.dumps(ops_history_tab)}
                    && params.get('opsDetail') === {json.dumps(ops_detail_tab)}
                    && params.get('opsQuality') === {json.dumps(ops_quality_tab)}
                    && activeHistory === {json.dumps(ops_history_tab)}
                    && activeDetail === {json.dumps(ops_detail_tab)}
                    && activeQuality === {json.dumps(ops_quality_tab)}
                    && (
                      typeof state === 'undefined'
                      || params.get('opsImportRun') === (state.selectedImportRunId || null)
                    )
                    && (
                      typeof state === 'undefined'
                      || params.get('opsImportBaseline') === (state.selectedBaselineRunId || null)
                    )
                    && (
                      typeof state === 'undefined'
                      || params.get('opsGeoRun') === (state.selectedGeoAssetRunId || null)
                    )
                    && (
                      typeof state === 'undefined'
                      || params.get('opsGeoBaseline') === (state.selectedGeoBaselineRunId || null)
                    )
                    && (
                      {json.dumps(ops_import_run)} === null
                      || (typeof state !== 'undefined' && (state.selectedImportRunId || null) === {json.dumps(ops_import_run)})
                    )
                    && (
                      {json.dumps(ops_import_baseline)} === null
                      || (typeof state !== 'undefined' && (state.selectedBaselineRunId || null) === {json.dumps(ops_import_baseline)})
                    )
                    && (
                      {json.dumps(ops_geo_run)} === null
                      || (typeof state !== 'undefined' && (state.selectedGeoAssetRunId || null) === {json.dumps(ops_geo_run)})
                    )
                    && (
                      {json.dumps(ops_geo_baseline)} === null
                      || (typeof state !== 'undefined' && (state.selectedGeoBaselineRunId || null) === {json.dumps(ops_geo_baseline)})
                    )
                  )
                )
                && document.querySelector('#mapModeBadge')?.textContent?.trim()?.length > 0;
            }}""",
            timeout_seconds=60.0,
        )
        backstage_snapshot = pw.take_snapshot(smoke_session, label, artifact_slug)
        backstage_state = browser_state(smoke_session)

        switch_result = set_workspace_view(smoke_session, "frontstage")
        wait_for(
            smoke_session,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'frontstage'
                && !params.get('view')
                && !params.get('backstage')
                && !params.get('opsHistory')
                && !params.get('opsDetail')
                && !params.get('opsQuality')
                && !params.get('opsImportRun')
                && !params.get('opsImportBaseline')
                && !params.get('opsGeoRun')
                && !params.get('opsGeoBaseline')
                && document.querySelector('#frontstageWorkspace')?.hidden === false
                && document.querySelector('#backstageWorkspace')?.hidden === true
                && document.querySelector('#mapModeBadge')?.textContent?.trim() === 'AMap Live'
                && document.querySelectorAll('#summaryGrid [data-summary-metric]').length >= 6;
            }""",
            timeout_seconds=90.0,
        )
        frontstage_snapshot = pw.take_snapshot(smoke_session, label, f"{artifact_slug}-frontstage")
        frontstage_state = browser_state(smoke_session)
        return {
            "url": smoke_url,
            "sessionMeta": session_meta,
            "requestedBackstageTab": backstage_tab,
            "requestedOpsHistoryTab": ops_history_tab,
            "requestedOpsDetailTab": ops_detail_tab,
            "requestedOpsQualityTab": ops_quality_tab,
            "requestedOpsImportRun": ops_import_run,
            "requestedOpsImportBaseline": ops_import_baseline,
            "requestedOpsGeoRun": ops_geo_run,
            "requestedOpsGeoBaseline": ops_geo_baseline,
            "backstageState": backstage_state,
            "frontstageSwitchResult": switch_result,
            "frontstageState": frontstage_state,
            "artifacts": {
                "backstage": str(backstage_snapshot),
                "frontstage": str(frontstage_snapshot),
            },
        }
    finally:
        if opened_new_session:
            pw.close_session_quietly(smoke_session)


def build_assertions(data: dict[str, object]) -> dict[str, dict[str, object]]:
    initial = data.get("initialState") or {}
    backstage_boot = data.get("backstageBootSmoke") or {}
    backstage_boot_state = backstage_boot.get("backstageState") or {}
    backstage_boot_frontstage = backstage_boot.get("frontstageState") or {}
    operations_backstage_boot = data.get("operationsBackstageBootSmoke") or {}
    operations_backstage_boot_state = operations_backstage_boot.get("backstageState") or {}
    operations_backstage_boot_frontstage = operations_backstage_boot.get("frontstageState") or {}
    operations_selection_boot = data.get("operationsSelectionBackstageBootSmoke") or {}
    operations_selection_boot_state = operations_selection_boot.get("backstageState") or {}
    operations_run_selection = data.get("operationsRunSelectionState") or {}
    filter_display = data.get("filterDisplayState") or {}
    backstage_strategy = data.get("backstageStrategyState") or {}
    backstage_operations = data.get("backstageOperationsState") or {}
    backstage_pipeline = data.get("backstagePipelineState") or {}
    backstage = data.get("backstageState") or {}
    frontstage_restore = data.get("frontstageRestoreState") or {}
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
        "backstage_direct_boot_defers_map_init": {
            "passed": backstage_boot_state.get("workspaceView") == "backstage"
            and backstage_boot_state.get("locationView") == "backstage"
            and backstage_boot_state.get("locationBackstage") == "schema"
            and backstage_boot_state.get("locationOpsHistory") is None
            and backstage_boot_state.get("locationOpsDetail") is None
            and backstage_boot_state.get("locationOpsQuality") is None
            and backstage_boot_state.get("locationOpsImportRun") is None
            and backstage_boot_state.get("locationOpsImportBaseline") is None
            and backstage_boot_state.get("locationOpsGeoRun") is None
            and backstage_boot_state.get("locationOpsGeoBaseline") is None
            and backstage_boot_state.get("mapMode") == "前台待启用"
            and backstage_boot_state.get("frontstageVisible") is False
            and backstage_boot_state.get("backstageVisible") is True,
            "actual": {
                "workspaceView": backstage_boot_state.get("workspaceView"),
                "locationView": backstage_boot_state.get("locationView"),
                "locationBackstage": backstage_boot_state.get("locationBackstage"),
                "locationOpsHistory": backstage_boot_state.get("locationOpsHistory"),
                "locationOpsDetail": backstage_boot_state.get("locationOpsDetail"),
                "locationOpsQuality": backstage_boot_state.get("locationOpsQuality"),
                "locationOpsImportRun": backstage_boot_state.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage_boot_state.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage_boot_state.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage_boot_state.get("locationOpsGeoBaseline"),
                "mapMode": backstage_boot_state.get("mapMode"),
                "frontstageVisible": backstage_boot_state.get("frontstageVisible"),
                "backstageVisible": backstage_boot_state.get("backstageVisible"),
            },
        },
        "backstage_boot_frontstage_switch_initializes_map": {
            "passed": backstage_boot_frontstage.get("workspaceView") == "frontstage"
            and backstage_boot_frontstage.get("locationView") is None
            and backstage_boot_frontstage.get("locationBackstage") is None
            and backstage_boot_frontstage.get("locationOpsHistory") is None
            and backstage_boot_frontstage.get("locationOpsDetail") is None
            and backstage_boot_frontstage.get("locationOpsQuality") is None
            and backstage_boot_frontstage.get("locationOpsImportRun") is None
            and backstage_boot_frontstage.get("locationOpsImportBaseline") is None
            and backstage_boot_frontstage.get("locationOpsGeoRun") is None
            and backstage_boot_frontstage.get("locationOpsGeoBaseline") is None
            and backstage_boot_frontstage.get("mapMode") == "AMap Live"
            and backstage_boot_frontstage.get("frontstageVisible") is True
            and backstage_boot_frontstage.get("backstageVisible") is False
            and len(backstage_boot_frontstage.get("summaryCards") or []) >= 6,
            "actual": {
                "workspaceView": backstage_boot_frontstage.get("workspaceView"),
                "locationView": backstage_boot_frontstage.get("locationView"),
                "locationBackstage": backstage_boot_frontstage.get("locationBackstage"),
                "locationOpsHistory": backstage_boot_frontstage.get("locationOpsHistory"),
                "locationOpsDetail": backstage_boot_frontstage.get("locationOpsDetail"),
                "locationOpsQuality": backstage_boot_frontstage.get("locationOpsQuality"),
                "locationOpsImportRun": backstage_boot_frontstage.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage_boot_frontstage.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage_boot_frontstage.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage_boot_frontstage.get("locationOpsGeoBaseline"),
                "mapMode": backstage_boot_frontstage.get("mapMode"),
                "frontstageVisible": backstage_boot_frontstage.get("frontstageVisible"),
                "backstageVisible": backstage_boot_frontstage.get("backstageVisible"),
                "summaryCards": backstage_boot_frontstage.get("summaryCards"),
            },
        },
        "operations_backstage_direct_boot_restores_ops_tabs": {
            "passed": operations_backstage_boot_state.get("workspaceView") == "backstage"
            and operations_backstage_boot_state.get("locationView") == "backstage"
            and operations_backstage_boot_state.get("locationBackstage") == "operations"
            and operations_backstage_boot_state.get("locationOpsHistory") == "metrics"
            and operations_backstage_boot_state.get("locationOpsDetail") == "sources"
            and operations_backstage_boot_state.get("locationOpsQuality") == "anchor"
            and operations_backstage_boot_state.get("locationOpsImportRun")
            == operations_backstage_boot_state.get("selectedImportRunId")
            and operations_backstage_boot_state.get("locationOpsImportBaseline")
            == operations_backstage_boot_state.get("selectedBaselineRunId")
            and operations_backstage_boot_state.get("locationOpsGeoRun")
            == operations_backstage_boot_state.get("selectedGeoAssetRunId")
            and operations_backstage_boot_state.get("locationOpsGeoBaseline")
            == operations_backstage_boot_state.get("selectedGeoBaselineRunId")
            and operations_backstage_boot_state.get("activeBackstageTab") == "operations"
            and operations_backstage_boot_state.get("activeOperationsHistoryTab") == "metrics"
            and operations_backstage_boot_state.get("activeOperationsDetailTab") == "sources"
            and operations_backstage_boot_state.get("activeOperationsQualityTab") == "anchor"
            and operations_backstage_boot_state.get("visibleBackstagePanels") == ["operations"]
            and operations_backstage_boot_state.get("visibleOperationsHistoryPanels") == ["metrics"]
            and operations_backstage_boot_state.get("visibleOperationsDetailPanels") == ["sources"]
            and operations_backstage_boot_state.get("visibleOperationsQualityPanels") == ["anchor"]
            and operations_backstage_boot_state.get("mapMode") == "前台待启用"
            and operations_backstage_boot_state.get("frontstageVisible") is False
            and operations_backstage_boot_state.get("backstageVisible") is True,
            "actual": {
                "workspaceView": operations_backstage_boot_state.get("workspaceView"),
                "locationView": operations_backstage_boot_state.get("locationView"),
                "locationBackstage": operations_backstage_boot_state.get("locationBackstage"),
                "locationOpsHistory": operations_backstage_boot_state.get("locationOpsHistory"),
                "locationOpsDetail": operations_backstage_boot_state.get("locationOpsDetail"),
                "locationOpsQuality": operations_backstage_boot_state.get("locationOpsQuality"),
                "locationOpsImportRun": operations_backstage_boot_state.get("locationOpsImportRun"),
                "locationOpsImportBaseline": operations_backstage_boot_state.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": operations_backstage_boot_state.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": operations_backstage_boot_state.get("locationOpsGeoBaseline"),
                "activeBackstageTab": operations_backstage_boot_state.get("activeBackstageTab"),
                "activeOperationsHistoryTab": operations_backstage_boot_state.get("activeOperationsHistoryTab"),
                "activeOperationsDetailTab": operations_backstage_boot_state.get("activeOperationsDetailTab"),
                "activeOperationsQualityTab": operations_backstage_boot_state.get("activeOperationsQualityTab"),
                "selectedImportRunId": operations_backstage_boot_state.get("selectedImportRunId"),
                "selectedBaselineRunId": operations_backstage_boot_state.get("selectedBaselineRunId"),
                "selectedGeoAssetRunId": operations_backstage_boot_state.get("selectedGeoAssetRunId"),
                "selectedGeoBaselineRunId": operations_backstage_boot_state.get("selectedGeoBaselineRunId"),
                "visibleBackstagePanels": operations_backstage_boot_state.get("visibleBackstagePanels"),
                "visibleOperationsHistoryPanels": operations_backstage_boot_state.get("visibleOperationsHistoryPanels"),
                "visibleOperationsDetailPanels": operations_backstage_boot_state.get("visibleOperationsDetailPanels"),
                "visibleOperationsQualityPanels": operations_backstage_boot_state.get("visibleOperationsQualityPanels"),
                "mapMode": operations_backstage_boot_state.get("mapMode"),
            },
        },
        "operations_backstage_boot_frontstage_switch_initializes_map": {
            "passed": operations_backstage_boot_frontstage.get("workspaceView") == "frontstage"
            and operations_backstage_boot_frontstage.get("locationView") is None
            and operations_backstage_boot_frontstage.get("locationBackstage") is None
            and operations_backstage_boot_frontstage.get("locationOpsHistory") is None
            and operations_backstage_boot_frontstage.get("locationOpsDetail") is None
            and operations_backstage_boot_frontstage.get("locationOpsQuality") is None
            and operations_backstage_boot_frontstage.get("locationOpsImportRun") is None
            and operations_backstage_boot_frontstage.get("locationOpsImportBaseline") is None
            and operations_backstage_boot_frontstage.get("locationOpsGeoRun") is None
            and operations_backstage_boot_frontstage.get("locationOpsGeoBaseline") is None
            and operations_backstage_boot_frontstage.get("mapMode") == "AMap Live"
            and operations_backstage_boot_frontstage.get("frontstageVisible") is True
            and operations_backstage_boot_frontstage.get("backstageVisible") is False
            and len(operations_backstage_boot_frontstage.get("summaryCards") or []) >= 6,
            "actual": {
                "workspaceView": operations_backstage_boot_frontstage.get("workspaceView"),
                "locationView": operations_backstage_boot_frontstage.get("locationView"),
                "locationBackstage": operations_backstage_boot_frontstage.get("locationBackstage"),
                "locationOpsHistory": operations_backstage_boot_frontstage.get("locationOpsHistory"),
                "locationOpsDetail": operations_backstage_boot_frontstage.get("locationOpsDetail"),
                "locationOpsQuality": operations_backstage_boot_frontstage.get("locationOpsQuality"),
                "locationOpsImportRun": operations_backstage_boot_frontstage.get("locationOpsImportRun"),
                "locationOpsImportBaseline": operations_backstage_boot_frontstage.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": operations_backstage_boot_frontstage.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": operations_backstage_boot_frontstage.get("locationOpsGeoBaseline"),
                "mapMode": operations_backstage_boot_frontstage.get("mapMode"),
                "frontstageVisible": operations_backstage_boot_frontstage.get("frontstageVisible"),
                "backstageVisible": operations_backstage_boot_frontstage.get("backstageVisible"),
                "summaryCards": operations_backstage_boot_frontstage.get("summaryCards"),
            },
        },
        "operations_backstage_selection_deep_link_restores_runs": {
            "passed": operations_selection_boot_state.get("workspaceView") == "backstage"
            and operations_selection_boot_state.get("locationView") == "backstage"
            and operations_selection_boot_state.get("locationBackstage") == "operations"
            and operations_selection_boot_state.get("locationOpsHistory")
            == operations_selection_boot.get("requestedOpsHistoryTab")
            and operations_selection_boot_state.get("locationOpsDetail")
            == operations_selection_boot.get("requestedOpsDetailTab")
            and operations_selection_boot_state.get("locationOpsQuality")
            == operations_selection_boot.get("requestedOpsQualityTab")
            and operations_selection_boot_state.get("locationOpsImportRun")
            == operations_selection_boot.get("requestedOpsImportRun")
            and operations_selection_boot_state.get("locationOpsImportBaseline")
            == operations_selection_boot.get("requestedOpsImportBaseline")
            and operations_selection_boot_state.get("locationOpsGeoRun")
            == operations_selection_boot.get("requestedOpsGeoRun")
            and operations_selection_boot_state.get("locationOpsGeoBaseline")
            == operations_selection_boot.get("requestedOpsGeoBaseline")
            and operations_selection_boot_state.get("selectedImportRunId")
            == operations_selection_boot.get("requestedOpsImportRun")
            and operations_selection_boot_state.get("selectedBaselineRunId")
            == operations_selection_boot.get("requestedOpsImportBaseline")
            and operations_selection_boot_state.get("selectedGeoAssetRunId")
            == operations_selection_boot.get("requestedOpsGeoRun")
            and operations_selection_boot_state.get("selectedGeoBaselineRunId")
            == operations_selection_boot.get("requestedOpsGeoBaseline")
            and operations_selection_boot_state.get("activeBackstageTab") == "operations"
            and operations_selection_boot_state.get("visibleBackstagePanels") == ["operations"],
            "actual": {
                "requestedOpsHistoryTab": operations_selection_boot.get("requestedOpsHistoryTab"),
                "requestedOpsDetailTab": operations_selection_boot.get("requestedOpsDetailTab"),
                "requestedOpsQualityTab": operations_selection_boot.get("requestedOpsQualityTab"),
                "requestedOpsImportRun": operations_selection_boot.get("requestedOpsImportRun"),
                "requestedOpsImportBaseline": operations_selection_boot.get("requestedOpsImportBaseline"),
                "requestedOpsGeoRun": operations_selection_boot.get("requestedOpsGeoRun"),
                "requestedOpsGeoBaseline": operations_selection_boot.get("requestedOpsGeoBaseline"),
                "locationOpsHistory": operations_selection_boot_state.get("locationOpsHistory"),
                "locationOpsDetail": operations_selection_boot_state.get("locationOpsDetail"),
                "locationOpsQuality": operations_selection_boot_state.get("locationOpsQuality"),
                "locationOpsImportRun": operations_selection_boot_state.get("locationOpsImportRun"),
                "locationOpsImportBaseline": operations_selection_boot_state.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": operations_selection_boot_state.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": operations_selection_boot_state.get("locationOpsGeoBaseline"),
                "selectedImportRunId": operations_selection_boot_state.get("selectedImportRunId"),
                "selectedBaselineRunId": operations_selection_boot_state.get("selectedBaselineRunId"),
                "selectedGeoAssetRunId": operations_selection_boot_state.get("selectedGeoAssetRunId"),
                "selectedGeoBaselineRunId": operations_selection_boot_state.get("selectedGeoBaselineRunId"),
                "activeBackstageTab": operations_selection_boot_state.get("activeBackstageTab"),
                "visibleBackstagePanels": operations_selection_boot_state.get("visibleBackstagePanels"),
            },
        },
        "filter_display_tab_switches_panel": {
            "passed": filter_display.get("activeFilterTab") == "display"
            and filter_display.get("visibleFilterPanels") == ["display"],
            "actual": {
                "activeFilterTab": filter_display.get("activeFilterTab"),
                "visibleFilterPanels": filter_display.get("visibleFilterPanels"),
            },
        },
        "workspace_backstage_strategy_switches_surface": {
            "passed": backstage_strategy.get("workspaceView") == "backstage"
            and backstage_strategy.get("locationView") == "backstage"
            and backstage_strategy.get("locationBackstage") == "strategy"
            and backstage_strategy.get("locationOpsHistory") is None
            and backstage_strategy.get("locationOpsDetail") is None
            and backstage_strategy.get("locationOpsQuality") is None
            and backstage_strategy.get("locationOpsImportRun") is None
            and backstage_strategy.get("locationOpsImportBaseline") is None
            and backstage_strategy.get("locationOpsGeoRun") is None
            and backstage_strategy.get("locationOpsGeoBaseline") is None
            and backstage_strategy.get("frontstageVisible") is False
            and backstage_strategy.get("backstageVisible") is True
            and backstage_strategy.get("overviewBandVisible") is False
            and backstage_strategy.get("activeBackstageTab") == "strategy"
            and backstage_strategy.get("visibleBackstagePanels") == ["strategy"],
            "actual": {
                "workspaceView": backstage_strategy.get("workspaceView"),
                "locationView": backstage_strategy.get("locationView"),
                "locationBackstage": backstage_strategy.get("locationBackstage"),
                "locationOpsHistory": backstage_strategy.get("locationOpsHistory"),
                "locationOpsDetail": backstage_strategy.get("locationOpsDetail"),
                "locationOpsQuality": backstage_strategy.get("locationOpsQuality"),
                "locationOpsImportRun": backstage_strategy.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage_strategy.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage_strategy.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage_strategy.get("locationOpsGeoBaseline"),
                "frontstageVisible": backstage_strategy.get("frontstageVisible"),
                "backstageVisible": backstage_strategy.get("backstageVisible"),
                "overviewBandVisible": backstage_strategy.get("overviewBandVisible"),
                "activeBackstageTab": backstage_strategy.get("activeBackstageTab"),
                "visibleBackstagePanels": backstage_strategy.get("visibleBackstagePanels"),
            },
        },
        "workspace_backstage_operations_switches_surface": {
            "passed": backstage_operations.get("workspaceView") == "backstage"
            and backstage_operations.get("locationView") == "backstage"
            and backstage_operations.get("locationBackstage") == "operations"
            and backstage_operations.get("locationOpsHistory") == "metrics"
            and backstage_operations.get("locationOpsDetail") == "sources"
            and backstage_operations.get("locationOpsQuality") == "anchor"
            and backstage_operations.get("locationOpsImportRun") == backstage_operations.get("selectedImportRunId")
            and backstage_operations.get("locationOpsImportBaseline") == backstage_operations.get("selectedBaselineRunId")
            and backstage_operations.get("locationOpsGeoRun") == backstage_operations.get("selectedGeoAssetRunId")
            and backstage_operations.get("locationOpsGeoBaseline") == backstage_operations.get("selectedGeoBaselineRunId")
            and backstage_operations.get("frontstageVisible") is False
            and backstage_operations.get("backstageVisible") is True
            and backstage_operations.get("overviewBandVisible") is False
            and backstage_operations.get("activeBackstageTab") == "operations"
            and backstage_operations.get("visibleBackstagePanels") == ["operations"]
            and backstage_operations.get("activeOperationsHistoryTab") == "metrics"
            and backstage_operations.get("visibleOperationsHistoryPanels") == ["metrics"]
            and backstage_operations.get("activeOperationsDetailTab") == "sources"
            and backstage_operations.get("visibleOperationsDetailPanels") == ["sources"]
            and backstage_operations.get("activeOperationsQualityTab") == "anchor"
            and backstage_operations.get("visibleOperationsQualityPanels") == ["anchor"],
            "actual": {
                "workspaceView": backstage_operations.get("workspaceView"),
                "locationView": backstage_operations.get("locationView"),
                "locationBackstage": backstage_operations.get("locationBackstage"),
                "locationOpsHistory": backstage_operations.get("locationOpsHistory"),
                "locationOpsDetail": backstage_operations.get("locationOpsDetail"),
                "locationOpsQuality": backstage_operations.get("locationOpsQuality"),
                "locationOpsImportRun": backstage_operations.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage_operations.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage_operations.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage_operations.get("locationOpsGeoBaseline"),
                "selectedImportRunId": backstage_operations.get("selectedImportRunId"),
                "selectedBaselineRunId": backstage_operations.get("selectedBaselineRunId"),
                "selectedGeoAssetRunId": backstage_operations.get("selectedGeoAssetRunId"),
                "selectedGeoBaselineRunId": backstage_operations.get("selectedGeoBaselineRunId"),
                "frontstageVisible": backstage_operations.get("frontstageVisible"),
                "backstageVisible": backstage_operations.get("backstageVisible"),
                "overviewBandVisible": backstage_operations.get("overviewBandVisible"),
                "activeBackstageTab": backstage_operations.get("activeBackstageTab"),
                "visibleBackstagePanels": backstage_operations.get("visibleBackstagePanels"),
                "activeOperationsHistoryTab": backstage_operations.get("activeOperationsHistoryTab"),
                "visibleOperationsHistoryPanels": backstage_operations.get("visibleOperationsHistoryPanels"),
                "activeOperationsDetailTab": backstage_operations.get("activeOperationsDetailTab"),
                "visibleOperationsDetailPanels": backstage_operations.get("visibleOperationsDetailPanels"),
                "activeOperationsQualityTab": backstage_operations.get("activeOperationsQualityTab"),
                "visibleOperationsQualityPanels": backstage_operations.get("visibleOperationsQualityPanels"),
            },
        },
        "workspace_backstage_pipeline_switches_surface": {
            "passed": backstage_pipeline.get("workspaceView") == "backstage"
            and backstage_pipeline.get("locationView") == "backstage"
            and backstage_pipeline.get("locationBackstage") == "pipeline"
            and backstage_pipeline.get("locationOpsHistory") is None
            and backstage_pipeline.get("locationOpsDetail") is None
            and backstage_pipeline.get("locationOpsQuality") is None
            and backstage_pipeline.get("locationOpsImportRun") is None
            and backstage_pipeline.get("locationOpsImportBaseline") is None
            and backstage_pipeline.get("locationOpsGeoRun") is None
            and backstage_pipeline.get("locationOpsGeoBaseline") is None
            and backstage_pipeline.get("frontstageVisible") is False
            and backstage_pipeline.get("backstageVisible") is True
            and backstage_pipeline.get("overviewBandVisible") is False
            and backstage_pipeline.get("activeBackstageTab") == "pipeline"
            and backstage_pipeline.get("visibleBackstagePanels") == ["pipeline"],
            "actual": {
                "workspaceView": backstage_pipeline.get("workspaceView"),
                "locationView": backstage_pipeline.get("locationView"),
                "locationBackstage": backstage_pipeline.get("locationBackstage"),
                "locationOpsHistory": backstage_pipeline.get("locationOpsHistory"),
                "locationOpsDetail": backstage_pipeline.get("locationOpsDetail"),
                "locationOpsQuality": backstage_pipeline.get("locationOpsQuality"),
                "locationOpsImportRun": backstage_pipeline.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage_pipeline.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage_pipeline.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage_pipeline.get("locationOpsGeoBaseline"),
                "frontstageVisible": backstage_pipeline.get("frontstageVisible"),
                "backstageVisible": backstage_pipeline.get("backstageVisible"),
                "overviewBandVisible": backstage_pipeline.get("overviewBandVisible"),
                "activeBackstageTab": backstage_pipeline.get("activeBackstageTab"),
                "visibleBackstagePanels": backstage_pipeline.get("visibleBackstagePanels"),
            },
        },
        "workspace_backstage_switches_surface": {
            "passed": backstage.get("workspaceView") == "backstage"
            and backstage.get("locationView") == "backstage"
            and backstage.get("locationBackstage") == "schema"
            and backstage.get("locationOpsHistory") is None
            and backstage.get("locationOpsDetail") is None
            and backstage.get("locationOpsQuality") is None
            and backstage.get("locationOpsImportRun") is None
            and backstage.get("locationOpsImportBaseline") is None
            and backstage.get("locationOpsGeoRun") is None
            and backstage.get("locationOpsGeoBaseline") is None
            and backstage.get("frontstageVisible") is False
            and backstage.get("backstageVisible") is True
            and backstage.get("overviewBandVisible") is False
            and backstage.get("activeBackstageTab") == "schema"
            and backstage.get("visibleBackstagePanels") == ["schema"],
            "actual": {
                "workspaceView": backstage.get("workspaceView"),
                "locationView": backstage.get("locationView"),
                "locationBackstage": backstage.get("locationBackstage"),
                "locationOpsHistory": backstage.get("locationOpsHistory"),
                "locationOpsDetail": backstage.get("locationOpsDetail"),
                "locationOpsQuality": backstage.get("locationOpsQuality"),
                "locationOpsImportRun": backstage.get("locationOpsImportRun"),
                "locationOpsImportBaseline": backstage.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": backstage.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": backstage.get("locationOpsGeoBaseline"),
                "frontstageVisible": backstage.get("frontstageVisible"),
                "backstageVisible": backstage.get("backstageVisible"),
                "overviewBandVisible": backstage.get("overviewBandVisible"),
                "activeBackstageTab": backstage.get("activeBackstageTab"),
                "visibleBackstagePanels": backstage.get("visibleBackstagePanels"),
            },
        },
        "workspace_frontstage_restore_recovers_map_surface": {
            "passed": frontstage_restore.get("workspaceView") == "frontstage"
            and frontstage_restore.get("locationView") is None
            and frontstage_restore.get("locationBackstage") is None
            and frontstage_restore.get("locationOpsHistory") is None
            and frontstage_restore.get("locationOpsDetail") is None
            and frontstage_restore.get("locationOpsQuality") is None
            and frontstage_restore.get("locationOpsImportRun") is None
            and frontstage_restore.get("locationOpsImportBaseline") is None
            and frontstage_restore.get("locationOpsGeoRun") is None
            and frontstage_restore.get("locationOpsGeoBaseline") is None
            and frontstage_restore.get("frontstageVisible") is True
            and frontstage_restore.get("backstageVisible") is False
            and frontstage_restore.get("overviewBandVisible") is True
            and len(frontstage_restore.get("summaryCards") or []) >= 6,
            "actual": {
                "workspaceView": frontstage_restore.get("workspaceView"),
                "locationView": frontstage_restore.get("locationView"),
                "locationBackstage": frontstage_restore.get("locationBackstage"),
                "locationOpsHistory": frontstage_restore.get("locationOpsHistory"),
                "locationOpsDetail": frontstage_restore.get("locationOpsDetail"),
                "locationOpsQuality": frontstage_restore.get("locationOpsQuality"),
                "locationOpsImportRun": frontstage_restore.get("locationOpsImportRun"),
                "locationOpsImportBaseline": frontstage_restore.get("locationOpsImportBaseline"),
                "locationOpsGeoRun": frontstage_restore.get("locationOpsGeoRun"),
                "locationOpsGeoBaseline": frontstage_restore.get("locationOpsGeoBaseline"),
                "frontstageVisible": frontstage_restore.get("frontstageVisible"),
                "backstageVisible": frontstage_restore.get("backstageVisible"),
                "overviewBandVisible": frontstage_restore.get("overviewBandVisible"),
                "summaryCards": frontstage_restore.get("summaryCards"),
            },
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
    parser = argparse.ArgumentParser(description="Run a full browser regression for Yieldwise.")
    parser.add_argument("--session", default="atlas-full-regression", help="Playwright browser session")
    parser.add_argument("--label", default=f"atlas-full-regression-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    parser.add_argument("--url", default="http://127.0.0.1:8013/backstage/")
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

    backstage_boot_smoke = run_backstage_boot_smoke(
        args.url,
        args.session,
        args.label,
        headed=args.headed,
    )
    artifacts["steps"].append(
        {
            "name": "backstage-boot-smoke",
            "result": {
                "mapMode": backstage_boot_smoke.get("backstageState", {}).get("mapMode"),
                "workspaceView": backstage_boot_smoke.get("backstageState", {}).get("workspaceView"),
                "frontstageMapMode": backstage_boot_smoke.get("frontstageState", {}).get("mapMode"),
            },
        }
    )
    artifacts["backstageBootSmoke"] = backstage_boot_smoke

    operations_backstage_boot_smoke = run_backstage_boot_smoke(
        args.url,
        args.session,
        args.label,
        backstage_tab="operations",
        ops_history_tab="metrics",
        ops_detail_tab="sources",
        ops_quality_tab="anchor",
        artifact_slug="backstage-boot-operations",
        headed=args.headed,
    )
    artifacts["steps"].append(
        {
            "name": "backstage-boot-operations-smoke",
            "result": {
                "workspaceView": operations_backstage_boot_smoke.get("backstageState", {}).get("workspaceView"),
                "backstageTab": operations_backstage_boot_smoke.get("backstageState", {}).get("activeBackstageTab"),
                "opsHistoryTab": operations_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsHistoryTab"),
                "opsDetailTab": operations_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsDetailTab"),
                "opsQualityTab": operations_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsQualityTab"),
                "frontstageMapMode": operations_backstage_boot_smoke.get("frontstageState", {}).get("mapMode"),
            },
        }
    )
    artifacts["operationsBackstageBootSmoke"] = operations_backstage_boot_smoke

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

        filter_display_result = set_filter_panel_tab(session_name, "display")
        wait_for(
            session_name,
            """() => document.querySelector('[data-filter-tab="display"]')?.classList.contains('is-active')
              && !document.querySelector('[data-filter-panel="display"]')?.hidden""",
            timeout_seconds=30.0,
        )
        filter_display_snapshot = pw.take_snapshot(session_name, args.label, "filter-display")
        filter_display_state = browser_state(session_name)
        artifacts["steps"].append(
            {"name": "filter-display-tab", "result": filter_display_result, "snapshot": str(filter_display_snapshot)}
        )
        artifacts["filterDisplayState"] = filter_display_state

        filter_scope_result = set_filter_panel_tab(session_name, "scope")
        wait_for(
            session_name,
            """() => document.querySelector('[data-filter-tab="scope"]')?.classList.contains('is-active')
              && !document.querySelector('[data-filter-panel="scope"]')?.hidden""",
            timeout_seconds=30.0,
        )
        artifacts["steps"].append({"name": "filter-scope-restore", "result": filter_scope_result})

        backstage_strategy_result = set_workspace_view(session_name, "backstage", backstage_tab="strategy")
        wait_for(
            session_name,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'backstage'
                && params.get('view') === 'backstage'
                && params.get('backstage') === 'strategy'
                && !params.get('opsHistory')
                && !params.get('opsDetail')
                && !params.get('opsQuality')
                && !params.get('opsImportRun')
                && !params.get('opsImportBaseline')
                && !params.get('opsGeoRun')
                && !params.get('opsGeoBaseline')
                && document.querySelector('#frontstageWorkspace')?.hidden === true
                && document.querySelector('#backstageWorkspace')?.hidden === false
                && document.querySelector('[data-research-backstage-tab="strategy"]')?.classList.contains('is-active');
            }""",
            timeout_seconds=30.0,
        )
        backstage_strategy_snapshot = pw.take_snapshot(session_name, args.label, "backstage-strategy")
        backstage_strategy_state = browser_state(session_name)
        artifacts["steps"].append(
            {
                "name": "workspace-backstage-strategy",
                "result": backstage_strategy_result,
                "snapshot": str(backstage_strategy_snapshot),
            }
        )
        artifacts["backstageStrategyState"] = backstage_strategy_state

        backstage_operations_result = set_workspace_view(
            session_name,
            "backstage",
            backstage_tab="operations",
            ops_history_tab="metrics",
            ops_detail_tab="sources",
            ops_quality_tab="anchor",
        )
        wait_for(
            session_name,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'backstage'
                && params.get('view') === 'backstage'
                && params.get('backstage') === 'operations'
                && params.get('opsHistory') === 'metrics'
                && params.get('opsDetail') === 'sources'
                && params.get('opsQuality') === 'anchor'
                && params.get('opsImportRun') === (typeof state !== 'undefined' ? (state.selectedImportRunId || null) : null)
                && params.get('opsImportBaseline') === (typeof state !== 'undefined' ? (state.selectedBaselineRunId || null) : null)
                && params.get('opsGeoRun') === (typeof state !== 'undefined' ? (state.selectedGeoAssetRunId || null) : null)
                && params.get('opsGeoBaseline') === (typeof state !== 'undefined' ? (state.selectedGeoBaselineRunId || null) : null)
                && document.querySelector('#frontstageWorkspace')?.hidden === true
                && document.querySelector('#backstageWorkspace')?.hidden === false
                && document.querySelector('[data-research-backstage-tab="operations"]')?.classList.contains('is-active')
                && document.querySelector('[data-ops-history-tab="metrics"]')?.classList.contains('is-active')
                && document.querySelector('[data-ops-detail-tab="sources"]')?.classList.contains('is-active')
                && document.querySelector('[data-ops-quality-tab="anchor"]')?.classList.contains('is-active')
                && !document.querySelector('[data-ops-history-panel="metrics"]')?.hidden
                && !document.querySelector('[data-ops-detail-panel="sources"]')?.hidden
                && !document.querySelector('[data-ops-quality-panel="anchor"]')?.hidden;
            }""",
            timeout_seconds=30.0,
        )
        backstage_operations_snapshot = pw.take_snapshot(session_name, args.label, "backstage-operations")
        backstage_operations_state = browser_state(session_name)
        artifacts["steps"].append(
            {
                "name": "workspace-backstage-operations",
                "result": backstage_operations_result,
                "snapshot": str(backstage_operations_snapshot),
            }
        )
        artifacts["backstageOperationsState"] = backstage_operations_state

        operations_run_targets = pick_operations_run_targets(session_name)
        import_target = (operations_run_targets.get("import") or {}).get("targetValue")
        if import_target:
            import_selection_result = click_via_dom(
                session_name,
                f"""(() => {{
                  const card = document.querySelector('[data-run-id="{import_target}"]');
                  card?.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                  return {{
                    clicked: Boolean(card),
                    runId: card?.dataset.runId || null,
                  }};
                }})()""",
            )
            wait_for(
                session_name,
                f"""() => {{
                  const params = new URL(window.location.href).searchParams;
                  return (typeof state !== 'undefined' && (state.selectedImportRunId || null) === {json.dumps(import_target)})
                    && params.get('opsImportRun') === {json.dumps(import_target)}
                    && params.get('opsHistory') === 'import'
                    && params.get('opsDetail') === 'import'
                    && document.querySelector('[data-ops-history-tab="import"]')?.classList.contains('is-active')
                    && document.querySelector('[data-ops-detail-tab="import"]')?.classList.contains('is-active');
                }}""",
                timeout_seconds=60.0,
            )
        else:
            import_selection_result = {"clicked": False, "runId": backstage_operations_state.get("selectedImportRunId")}

        import_baseline_option = pick_first_non_empty_select_option(session_name, "[data-baseline-run-select]")
        if import_baseline_option.get("value"):
            import_baseline_result = set_select_value(
                session_name,
                "[data-baseline-run-select]",
                import_baseline_option["value"],
            )
            wait_for(
                session_name,
                f"""() => {{
                  const params = new URL(window.location.href).searchParams;
                  return (typeof state !== 'undefined' && (state.selectedBaselineRunId || null) === {json.dumps(import_baseline_option["value"])})
                    && params.get('opsImportBaseline') === {json.dumps(import_baseline_option["value"])};
                }}""",
                timeout_seconds=60.0,
            )
        else:
            import_baseline_result = {
                "changed": False,
                "requestedValue": None,
                "reason": "no-baseline-option",
            }

        geo_target = (operations_run_targets.get("geo") or {}).get("targetValue")
        if geo_target:
            geo_selection_result = click_via_dom(
                session_name,
                f"""(() => {{
                  const card = document.querySelector('[data-geo-run-id="{geo_target}"]');
                  card?.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                  return {{
                    clicked: Boolean(card),
                    runId: card?.dataset.geoRunId || null,
                  }};
                }})()""",
            )
            wait_for(
                session_name,
                f"""() => {{
                  const params = new URL(window.location.href).searchParams;
                  return (typeof state !== 'undefined' && (state.selectedGeoAssetRunId || null) === {json.dumps(geo_target)})
                    && params.get('opsGeoRun') === {json.dumps(geo_target)}
                    && params.get('opsHistory') === 'geo'
                    && params.get('opsDetail') === 'geo'
                    && document.querySelector('[data-ops-history-tab="geo"]')?.classList.contains('is-active')
                    && document.querySelector('[data-ops-detail-tab="geo"]')?.classList.contains('is-active');
                }}""",
                timeout_seconds=60.0,
            )
        else:
            geo_selection_result = {"clicked": False, "runId": backstage_operations_state.get("selectedGeoAssetRunId")}

        geo_baseline_option = pick_first_non_empty_select_option(session_name, "[data-geo-baseline-run-select]")
        if geo_baseline_option.get("value"):
            geo_baseline_result = set_select_value(
                session_name,
                "[data-geo-baseline-run-select]",
                geo_baseline_option["value"],
            )
            wait_for(
                session_name,
                f"""() => {{
                  const params = new URL(window.location.href).searchParams;
                  return (typeof state !== 'undefined' && (state.selectedGeoBaselineRunId || null) === {json.dumps(geo_baseline_option["value"])})
                    && params.get('opsGeoBaseline') === {json.dumps(geo_baseline_option["value"])};
                }}""",
                timeout_seconds=60.0,
            )
        else:
            geo_baseline_result = {
                "changed": False,
                "requestedValue": None,
                "reason": "no-baseline-option",
            }

        operations_run_selection_snapshot = pw.take_snapshot(session_name, args.label, "backstage-operations-selection")
        operations_run_selection_state = browser_state(session_name)
        operations_selection_payload = {
            "runTargets": operations_run_targets,
            "importSelection": import_selection_result,
            "importBaselineOption": import_baseline_option,
            "importBaselineSelection": import_baseline_result,
            "geoSelection": geo_selection_result,
            "geoBaselineOption": geo_baseline_option,
            "geoBaselineSelection": geo_baseline_result,
            "state": operations_run_selection_state,
        }
        artifacts["steps"].append(
            {
                "name": "workspace-backstage-operations-selection",
                "result": {
                    "importRunId": operations_run_selection_state.get("selectedImportRunId"),
                    "importBaselineRunId": operations_run_selection_state.get("selectedBaselineRunId"),
                    "geoRunId": operations_run_selection_state.get("selectedGeoAssetRunId"),
                    "geoBaselineRunId": operations_run_selection_state.get("selectedGeoBaselineRunId"),
                    "opsHistoryTab": operations_run_selection_state.get("activeOperationsHistoryTab"),
                    "opsDetailTab": operations_run_selection_state.get("activeOperationsDetailTab"),
                    "opsQualityTab": operations_run_selection_state.get("activeOperationsQualityTab"),
                },
                "snapshot": str(operations_run_selection_snapshot),
            }
        )
        artifacts["operationsRunSelectionState"] = operations_run_selection_state
        artifacts["operationsRunSelection"] = operations_selection_payload

        operations_selection_backstage_boot_smoke = run_backstage_boot_smoke(
            args.url,
            args.session,
            args.label,
            backstage_tab="operations",
            ops_history_tab=operations_run_selection_state.get("activeOperationsHistoryTab"),
            ops_detail_tab=operations_run_selection_state.get("activeOperationsDetailTab"),
            ops_quality_tab=operations_run_selection_state.get("activeOperationsQualityTab"),
            ops_import_run=operations_run_selection_state.get("selectedImportRunId"),
            ops_import_baseline=operations_run_selection_state.get("selectedBaselineRunId"),
            ops_geo_run=operations_run_selection_state.get("selectedGeoAssetRunId"),
            ops_geo_baseline=operations_run_selection_state.get("selectedGeoBaselineRunId"),
            artifact_slug="backstage-boot-operations-selection",
            headed=args.headed,
        )
        artifacts["steps"].append(
            {
                "name": "backstage-boot-operations-selection-smoke",
                "result": {
                    "importRunId": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("selectedImportRunId"),
                    "importBaselineRunId": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("selectedBaselineRunId"),
                    "geoRunId": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("selectedGeoAssetRunId"),
                    "geoBaselineRunId": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("selectedGeoBaselineRunId"),
                    "opsHistoryTab": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsHistoryTab"),
                    "opsDetailTab": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsDetailTab"),
                    "opsQualityTab": operations_selection_backstage_boot_smoke.get("backstageState", {}).get("activeOperationsQualityTab"),
                },
            }
        )
        artifacts["operationsSelectionBackstageBootSmoke"] = operations_selection_backstage_boot_smoke

        backstage_pipeline_result = set_workspace_view(session_name, "backstage", backstage_tab="pipeline")
        wait_for(
            session_name,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'backstage'
                && params.get('view') === 'backstage'
                && params.get('backstage') === 'pipeline'
                && !params.get('opsHistory')
                && !params.get('opsDetail')
                && !params.get('opsQuality')
                && !params.get('opsImportRun')
                && !params.get('opsImportBaseline')
                && !params.get('opsGeoRun')
                && !params.get('opsGeoBaseline')
                && document.querySelector('#frontstageWorkspace')?.hidden === true
                && document.querySelector('#backstageWorkspace')?.hidden === false
                && document.querySelector('[data-research-backstage-tab="pipeline"]')?.classList.contains('is-active');
            }""",
            timeout_seconds=30.0,
        )
        backstage_pipeline_snapshot = pw.take_snapshot(session_name, args.label, "backstage-pipeline")
        backstage_pipeline_state = browser_state(session_name)
        artifacts["steps"].append(
            {
                "name": "workspace-backstage-pipeline",
                "result": backstage_pipeline_result,
                "snapshot": str(backstage_pipeline_snapshot),
            }
        )
        artifacts["backstagePipelineState"] = backstage_pipeline_state

        backstage_result = set_workspace_view(session_name, "backstage", backstage_tab="schema")
        wait_for(
            session_name,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'backstage'
                && params.get('view') === 'backstage'
                && params.get('backstage') === 'schema'
                && !params.get('opsHistory')
                && !params.get('opsDetail')
                && !params.get('opsQuality')
                && !params.get('opsImportRun')
                && !params.get('opsImportBaseline')
                && !params.get('opsGeoRun')
                && !params.get('opsGeoBaseline')
                && document.querySelector('#frontstageWorkspace')?.hidden === true
                && document.querySelector('#backstageWorkspace')?.hidden === false
                && document.querySelector('[data-research-backstage-tab="schema"]')?.classList.contains('is-active');
            }""",
            timeout_seconds=30.0,
        )
        backstage_snapshot = pw.take_snapshot(session_name, args.label, "backstage-schema")
        backstage_state = browser_state(session_name)
        artifacts["steps"].append(
            {"name": "workspace-backstage-schema", "result": backstage_result, "snapshot": str(backstage_snapshot)}
        )
        artifacts["backstageState"] = backstage_state

        frontstage_restore_result = set_workspace_view(session_name, "frontstage")
        wait_for(
            session_name,
            """() => {
              const params = new URL(window.location.href).searchParams;
              return document.querySelector('#appShell')?.dataset.workspaceView === 'frontstage'
                && !params.get('view')
                && !params.get('backstage')
                && !params.get('opsHistory')
                && !params.get('opsDetail')
                && !params.get('opsQuality')
                && !params.get('opsImportRun')
                && !params.get('opsImportBaseline')
                && !params.get('opsGeoRun')
                && !params.get('opsGeoBaseline')
                && document.querySelector('#frontstageWorkspace')?.hidden === false
                && document.querySelector('#backstageWorkspace')?.hidden === true
                && document.querySelectorAll('#summaryGrid [data-summary-metric]').length >= 6
                && document.querySelectorAll('[data-browser-coverage-community-id]').length > 0;
            }""",
            timeout_seconds=60.0,
        )
        frontstage_restore_snapshot = pw.take_snapshot(session_name, args.label, "frontstage-restored")
        frontstage_restore_state = browser_state(session_name)
        artifacts["steps"].append(
            {
                "name": "workspace-frontstage-restore",
                "result": frontstage_restore_result,
                "snapshot": str(frontstage_restore_snapshot),
            }
        )
        artifacts["frontstageRestoreState"] = frontstage_restore_state

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
        floor_context_reset = None
        try:
            floor_ready = wait_for_floor_layer_ready(session_name)
        except RuntimeError:
            floor_context_reset = reset_floor_watchlist_context(session_name)
            floor_ready = wait_for_floor_layer_ready(session_name)
        floor_snapshot = pw.take_snapshot(session_name, args.label, "floor")
        floor_state = browser_state(session_name)
        artifacts["steps"].append({"name": "floor-mode", "result": floor_result, "snapshot": str(floor_snapshot)})
        artifacts["floorState"] = floor_state
        artifacts["floorReady"] = floor_ready
        artifacts["floorContextReset"] = floor_context_reset

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
