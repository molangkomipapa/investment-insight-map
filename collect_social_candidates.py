import argparse
import csv
import math
import os
import re
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

import requests


NAVER_API_BASE = "https://openapi.naver.com/v1/search"
KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
TOUR_API_KEYWORD_URL = "https://apis.data.go.kr/B551011/KorService2/searchKeyword2"
OUTPUT_FILE = Path("data/social_candidates.csv")
STREAMLIT_SECRETS_FILE = Path(".streamlit/secrets.toml")

CATEGORY_QUERIES = {
    "foods": ["맛집", "현지인 맛집", "시장 먹거리", "웨이팅 적은 맛집"],
    "affordable_stays": ["저렴한 숙소", "가성비 숙소", "비즈니스호텔", "게스트하우스"],
    "camping": ["캠핑장", "오토캠핑장", "카라반", "야영장"],
    "places": ["가볼만한곳", "명소", "즐길거리", "산책 코스"],
    "desserts": ["카페", "빵집", "디저트", "베이커리"],
}

TOUR_CONTENT_TYPES = {
    "foods": "39",
    "affordable_stays": "32",
    "camping": "28",
    "places": "12",
    "desserts": "39",
}


def clean_html(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def load_secrets():
    if not STREAMLIT_SECRETS_FILE.exists():
        return {}

    with STREAMLIT_SECRETS_FILE.open("rb") as file:
        return tomllib.load(file)


def get_secret(name):
    return os.getenv(name) or load_secrets().get(name)


def normalize_name(text):
    return re.sub(r"[^0-9a-zA-Z가-힣]", "", text or "").lower()


def naver_headers():
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if (not client_id or not client_secret) and STREAMLIT_SECRETS_FILE.exists():
        secrets = load_secrets()
        client_id = client_id or secrets.get("NAVER_CLIENT_ID")
        client_secret = client_secret or secrets.get("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are required in environment variables "
            "or .streamlit/secrets.toml."
        )

    return {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }


def kakao_headers():
    api_key = get_secret("KAKAO_REST_API_KEY")
    if not api_key:
        return None

    return {"Authorization": f"KakaoAK {api_key}"}


def tour_api_service_key():
    return get_secret("TOUR_API_SERVICE_KEY")


def tour_api_service_keys():
    service_key = tour_api_service_key()
    if not service_key:
        return []

    keys = [service_key]
    decoded_key = unquote(service_key)
    if decoded_key != service_key:
        keys.append(decoded_key)

    return keys


def naver_search(endpoint, query, display=10, sort="sim"):
    response = requests.get(
        f"{NAVER_API_BASE}/{endpoint}.json",
        headers=naver_headers(),
        params={
            "query": query,
            "display": display,
            "sort": sort,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def count_mentions(endpoint, query):
    try:
        data = naver_search(endpoint, query, display=10, sort="sim")
        return int(data.get("total", 0))
    except Exception:
        return 0


def naver_local_candidates(region, category, limit_per_query=10):
    seen = set()
    results = []

    for keyword in CATEGORY_QUERIES[category]:
        query = f"{region} {keyword}"

        try:
            data = naver_search("local", query, display=limit_per_query, sort="comment")
        except Exception:
            continue

        for item in data.get("items", []):
            name = clean_html(item.get("title"))
            if not name or name in seen:
                continue

            seen.add(name)
            address = item.get("roadAddress") or item.get("address") or ""
            results.append({
                "name": name,
                "query": f"{region} {name}",
                "address": clean_html(address),
                "category_hint": clean_html(item.get("category", "")),
                "source_url": item.get("link", ""),
                "source": "naver_local",
            })

    return results


def kakao_local_candidates(region, category, limit_per_query=10):
    headers = kakao_headers()
    if not headers:
        return []

    seen = set()
    results = []

    for keyword in CATEGORY_QUERIES[category]:
        query = f"{region} {keyword}"

        try:
            response = requests.get(
                KAKAO_LOCAL_URL,
                headers=headers,
                params={"query": query, "size": limit_per_query, "sort": "accuracy"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            continue

        for item in data.get("documents", []):
            name = clean_html(item.get("place_name"))
            if not name or name in seen:
                continue

            seen.add(name)
            address = item.get("road_address_name") or item.get("address_name") or ""
            results.append({
                "name": name,
                "query": f"{region} {name}",
                "address": clean_html(address),
                "category_hint": clean_html(item.get("category_name", "")),
                "source_url": item.get("place_url", ""),
                "source": "kakao_local",
            })

    return results


def tour_api_candidates(region, category, limit_per_query=10):
    service_keys = tour_api_service_keys()
    if not service_keys:
        return []

    seen = set()
    results = []
    content_type_id = TOUR_CONTENT_TYPES[category]

    for keyword in CATEGORY_QUERIES[category]:
        query = f"{region} {keyword}"

        data = None
        for service_key in service_keys:
            try:
                response = requests.get(
                    TOUR_API_KEYWORD_URL,
                    params={
                        "serviceKey": service_key,
                        "MobileOS": "ETC",
                        "MobileApp": "TravelRegionSearch",
                        "_type": "json",
                        "keyword": query,
                        "contentTypeId": content_type_id,
                        "numOfRows": limit_per_query,
                        "pageNo": 1,
                        "arrange": "Q",
                    },
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                break
            except Exception:
                data = None

        if data is None:
            continue

        response_body = data.get("response", {}).get("body", {})
        items_container = response_body.get("items", {})
        if not isinstance(items_container, dict):
            continue

        items = items_container.get("item", [])
        if isinstance(items, dict):
            items = [items]
        elif not isinstance(items, list):
            continue

        for item in items:
            name = clean_html(item.get("title"))
            if not name or name in seen:
                continue

            seen.add(name)
            results.append({
                "name": name,
                "query": f"{region} {name}",
                "address": clean_html(item.get("addr1", "")),
                "category_hint": content_type_id,
                "source_url": "",
                "source": "tour_api",
            })

    return results


def merge_candidates(*candidate_groups):
    merged = {}

    for candidates in candidate_groups:
        for candidate in candidates:
            key = normalize_name(candidate["name"])
            if not key:
                continue

            current = merged.setdefault(key, {
                **candidate,
                "sources": set(),
                "source_urls": [],
                "kakao_match": False,
                "tourapi_match": False,
            })
            current["sources"].add(candidate["source"])
            if candidate.get("source_url"):
                current["source_urls"].append(candidate["source_url"])
            if not current.get("address") and candidate.get("address"):
                current["address"] = candidate["address"]
            if not current.get("category_hint") and candidate.get("category_hint"):
                current["category_hint"] = candidate["category_hint"]
            if candidate["source"] == "kakao_local":
                current["kakao_match"] = True
            if candidate["source"] == "tour_api":
                current["tourapi_match"] = True

    results = []
    for candidate in merged.values():
        source_names = sorted(candidate["sources"])
        candidate["source"] = "+".join(source_names)
        candidate["source_count"] = len(source_names)
        candidate["source_url"] = candidate["source_urls"][0] if candidate["source_urls"] else ""
        results.append(candidate)

    return results


def local_candidates(region, category):
    candidate_groups = []

    for provider in (
        naver_local_candidates,
        kakao_local_candidates,
        tour_api_candidates,
    ):
        try:
            candidate_groups.append(provider(region, category))
        except Exception:
            candidate_groups.append([])

    return merge_candidates(*candidate_groups)


def score_candidate(
    blog_mentions,
    cafe_mentions,
    instagram_mentions=0,
    facebook_mentions=0,
    source_count=1,
    kakao_match=False,
    tourapi_match=False,
):
    # Log scaling keeps a huge platform from drowning out smaller but meaningful signals.
    score = (
        math.log1p(blog_mentions) * 24
        + math.log1p(cafe_mentions) * 26
        + math.log1p(instagram_mentions) * 22
        + math.log1p(facebook_mentions) * 12
        + max(0, source_count - 1) * 8
        + (5 if kakao_match else 0)
        + (5 if tourapi_match else 0)
    )
    return min(100, round(score))


def build_rows(regions):
    rows = []
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for region in regions:
        for category in CATEGORY_QUERIES:
            print(f"Collecting {region} / {category}...")
            for candidate in local_candidates(region, category):
                query = candidate["query"]
                blog_mentions = count_mentions("blog", query)
                cafe_mentions = count_mentions("cafearticle", query)

                rows.append({
                    "region": region,
                    "category": category,
                    "name": candidate["name"],
                    "query": query,
                    "score": score_candidate(
                        blog_mentions,
                        cafe_mentions,
                        source_count=candidate.get("source_count", 1),
                        kakao_match=candidate.get("kakao_match", False),
                        tourapi_match=candidate.get("tourapi_match", False),
                    ),
                    "blog_mentions": blog_mentions,
                    "instagram_mentions": 0,
                    "cafe_mentions": cafe_mentions,
                    "facebook_mentions": 0,
                    "source_count": candidate.get("source_count", 1),
                    "kakao_match": candidate.get("kakao_match", False),
                    "tourapi_match": candidate.get("tourapi_match", False),
                    "address": candidate["address"],
                    "category_hint": candidate["category_hint"],
                    "source": candidate["source"],
                    "source_url": candidate["source_url"],
                    "collected_at": collected_at,
                })

    rows.sort(key=lambda row: (row["region"], row["category"], -row["score"]))
    return rows


def write_rows(rows, output_file):
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "region", "category", "name", "query", "score",
        "blog_mentions", "instagram_mentions", "cafe_mentions", "facebook_mentions",
        "source_count", "kakao_match", "tourapi_match",
        "address", "category_hint", "source", "source_url", "collected_at",
    ]

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def check_apis():
    print("Naver:", "configured" if naver_headers() else "missing")

    headers = kakao_headers()
    print("Kakao:", "configured" if headers else "missing")
    if headers:
        try:
            response = requests.get(
                KAKAO_LOCAL_URL,
                headers=headers,
                params={"query": "강릉 맛집", "size": 1},
                timeout=10,
            )
            print("Kakao status:", response.status_code)
            if response.status_code != 200:
                print("Kakao message:", response.text[:200])
        except Exception as error:
            print("Kakao error:", error)

    keys = tour_api_service_keys()
    print("TourAPI:", "configured" if keys else "missing")
    if keys:
        ok = False
        last_status = None
        last_text = ""
        for key in keys:
            try:
                response = requests.get(
                    TOUR_API_KEYWORD_URL,
                    params={
                        "serviceKey": key,
                        "MobileOS": "ETC",
                        "MobileApp": "TravelRegionSearch",
                        "_type": "json",
                        "keyword": "강릉",
                        "contentTypeId": "12",
                        "numOfRows": 1,
                        "pageNo": 1,
                    },
                    timeout=10,
                )
                last_status = response.status_code
                last_text = response.text[:200]
                if response.status_code == 200:
                    ok = True
                    break
            except Exception as error:
                last_text = str(error)

        print("TourAPI status:", 200 if ok else last_status)
        if not ok:
            print("TourAPI message:", last_text)


def main():
    parser = argparse.ArgumentParser(description="Collect travel candidate signals.")
    parser.add_argument(
        "--regions",
        nargs="+",
        required=False,
        help="Region names to collect, for example: 강릉 속초 부산 제주",
    )
    parser.add_argument("--output", default=str(OUTPUT_FILE))
    parser.add_argument("--check-apis", action="store_true")
    args = parser.parse_args()

    if args.check_apis:
        check_apis()
        return

    if not args.regions:
        parser.error("--regions is required unless --check-apis is used.")

    rows = build_rows(args.regions)
    write_rows(rows, Path(args.output))
    print(f"Wrote {len(rows)} candidates to {args.output}")


if __name__ == "__main__":
    main()
