from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jobs.import_reference_dictionary import COMMUNITY_REQUIRED_FIELDS, DISTRICT_REQUIRED_FIELDS, load_csv_rows, split_aliases


AMAP_WEB_SERVICE_ENV = "AMAP_WEB_SERVICE_KEY"
GEOCODE_ENDPOINT = "https://restapi.amap.com/v3/geocode/geo"
PLACE_ENDPOINT = "https://restapi.amap.com/v3/place/text"
PREFERRED_LEVEL_SCORES = {
    "住宅区": 0.93,
    "商务住宅": 0.9,
    "楼栋": 0.88,
    "门牌号": 0.84,
    "兴趣点": 0.8,
    "村庄": 0.72,
}
REJECT_LEVELS = {"区县", "城市", "省", "热点商圈"}
PREFERRED_PLACE_TYPE_SCORES = {
    "住宅小区": 0.92,
    "住宅区": 0.9,
    "商务住宅": 0.88,
    "楼栋": 0.84,
}
REJECT_PLACE_NAME_TOKENS = {"停车场", "出入口", "资产管理中心", "地上停车场"}
COMMON_SUFFIXES = ("园", "花园", "家园", "苑", "公寓", "小区")


def fetch_geocode(key: str, address: str, city: str = "上海") -> dict[str, Any] | None:
    query = urlencode({"key": key, "address": address, "city": city})
    url = f"{GEOCODE_ENDPOINT}?{query}"
    with urlopen(url, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or str(payload.get("status")) != "1":
        return None
    geocodes = payload.get("geocodes")
    if not isinstance(geocodes, list) or not geocodes:
        return None
    first = geocodes[0]
    location = str(first.get("location") or "")
    if "," not in location:
        return None
    lng_text, lat_text = location.split(",", 1)
    try:
        center_lng = float(lng_text)
        center_lat = float(lat_text)
    except ValueError:
        return None
    return {
        "center_lng": center_lng,
        "center_lat": center_lat,
        "formatted_address": first.get("formatted_address"),
        "level": first.get("level"),
        "match_source": "amap_geocode",
    }


def fetch_place_candidates(key: str, keywords: str, city: str = "上海") -> list[dict[str, Any]]:
    query = urlencode({"key": key, "keywords": keywords, "city": city, "citylimit": "true", "offset": 8, "page": 1})
    url = f"{PLACE_ENDPOINT}?{query}"
    with urlopen(url, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict) or str(payload.get("status")) != "1":
        return []
    pois = payload.get("pois")
    if not isinstance(pois, list):
        return []
    candidates: list[dict[str, Any]] = []
    for poi in pois:
        location = str(poi.get("location") or "")
        if "," not in location:
            continue
        lng_text, lat_text = location.split(",", 1)
        try:
            center_lng = float(lng_text)
            center_lat = float(lat_text)
        except ValueError:
            continue
        candidates.append(
            {
                "center_lng": center_lng,
                "center_lat": center_lat,
                "formatted_address": f"{poi.get('name') or ''} {poi.get('address') or ''}".strip(),
                "level": poi.get("type"),
                "poi_name": poi.get("name"),
                "adname": poi.get("adname"),
                "type": poi.get("type"),
                "match_source": "amap_place",
            }
        )
    return candidates


def build_search_terms(primary_name: str, aliases: list[str]) -> list[str]:
    terms: list[str] = []
    for term in [primary_name, *aliases]:
        cleaned = (term or "").strip()
        if cleaned and cleaned not in terms:
            terms.append(cleaned)
        if cleaned and not cleaned.endswith(COMMON_SUFFIXES):
            for suffix in COMMON_SUFFIXES:
                candidate = f"{cleaned}{suffix}"
                if candidate not in terms:
                    terms.append(candidate)
    return terms


def evaluate_geocode_candidate(
    candidate_query: str,
    district_name: str,
    community_name: str,
    aliases: list[str],
    geocode_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not geocode_result:
        return None
    level = str(geocode_result.get("level") or "")
    if level in REJECT_LEVELS:
        return None
    formatted_address = str(geocode_result.get("formatted_address") or "")
    score = PREFERRED_LEVEL_SCORES.get(level, 0.68)
    community_tokens = [community_name, *aliases]
    has_name_match = any(token and token in formatted_address for token in community_tokens)
    has_district_match = bool(district_name and district_name in formatted_address)
    if not has_name_match and not has_district_match:
        return None
    if has_name_match:
        score += 0.05
    elif not has_district_match:
        score -= 0.08
    if "小区" in candidate_query:
        score += 0.02
    score = round(min(score, 0.99), 2)
    return {
        **geocode_result,
        "query": candidate_query,
        "score": score,
    }


def _text_matches_tokens(text: str, tokens: list[str]) -> bool:
    for token in tokens:
        if not token:
            continue
        if token in text or text in token:
            return True
    return False


def evaluate_place_candidate(
    candidate_query: str,
    district_name: str,
    community_name: str,
    aliases: list[str],
    place_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not place_result:
        return None
    poi_name = str(place_result.get("poi_name") or "")
    if any(token in poi_name for token in REJECT_PLACE_NAME_TOKENS):
        return None
    place_type = str(place_result.get("type") or "")
    residential_hint = next((label for label in PREFERRED_PLACE_TYPE_SCORES if label in place_type), None)
    if residential_hint is None:
        return None
    community_tokens = [community_name, *aliases]
    address_blob = " ".join(
        filter(
            None,
            [
                poi_name,
                str(place_result.get("formatted_address") or ""),
                str(place_result.get("adname") or ""),
            ],
        )
    )
    has_name_match = _text_matches_tokens(address_blob, community_tokens)
    has_district_match = bool(district_name and district_name in address_blob)
    if not has_name_match:
        return None
    score = PREFERRED_PLACE_TYPE_SCORES[residential_hint]
    if has_name_match:
        score += 0.05
    if has_district_match:
        score += 0.02
    if any(token in poi_name for token in community_tokens if token):
        score += 0.02
    if "小区" in candidate_query:
        score += 0.01
    score = round(min(score, 0.99), 2)
    return {
        **place_result,
        "query": candidate_query,
        "score": score,
    }


def suggest_place_candidate(
    candidate_query: str,
    district_name: str,
    place_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not place_result:
        return None
    poi_name = str(place_result.get("poi_name") or "")
    if any(token in poi_name for token in REJECT_PLACE_NAME_TOKENS):
        return None
    place_type = str(place_result.get("type") or "")
    residential_hint = next((label for label in PREFERRED_PLACE_TYPE_SCORES if label in place_type), None)
    if residential_hint is None:
        return None
    address_blob = " ".join(
        filter(
            None,
            [
                poi_name,
                str(place_result.get("formatted_address") or ""),
                str(place_result.get("adname") or ""),
            ],
        )
    )
    has_district_match = bool(district_name and district_name in address_blob)
    if not has_district_match:
        return None
    score = round(min(PREFERRED_PLACE_TYPE_SCORES[residential_hint] - 0.08, 0.9), 2)
    return {
        **place_result,
        "query": candidate_query,
        "score": score,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich community dictionary CSV with AMap geocoded anchors.")
    parser.add_argument("--community-file", required=True, type=Path)
    parser.add_argument("--district-file", required=True, type=Path)
    parser.add_argument("--output-file", required=True, type=Path)
    parser.add_argument("--report-file", required=True, type=Path)
    parser.add_argument("--pause-ms", type=int, default=120)
    parser.add_argument("--web-service-key", default=os.getenv(AMAP_WEB_SERVICE_ENV, "").strip())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.web_service_key:
        raise SystemExit(f"缺少高德 Web 服务 key。请传 --web-service-key 或配置 {AMAP_WEB_SERVICE_ENV}。")

    district_rows = load_csv_rows(args.district_file, DISTRICT_REQUIRED_FIELDS)
    district_name_index = {row["district_id"]: row["district_name"] for row in district_rows}
    community_rows = load_csv_rows(args.community_file, COMMUNITY_REQUIRED_FIELDS)

    enriched_rows: list[dict[str, Any]] = []
    report_rows: list[dict[str, Any]] = []
    success_count = 0

    for row in community_rows:
        district_name = district_name_index.get(row["district_id"], row["district_id"])
        aliases = split_aliases(row.get("aliases"))[:6]
        search_terms = build_search_terms(row["community_name"], aliases)
        query_candidates = []
        for search_term in search_terms:
            for candidate in (
                f"上海市{district_name}{search_term}",
                f"上海市{district_name}{search_term}小区",
                f"上海市{search_term}",
                f"上海市{search_term}小区",
            ):
                if candidate not in query_candidates:
                    query_candidates.append(candidate)

        best_candidate = None
        backup_candidates: list[dict[str, Any]] = []
        for candidate in query_candidates:
            geocode_result = fetch_geocode(args.web_service_key, candidate)
            evaluated = evaluate_geocode_candidate(candidate, district_name, row["community_name"], aliases, geocode_result)
            if evaluated and (best_candidate is None or evaluated["score"] > best_candidate["score"]):
                best_candidate = evaluated
            time.sleep(max(args.pause_ms, 0) / 1000)
            for place_result in fetch_place_candidates(args.web_service_key, candidate):
                suggested_place = suggest_place_candidate(candidate, district_name, place_result)
                if suggested_place:
                    backup_candidates.append(suggested_place)
                evaluated_place = evaluate_place_candidate(candidate, district_name, row["community_name"], aliases, place_result)
                if evaluated_place:
                    if best_candidate is None or evaluated_place["score"] > best_candidate["score"]:
                        best_candidate = evaluated_place
            time.sleep(max(args.pause_ms, 0) / 1000)

        enriched = dict(row)
        if best_candidate:
            success_count += 1
            enriched["center_lng"] = best_candidate["center_lng"]
            enriched["center_lat"] = best_candidate["center_lat"]
            enriched["anchor_source"] = best_candidate.get("match_source") or "amap_geocode"
            enriched["anchor_quality"] = best_candidate["score"]
            enriched["source_refs"] = best_candidate["query"] or ""
        else:
            enriched["center_lng"] = ""
            enriched["center_lat"] = ""
            enriched["anchor_source"] = ""
            enriched["anchor_quality"] = ""
            enriched["source_refs"] = ""
        enriched_rows.append(enriched)
        report_rows.append(
            {
                "community_id": row["community_id"],
                "community_name": row["community_name"],
                "district_id": row["district_id"],
                "district_name": district_name,
                "matched": bool(best_candidate),
                "query": best_candidate.get("query") if best_candidate else None,
                "formatted_address": best_candidate.get("formatted_address") if best_candidate else None,
                "level": best_candidate.get("level") if best_candidate else None,
                "center_lng": best_candidate.get("center_lng") if best_candidate else None,
                "center_lat": best_candidate.get("center_lat") if best_candidate else None,
                "anchor_quality": best_candidate.get("score") if best_candidate else None,
                "match_source": best_candidate.get("match_source") if best_candidate else None,
                "poi_name": best_candidate.get("poi_name") if best_candidate else None,
                "candidate_suggestions": [
                    {
                        "query": candidate.get("query"),
                        "name": candidate.get("poi_name"),
                        "address": candidate.get("formatted_address"),
                        "score": candidate.get("score"),
                        "match_source": candidate.get("match_source"),
                    }
                    for candidate in sorted(backup_candidates, key=lambda item: item.get("score", 0), reverse=True)[:3]
                ],
            }
        )
        time.sleep(max(args.pause_ms, 0) / 1000)

    fieldnames = list(community_rows[0].keys()) if community_rows else list(COMMUNITY_REQUIRED_FIELDS)
    for field in ["center_lng", "center_lat", "anchor_source", "anchor_quality", "source_refs"]:
        if field not in fieldnames:
            fieldnames.append(field)

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with args.output_file.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in enriched_rows:
            writer.writerow(row)

    report = {
        "community_count": len(community_rows),
        "anchored_count": success_count,
        "anchored_pct": round(success_count / max(len(community_rows), 1) * 100, 1) if community_rows else 0.0,
        "items": report_rows,
    }
    args.report_file.parent.mkdir(parents=True, exist_ok=True)
    args.report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
