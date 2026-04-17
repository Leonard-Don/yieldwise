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
    output = run_pwcli_with_timeout(session, "eval", script, timeout_seconds=timeout_seconds)
    return pw.extract_playwright_result(output)


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
          const attentionPanel = document.querySelector('[data-browser-capture-attention-panel="true"]');
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
            attentionPanelRunId: attentionPanel?.dataset.browserCaptureAttentionRunId || null,
            attentionPanelAttentionCount: Number(attentionPanel?.dataset.browserCaptureAttentionCount || 0),
            attentionFillCount: document.querySelectorAll('[data-browser-capture-fill-from-attention]').length,
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
            await applyDistrictScope({json.dumps(district_id)});
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
    building = data.get("buildingState") or {}
    floor = data.get("floorState") or {}
    sampling = data.get("samplingState") or {}
    exports = data.get("exports") or []
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
        "workbench_next_review_opens_attention": {
            "passed": next_review_click.get("reason") == "no-review-task"
            or (
                bool(next_review_click.get("clicked"))
                and next_review.get("selectedSamplingTaskId") == next_review_click.get("target")
                and bool(next_review.get("attentionPanelRunId"))
                and (next_review.get("attentionPanelAttentionCount") or 0) > 0
                and (next_review.get("attentionFillCount") or 0) > 0
            ),
            "actual": {
                "clicked": next_review_click.get("clicked"),
                "target": next_review_click.get("target"),
                "reason": next_review_click.get("reason"),
                "selectedSamplingTaskId": next_review.get("selectedSamplingTaskId"),
                "attentionPanelRunId": next_review.get("attentionPanelRunId"),
                "attentionPanelAttentionCount": next_review.get("attentionPanelAttentionCount"),
                "attentionFillCount": next_review.get("attentionFillCount"),
                "samplingTaskLabel": next_review.get("samplingTaskLabel"),
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

        district_coverage_click_result = click_via_dom(
            session_name,
            """(() => {
              const currentTaskId = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || '';
              const currentDistrict = document.querySelector('#districtFilter')?.value || 'all';
              const cards = [...document.querySelectorAll('[data-browser-coverage-district]')];
              const card = cards.find((item) => {
                const district = item.dataset.browserCoverageDistrict || '';
                const taskId = item.dataset.browserCoverageTaskId || '';
                return district && district !== currentDistrict && taskId && taskId !== currentTaskId;
              }) || cards[0];
              if (!card) return { clicked: false };
              const district = card.dataset.browserCoverageDistrict || null;
              const taskId = card.dataset.browserCoverageTaskId || null;
              const label = card.querySelector('strong')?.textContent?.trim() || null;
              card.dispatchEvent(new MouseEvent('click', { bubbles: true }));
              return { clicked: true, district, taskId, label };
            })()""",
        )
        if district_coverage_click_result.get("district"):
            wait_for(
                session_name,
                f"""() => document.querySelector('#districtFilter')?.value === {json.dumps(district_coverage_click_result["district"])}""",
            )
        if district_coverage_click_result.get("taskId"):
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(district_coverage_click_result["taskId"])}""",
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

        coverage_click_result = click_via_dom(
            session_name,
            """(() => {
              const currentTaskId = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || '';
              const cards = [...document.querySelectorAll('[data-browser-coverage-community-id]')];
              const card = cards.find((item) => {
                const taskId = item.dataset.browserCoverageTaskId || '';
                return taskId && taskId !== currentTaskId;
              }) || cards[0];
              if (!card) return { clicked: false };
              const label = card.querySelector('strong')?.textContent?.trim() || null;
              const taskId = card.dataset.browserCoverageTaskId || null;
              card.dispatchEvent(new MouseEvent('click', { bubbles: true }));
              return { clicked: true, label, taskId };
            })()""",
        )
        if coverage_click_result.get("taskId"):
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(coverage_click_result["taskId"])}""",
            )
        coverage_snapshot = pw.take_snapshot(session_name, args.label, "coverage-click")
        coverage_state = browser_state(session_name)
        artifacts["coverageClickResult"] = coverage_click_result
        artifacts["steps"].append({"name": "coverage-card", "result": coverage_click_result, "snapshot": str(coverage_snapshot)})
        artifacts["coverageState"] = coverage_state

        next_capture_click_result = click_via_dom(
            session_name,
            """(() => {
              const button =
                document.querySelector('[data-browser-workbench-next-capture]:not([disabled])') ||
                document.querySelector('[data-browser-workbench-next-district]:not([disabled])');
              if (!button) return { clicked: false };
              const before = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
              const target = button.dataset.browserWorkbenchNextCapture || button.dataset.browserWorkbenchNextDistrict || null;
              const text = button.textContent?.trim() || null;
              button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
              return { clicked: true, before, target, text };
            })()""",
        )
        if next_capture_click_result.get("target"):
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(next_capture_click_result["target"])}""",
            )
        next_capture_snapshot = pw.take_snapshot(session_name, args.label, "next-capture")
        next_capture_state = browser_state(session_name)
        artifacts["nextCaptureClickResult"] = next_capture_click_result
        artifacts["steps"].append({"name": "next-capture", "result": next_capture_click_result, "snapshot": str(next_capture_snapshot)})
        artifacts["nextCaptureState"] = next_capture_state

        next_review_click_result = eval_json_with_timeout(
            session_name,
            """async () => {
              const before = document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId || null;
              const button = document.querySelector('[data-browser-workbench-next-review]:not([disabled])');
              if (button) {
                const target = button.dataset.browserWorkbenchNextReview || null;
                const text = button.textContent?.trim() || null;
                button.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                return { clicked: true, before, target, text, via: 'button' };
              }

              const currentDistrict = typeof state !== 'undefined' ? state.districtFilter : 'all';
              const tasks = Array.isArray(state?.browserSamplingPackItems) ? state.browserSamplingPackItems : [];
              let targetTask =
                tasks.find((item) =>
                  item?.taskId !== before &&
                  Number(item?.latestCaptureAttentionCount ?? 0) > 0 &&
                  (currentDistrict === 'all' || item?.districtId === currentDistrict)
                ) ||
                tasks.find((item) => item?.taskId !== before && Number(item?.latestCaptureAttentionCount ?? 0) > 0);
              if (!targetTask) {
                return { clicked: false, before, reason: 'no-review-task' };
              }
              if (typeof applyDistrictScope === 'function' && targetTask.districtId && targetTask.districtId !== currentDistrict) {
                await applyDistrictScope(targetTask.districtId);
              }
              if (typeof navigateToBrowserSamplingTask === 'function') {
                await navigateToBrowserSamplingTask(targetTask, {
                  resetDraft: false,
                  revealLatestCaptureRun: true,
                });
                try {
                  render();
                } catch (error) {
                  // Keep the helper resilient if render is temporarily unavailable.
                }
              } else {
                const reviewButton = document.querySelector('[data-browser-workbench-next-review]:not([disabled])');
                if (!reviewButton) {
                  return { clicked: false, before, reason: 'missing-helper-and-button' };
                }
                reviewButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
              }
              return {
                clicked: true,
                before,
                target: targetTask.taskId || null,
                text: targetTask.communityName || targetTask.taskId || null,
                via: 'fallback-task',
              };
            }""",
            timeout_seconds=60.0,
        )
        if next_review_click_result.get("target"):
            wait_for(
                session_name,
                f"""() => document.querySelector('[data-browser-capture-panel]')?.dataset.browserCaptureTaskId === {json.dumps(next_review_click_result["target"])}""",
            )
            wait_for(
                session_name,
                """() => {
                  const panel = document.querySelector('[data-browser-capture-attention-panel="true"]');
                  const runId = panel?.dataset.browserCaptureAttentionRunId || '';
                  const attentionCount = Number(panel?.dataset.browserCaptureAttentionCount || 0);
                  return runId && attentionCount > 0 ? { runId, attentionCount } : null;
                }""",
                timeout_seconds=20.0,
            )
        next_review_state = browser_state(session_name)
        artifacts["nextReviewClickResult"] = next_review_click_result
        artifacts["steps"].append({"name": "next-review", "result": next_review_click_result})
        artifacts["nextReviewState"] = next_review_state

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

        console_errors = pw.run_pwcli(session_name, "console", "error")
        console_path = OUTPUT_DIR / f"{args.label}-console.txt"
        console_path.write_text(console_errors, encoding="utf-8")
        artifacts["consoleLog"] = str(console_path)
        artifacts["assertions"] = build_assertions(artifacts)

        summary_path = OUTPUT_DIR / f"{args.label}.json"
        write_json(summary_path, artifacts)
        print(str(summary_path))
        return 0
    finally:
        if opened_new_session and not args.keep_session_open:
            pw.close_session_quietly(session_name)


if __name__ == "__main__":
    raise SystemExit(main())
