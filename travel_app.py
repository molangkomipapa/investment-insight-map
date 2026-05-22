from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st

try:
    from collect_social_candidates import (
        count_mentions,
        local_candidates,
        score_candidate,
    )
except ImportError:
    count_mentions = None
    local_candidates = None
    score_candidate = None


KST = timezone(timedelta(hours=9))
SOCIAL_CANDIDATES_FILE = Path("data/social_candidates.csv")
CATEGORY_LABELS = {
    "foods": "먹을 곳",
    "affordable_stays": "저렴한 숙소",
    "camping": "캠핑장",
    "places": "갈 곳·즐길거리",
    "desserts": "디저트·카페",
}
CATEGORY_CAPTIONS = {
    "foods": "식사는 현지 음식, 시장, 리뷰 반복 노출을 우선으로 봅니다.",
    "affordable_stays": "가격, 청결, 위치, 주차 언급이 같이 잡히는 숙소 후보를 먼저 보여줍니다.",
    "camping": "캠핑장은 화장실, 샤워실, 사이트 간격, 예약 후기를 별도로 봅니다.",
    "places": "명소, 산책, 체험, 사진 포인트를 섞어서 먼저 추려줍니다.",
    "desserts": "식사와 분리해서 빵집, 카페, 디저트 언급이 많은 후보를 보여줍니다.",
}


REGION_GUIDES = {
    "동해": {
        "title": "동해",
        "subtitle": "바다, 묵호, 논골담길, 해산물, 조용한 감성 숙소",
        "hero": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
        "tags": ["바다", "강원", "드라이브", "해산물", "감성 산책"],
        "foods": ["곰치국", "물회", "장칼국수", "생선구이", "오징어순대"],
        "affordable_stays": ["동해역 근처 모텔", "묵호항 근처 게스트하우스", "천곡동 비즈니스호텔", "망상해변 펜션"],
        "camping": ["망상오토캠핑리조트", "추암오토캠핑장", "무릉계곡 힐링캠프장"],
        "places": ["묵호등대", "논골담길", "추암촛대바위", "무릉계곡", "도째비골 스카이밸리"],
        "desserts": ["묵호항 카페", "논골담길 디저트 카페", "망상해변 오션뷰 카페", "동해 빵집"],
    },
    "강릉": {
        "title": "강릉",
        "subtitle": "커피, 바다, 초당순두부, KTX 주말 여행",
        "hero": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
        "tags": ["바다", "카페", "맛집", "주말", "강원"],
        "foods": ["초당순두부", "장칼국수", "물회", "오징어순대", "감자옹심이"],
        "affordable_stays": ["강릉역 근처 비즈니스호텔", "교동 게스트하우스", "경포대 가성비 펜션", "안목해변 모텔"],
        "camping": ["연곡해변 솔향기캠핑장", "강릉 오토캠핑장", "주문진 캠핑장"],
        "places": ["경포해변", "오죽헌", "안목해변", "아르떼뮤지엄 강릉", "주문진 방파제"],
        "desserts": ["안목 커피거리", "초당 디저트 카페", "사천 오션뷰 카페", "강릉 빵집"],
    },
    "속초": {
        "title": "속초",
        "subtitle": "설악산, 시장 먹거리, 바다, 짧고 꽉 찬 여행",
        "hero": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1600&q=80",
        "tags": ["바다", "산", "시장", "먹방", "강원"],
        "foods": ["닭강정", "아바이순대", "물회", "홍게", "섭국"],
        "affordable_stays": ["속초 중앙시장 근처 숙소", "청초호 비즈니스호텔", "조양동 모텔", "대포항 펜션"],
        "camping": ["설악동 야영장", "속초 국민여가캠핑장", "고성 송지호 캠핑장"],
        "places": ["설악산", "영금정", "청초호", "속초아이", "아바이마을"],
        "desserts": ["속초 중앙시장 디저트", "청초호 카페", "영랑호 카페", "속초 빵집"],
    },
    "부산": {
        "title": "부산",
        "subtitle": "광안리 야경, 돼지국밥, 시장, 바다 도시",
        "hero": "https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=1600&q=80",
        "tags": ["바다", "도시", "야경", "맛집", "친구"],
        "foods": ["돼지국밥", "밀면", "회", "어묵", "씨앗호떡"],
        "affordable_stays": ["서면 비즈니스호텔", "광안리 가성비 호텔", "부산역 근처 숙소", "해운대 게스트하우스"],
        "camping": ["송정 캠핑장", "대저 캠핑장", "기장 오토캠핑장"],
        "places": ["광안리해수욕장", "흰여울문화마을", "동백섬", "감천문화마을", "태종대"],
        "desserts": ["전포 카페거리", "해리단길 카페", "영도 오션뷰 카페", "부산 빵집"],
    },
    "제주": {
        "title": "제주",
        "subtitle": "오름, 해변, 숲길, 카페, 긴 호흡의 여행",
        "hero": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
        "tags": ["섬", "자연", "드라이브", "카페", "힐링"],
        "foods": ["고기국수", "흑돼지", "갈치조림", "해산물", "몸국"],
        "affordable_stays": ["제주시 가성비 호텔", "서귀포 게스트하우스", "애월 펜션", "성산 저렴한 숙소"],
        "camping": ["김녕해수욕장 야영장", "모구리야영장", "서귀포 자연휴양림 야영장"],
        "places": ["성산일출봉", "사려니숲길", "새별오름", "협재해변", "비자림"],
        "desserts": ["구좌 카페", "애월 오션뷰 카페", "서귀포 디저트", "제주 베이커리"],
    },
    "가평": {
        "title": "가평",
        "subtitle": "계곡, 캠핑, 펜션, 서울 근교 물놀이",
        "hero": "https://images.unsplash.com/photo-1433086966358-54859d0ed716?auto=format&fit=crop&w=1600&q=80",
        "tags": ["계곡", "캠핑", "서울근교", "물놀이", "펜션"],
        "foods": ["닭갈비", "막국수", "잣두부", "송어회", "백숙"],
        "affordable_stays": ["가평역 근처 펜션", "청평 가성비 숙소", "북면 펜션", "남이섬 근처 모텔"],
        "camping": ["자라섬 캠핑장", "가평 계곡 캠핑장", "청평 캠핑장"],
        "places": ["남이섬", "아침고요수목원", "자라섬", "용추계곡", "청평호"],
        "desserts": ["청평 카페", "가평 베이커리", "북한강 뷰 카페", "남이섬 근처 카페"],
    },
}


SITUATION_GUIDES = {
    "계곡": {
        "summary": "계곡은 수도권 근교, 강원 산간, 충청·전라·경상권까지 선택지가 넓어요. 거리, 물놀이 난이도, 캠핑 가능 여부로 좁히면 좋습니다.",
        "regions": ["가평", "포천", "양평", "홍천", "인제", "양양", "괴산", "제천", "무주", "지리산", "청도", "밀양"],
        "spots": [
            {"name": "용추계곡", "region": "가평", "location": "경기 가평군 가평읍", "note": "수도권 근교 물놀이와 펜션 여행에 좋아요."},
            {"name": "백운계곡", "region": "포천", "location": "경기 포천시 이동면", "note": "물놀이, 백숙, 당일치기 조합이 편해요."},
            {"name": "중원계곡", "region": "양평", "location": "경기 양평군 용문면", "note": "서울 근교 숲길과 계곡 산책을 같이 보기 좋아요."},
            {"name": "수타사계곡", "region": "홍천", "location": "강원 홍천군 영귀미면", "note": "숲길, 계곡, 사찰 산책을 묶기 좋아요."},
            {"name": "아침가리계곡", "region": "인제", "location": "강원 인제군 기린면", "note": "트레킹 성격이 강해서 준비가 필요한 계곡이에요."},
            {"name": "미천골계곡", "region": "양양", "location": "강원 양양군 서면", "note": "자연휴양림, 숲, 조용한 물놀이에 어울려요."},
            {"name": "쌍곡계곡", "region": "괴산", "location": "충북 괴산군 칠성면", "note": "충청권 대표 계곡으로 가족 물놀이 후보예요."},
            {"name": "송계계곡", "region": "제천", "location": "충북 제천시 한수면", "note": "월악산 주변 드라이브와 같이 보기 좋아요."},
            {"name": "구천동계곡", "region": "무주", "location": "전북 무주군 설천면", "note": "긴 계곡길과 덕유산 여행을 묶기 좋아요."},
            {"name": "뱀사골계곡", "region": "남원", "location": "전북 남원시 산내면", "note": "지리산권 깊은 계곡 여행지예요."},
            {"name": "운문사계곡", "region": "청도", "location": "경북 청도군 운문면", "note": "대구 근교 계곡과 사찰 산책 조합이 좋아요."},
            {"name": "호박소계곡", "region": "밀양", "location": "경남 밀양시 산내면", "note": "영남권에서 물색과 바위 풍경으로 많이 찾는 곳이에요."},
        ],
        "searches": ["계곡 캠핑장", "계곡 백숙 맛집", "계곡 근처 저렴한 숙소", "아이와 가기 좋은 계곡"],
    },
    "바다": {
        "summary": "조용한 해변, 도시 바다, 섬 여행처럼 원하는 분위기에 따라 지역을 고르면 좋아요.",
        "regions": ["강릉", "속초", "동해", "양양", "고성", "태안", "보령", "군산", "부산", "여수", "남해", "제주"],
        "spots": [
            {"name": "경포해변", "region": "강릉", "location": "강원 강릉시 안현동", "note": "접근성, 숙소, 카페 선택지가 많아요."},
            {"name": "속초해수욕장", "region": "속초", "location": "강원 속초시 조양동", "note": "시장 먹거리와 설악산 일정을 같이 잡기 좋아요."},
            {"name": "망상해변", "region": "동해", "location": "강원 동해시 망상동", "note": "캠핑장과 넓은 백사장이 강점이에요."},
            {"name": "낙산해변", "region": "양양", "location": "강원 양양군 강현면", "note": "서핑, 카페, 낙산사 코스를 묶기 좋아요."},
            {"name": "송지호해변", "region": "고성", "location": "강원 고성군 죽왕면", "note": "조용한 동해 바다와 캠핑 후보로 좋아요."},
            {"name": "만리포해수욕장", "region": "태안", "location": "충남 태안군 소원면", "note": "서해 일몰과 가족 여행으로 많이 찾는 곳이에요."},
            {"name": "대천해수욕장", "region": "보령", "location": "충남 보령시 신흑동", "note": "숙소와 먹거리 인프라가 많은 서해 대표 해변이에요."},
            {"name": "선유도해수욕장", "region": "군산", "location": "전북 군산시 옥도면", "note": "섬 드라이브와 해변 산책을 같이 즐기기 좋아요."},
            {"name": "광안리해수욕장", "region": "부산", "location": "부산 수영구 광안해변로", "note": "도시 바다, 야경, 맛집이 강해요."},
            {"name": "만성리검은모래해변", "region": "여수", "location": "전남 여수시 만흥동", "note": "여수 먹거리와 밤바다 일정에 붙이기 좋아요."},
            {"name": "상주은모래비치", "region": "남해", "location": "경남 남해군 상주면", "note": "남해 드라이브와 조용한 휴식에 어울려요."},
            {"name": "협재해변", "region": "제주", "location": "제주시 한림읍 협재리", "note": "맑은 물색, 카페, 서쪽 제주 코스에 좋아요."},
        ],
        "searches": ["오션뷰 카페", "바다 근처 가성비 숙소", "해산물 맛집", "해변 산책 코스"],
    },
    "캠핑": {
        "summary": "캠핑은 예약 가능 여부와 화장실·샤워실 상태가 중요해서 지도 리뷰 확인이 특히 중요해요.",
        "regions": ["가평", "동해", "강릉", "속초", "제주", "양평"],
        "searches": ["오토캠핑장", "카라반 캠핑장", "캠핑장 샤워실 깨끗한 곳", "반려견 동반 캠핑장"],
    },
    "맛집": {
        "summary": "시장, 현지식, 카페거리 순서로 보면 실패 확률이 낮아요.",
        "regions": ["강릉", "속초", "부산", "전주", "여수", "제주"],
        "searches": ["현지인 맛집", "시장 먹거리", "웨이팅 적은 맛집", "혼밥 맛집"],
    },
    "비오는날": {
        "summary": "비가 오면 미술관, 대형 카페, 시장, 스파, 실내 체험을 먼저 잡는 게 편해요.",
        "regions": ["서울", "부산", "강릉", "제주", "대전", "대구"],
        "searches": ["비오는날 실내 데이트", "실내 관광지", "대형 카페", "스파 마사지"],
    },
}


def get_kst_now():
    return datetime.now(KST)


def normalize(text):
    return text.strip().replace(" ", "").lower()


def search_url(query, service):
    encoded = quote_plus(query)
    if service == "naver":
        return f"https://search.naver.com/search.naver?query={encoded}"
    if service == "naver_map":
        return f"https://map.naver.com/p/search/{encoded}"
    if service == "google_map":
        return f"https://www.google.com/maps/search/{encoded}"
    if service == "booking":
        return f"https://www.google.com/search?q={quote_plus(query + ' 저렴한 숙소 후기')}"
    return f"https://www.google.com/search?q={encoded}"


def parse_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def estimate_cost(category, name):
    text = normalize(name)

    if category == "affordable_stays":
        if any(word in text for word in ["게스트하우스", "호스텔"]):
            return "예상 1박 3만-7만원"
        if any(word in text for word in ["모텔", "비즈니스호텔"]):
            return "예상 1박 5만-10만원"
        if any(word in text for word in ["리조트", "펜션", "풀빌라"]):
            return "예상 1박 8만-18만원"
        return "예상 1박 5만-12만원"

    if category == "camping":
        if any(word in text for word in ["글램핑", "카라반"]):
            return "예상 1박 7만-18만원"
        if any(word in text for word in ["오토", "캠핑", "야영"]):
            return "예상 1박 2만-7만원"
        return "예상 1박 3만-10만원"

    return ""


def find_region(query):
    clean_query = normalize(query)
    if not clean_query:
        return None

    for key, guide in REGION_GUIDES.items():
        searchable = normalize(key + guide["title"] + " ".join(guide["tags"]))
        if clean_query in searchable or searchable in clean_query:
            return key

    return None


def find_situations(query):
    clean_query = normalize(query)
    results = []
    for key, guide in SITUATION_GUIDES.items():
        if normalize(key) in clean_query or clean_query in normalize(key):
            results.append((key, guide))
    return results


def get_saved_notes():
    try:
        with open("travel_notes.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return ""


def save_note(text):
    with open("travel_notes.txt", "a", encoding="utf-8") as file:
        file.write("\n---\n")
        file.write(get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST") + "\n")
        file.write(text.strip() + "\n")


def link_row(query, include_stay=False):
    cols = st.columns(3 if not include_stay else 4)
    cols[0].link_button("네이버 검색", search_url(query, "naver"), width="stretch")
    cols[1].link_button("네이버 지도", search_url(query, "naver_map"), width="stretch")
    cols[2].link_button("구글 지도", search_url(query, "google_map"), width="stretch")
    if include_stay:
        cols[3].link_button("후기 비교", search_url(query, "booking"), width="stretch")


def social_metrics(seed):
    base = sum(ord(char) for char in seed)
    blog = 42 + (base % 118)
    instagram = 180 + ((base * 7) % 890)
    cafe = 18 + ((base * 5) % 84)
    facebook = 9 + ((base * 3) % 47)
    score = min(98, round((blog * 0.18) + (instagram * 0.045) + (cafe * 0.24) + (facebook * 0.16)))

    return {
        "score": score,
        "blog": blog,
        "instagram": instagram,
        "cafe": cafe,
        "facebook": facebook,
    }


@st.cache_data(ttl=60 * 15)
def load_social_candidates():
    if not SOCIAL_CANDIDATES_FILE.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(SOCIAL_CANDIDATES_FILE)
    except Exception:
        return pd.DataFrame()


def get_real_candidates(region_name, category, limit=50):
    data = load_social_candidates()
    if data.empty:
        return []

    required_columns = {
        "region", "category", "name", "query", "score",
        "blog_mentions", "instagram_mentions", "cafe_mentions", "facebook_mentions",
    }
    if not required_columns.issubset(data.columns):
        return []

    rows = data[
        (data["region"].astype(str) == region_name)
        & (data["category"].astype(str) == category)
    ].copy()

    if rows.empty:
        return []

    rows["score"] = pd.to_numeric(rows["score"], errors="coerce").fillna(0)
    rows = rows.sort_values("score", ascending=False).head(limit)
    candidates = []

    for index, row in enumerate(rows.to_dict("records"), start=1):
        candidates.append({
            "rank": index,
            "name": row["name"],
            "query": row.get("query") or row["name"],
            "source": row.get("source", "수집 데이터"),
            "address": row.get("address", ""),
            "source_count": int(row.get("source_count", 1) or 1),
            "kakao_match": parse_bool(row.get("kakao_match", False)),
            "tourapi_match": parse_bool(row.get("tourapi_match", False)),
            "cost_hint": estimate_cost(category, row["name"]),
            "metrics": {
                "score": int(row["score"]),
                "blog": int(row.get("blog_mentions", 0) or 0),
                "instagram": int(row.get("instagram_mentions", 0) or 0),
                "cafe": int(row.get("cafe_mentions", 0) or 0),
                "facebook": int(row.get("facebook_mentions", 0) or 0),
            },
        })

    return candidates


def make_candidate_name(region_name, source, category, index):
    suffixes = {
        "foods": ["현지인 추천", "웨이팅 적은 곳", "가성비", "시장 근처", "주차 편한 곳"],
        "affordable_stays": ["후기 좋은 곳", "가성비", "주차 편한 곳", "깨끗한 곳", "위치 좋은 곳"],
        "camping": ["예약 후기", "화장실 깨끗한 곳", "조용한 사이트", "오토캠핑", "초보 캠핑"],
        "places": ["사진 명소", "산책 코스", "주차 편한 곳", "아이와 함께", "비오는날 대안"],
        "desserts": ["디저트 맛집", "커피 맛집", "오션뷰", "조용한 카페", "빵지순례"],
    }
    suffix = suffixes[category][index % len(suffixes[category])]
    return f"{region_name} {source} {suffix}"


def build_ranked_candidates(guide, category, limit=50):
    real_candidates = get_real_candidates(guide["title"], category, limit=limit)
    if real_candidates:
        return real_candidates

    sources = guide[category]
    candidates = []

    for index in range(limit):
        source = sources[index % len(sources)]
        name = make_candidate_name(guide["title"], source, category, index)
        metrics = social_metrics(f"{guide['title']}:{category}:{name}:{index}")
        candidates.append({
            "rank": index + 1,
            "name": name,
            "query": name,
            "source": "임시 랭킹",
            "address": "",
            "cost_hint": estimate_cost(category, name),
            "metrics": metrics,
        })

    return sorted(candidates, key=lambda item: item["metrics"]["score"], reverse=True)


@st.cache_data(ttl=60 * 30)
def collect_live_candidates(region_name, category, limit=50):
    if not local_candidates or not count_mentions or not score_candidate:
        return []

    candidates = []

    try:
        raw_candidates = local_candidates(region_name, category)
    except Exception:
        return []

    for item in raw_candidates:
        query = item.get("query") or f"{region_name} {item['name']}"
        blog_mentions = count_mentions("blog", query)
        cafe_mentions = count_mentions("cafearticle", query)
        metrics = {
            "blog": blog_mentions,
            "instagram": 0,
            "cafe": cafe_mentions,
            "facebook": 0,
            "score": score_candidate(
                blog_mentions,
                cafe_mentions,
                source_count=item.get("source_count", 1),
                kakao_match=item.get("kakao_match", False),
                tourapi_match=item.get("tourapi_match", False),
            ),
        }
        candidates.append({
            "rank": 0,
            "name": item["name"],
            "query": query,
            "source": item.get("source", "live_search"),
            "address": item.get("address", ""),
            "source_count": item.get("source_count", 1),
            "cost_hint": estimate_cost(category, item["name"]),
            "metrics": metrics,
        })

    candidates = sorted(candidates, key=lambda item: item["metrics"]["score"], reverse=True)
    for index, candidate in enumerate(candidates[:limit], start=1):
        candidate["rank"] = index

    return candidates[:limit]


def render_candidate_card(candidate, include_stay=False):
    metrics = candidate["metrics"]

    with st.container(border=True):
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            st.markdown(f"**{candidate['rank']}. {candidate['name']}**")
            st.caption(
                f"블로그 {metrics['blog']} · 인스타 {metrics['instagram']} · "
                f"카페 {metrics['cafe']} · 페이스북 {metrics['facebook']}"
            )
            if candidate.get("address"):
                st.caption(f"위치: {candidate['address']}")
            if candidate.get("cost_hint"):
                st.caption(f"비용: {candidate['cost_hint']}")
            st.caption(
                f"데이터: {candidate.get('source', '수집 데이터')} · "
                f"출처 {candidate.get('source_count', 1)}개"
            )
        with header_cols[1]:
            st.metric("반응 점수", f"{metrics['score']}점")

        st.progress(metrics["score"] / 100)

        with st.expander("검증 링크 열기"):
            link_row(candidate["query"], include_stay=include_stay)


def render_ranked_section(guide, category, title, caption, include_stay=False):
    st.markdown(f"#### {title}")
    st.caption(caption)

    candidates = build_ranked_candidates(guide, category)
    display_limit = st.slider(
        "표시할 후보 수",
        min_value=10,
        max_value=min(50, max(10, len(candidates))),
        value=min(10, len(candidates)),
        step=10,
        key=f"{guide['title']}_{category}_limit",
    )
    if candidates and candidates[0].get("source") == "임시 랭킹":
        st.caption("아직 수집 CSV가 없어 임시 랭킹을 보여줍니다. 수집 스크립트를 실행하면 실제 데이터로 바뀝니다.")
    else:
        st.caption("수집된 블로그·카페·소셜 반응 데이터를 합산해 정렬했습니다.")

    st.caption(f"총 {len(candidates)}개 후보 중 상위 {display_limit}개를 보여줍니다.")

    for display_rank, candidate in enumerate(candidates[:display_limit], start=1):
        candidate["rank"] = display_rank
        render_candidate_card(candidate, include_stay=include_stay)

    st.markdown("##### 더 확인하기")
    broad_query = {
        "foods": f"{guide['title']} 맛집",
        "affordable_stays": f"{guide['title']} 저렴한 숙소 후기",
        "camping": f"{guide['title']} 캠핑장",
        "places": f"{guide['title']} 가볼만한곳",
        "desserts": f"{guide['title']} 빵집 카페 디저트",
    }[category]
    link_row(broad_query, include_stay=include_stay)


def render_live_region(region_name):
    st.markdown(
        f"""
        <section class="hero" style="background-image: linear-gradient(90deg, rgba(16, 22, 28, .72), rgba(16, 22, 28, .2)), url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80');">
            <div>
                <p class="eyebrow">실시간 지역 검색</p>
                <h1>{region_name}</h1>
                <p class="hero-copy">준비된 지역 데이터가 없어도 공식 검색 API로 후보를 먼저 수집해서 보여줍니다.</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    section_tabs = st.tabs(list(CATEGORY_LABELS.values()))
    categories = list(CATEGORY_LABELS.keys())

    for tab, category in zip(section_tabs, categories):
        with tab:
            st.markdown(f"#### {CATEGORY_LABELS[category]} 후보")
            st.caption(CATEGORY_CAPTIONS[category])
            with st.spinner(f"{region_name} {CATEGORY_LABELS[category]} 후보를 수집하는 중입니다."):
                candidates = collect_live_candidates(region_name, category)

            if candidates:
                display_limit = st.slider(
                    "표시할 후보 수",
                    min_value=10,
                    max_value=min(50, max(10, len(candidates))),
                    value=min(10, len(candidates)),
                    step=10,
                    key=f"live_{region_name}_{category}_limit",
                )
                st.caption("네이버 지역·블로그·카페와 사용 가능한 추가 API 신호를 합산해 정렬했습니다.")
                st.caption(f"총 {len(candidates)}개 후보 중 상위 {display_limit}개를 보여줍니다.")
                for candidate in candidates[:display_limit]:
                    render_candidate_card(
                        candidate,
                        include_stay=category == "affordable_stays",
                    )
            else:
                st.warning("이 카테고리의 후보를 아직 수집하지 못했어요. 검증 링크로 바로 이어갈게요.")
                fallback_query = {
                    "foods": f"{region_name} 맛집",
                    "affordable_stays": f"{region_name} 저렴한 숙소 후기",
                    "camping": f"{region_name} 캠핑장",
                    "places": f"{region_name} 가볼만한곳",
                    "desserts": f"{region_name} 빵집 카페 디저트",
                }[category]
                link_row(fallback_query, include_stay=category == "affordable_stays")


def render_chip_row(items):
    chips = "".join(f"<span class='chip'>{item}</span>" for item in items)
    st.markdown(f"<div class='chip-row'>{chips}</div>", unsafe_allow_html=True)


def render_search_item(label, query, hint=None, include_stay=False):
    with st.container(border=True):
        st.markdown(f"**{label}**")
        if hint:
            st.caption(hint)
        st.caption(f"검색어: {query}")
        link_row(query, include_stay=include_stay)


def render_region(guide):
    st.markdown(
        f"""
        <section class="hero" style="background-image: linear-gradient(90deg, rgba(16, 22, 28, .72), rgba(16, 22, 28, .24)), url('{guide["hero"]}');">
            <div>
                <p class="eyebrow">지역 검색 결과</p>
                <h1>{guide["title"]}</h1>
                <p class="hero-copy">{guide["subtitle"]}</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    render_chip_row(guide["tags"])

    st.markdown("### 먼저 볼 것")
    quick_cols = st.columns(4)
    quick_cols[0].link_button("맛집 지도", search_url(f"{guide['title']} 맛집", "naver_map"), width="stretch")
    quick_cols[1].link_button("저렴한 숙소", search_url(f"{guide['title']} 저렴한 숙소 후기", "booking"), width="stretch")
    quick_cols[2].link_button("캠핑장", search_url(f"{guide['title']} 캠핑장", "naver_map"), width="stretch")
    quick_cols[3].link_button("가볼만한곳", search_url(f"{guide['title']} 가볼만한곳", "naver"), width="stretch")

    section_tabs = st.tabs(["먹을 곳", "저렴한 숙소", "캠핑장", "갈 곳·즐길거리", "디저트·카페"])

    with section_tabs[0]:
        render_ranked_section(
            guide,
            "foods",
            "소셜 반응이 좋은 식사 후보 10",
            "식사는 현지 음식, 시장, 리뷰 반복 노출을 우선으로 봅니다.",
        )

    with section_tabs[1]:
        render_ranked_section(
            guide,
            "affordable_stays",
            "가성비 숙소 후보 10",
            "가격, 청결, 위치, 주차 언급이 같이 잡히는 숙소 후보를 먼저 보여줍니다.",
            include_stay=True,
        )

    with section_tabs[2]:
        render_ranked_section(
            guide,
            "camping",
            "캠핑장 후보 10",
            "캠핑장은 화장실, 샤워실, 사이트 간격, 예약 후기를 별도로 봅니다.",
        )

    with section_tabs[3]:
        render_ranked_section(
            guide,
            "places",
            "갈 곳과 즐길거리 후보 10",
            "명소, 산책, 체험, 사진 포인트를 섞어서 먼저 추려줍니다.",
        )

    with section_tabs[4]:
        render_ranked_section(
            guide,
            "desserts",
            "디저트와 커피 후보 10",
            "식사와 분리해서 빵집, 카페, 디저트 언급이 많은 후보를 보여줍니다.",
        )


def render_situation_spots(key, spots):
    st.markdown(f"**추천 {key} 12곳**")
    spot_cols = st.columns(3)

    for index, spot in enumerate(spots):
        with spot_cols[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{index + 1}. {spot['name']}**")
                st.caption(f"{spot['region']} · {spot['location']}")
                st.write(spot["note"])
                st.link_button(
                    "지도 보기",
                    search_url(spot["name"], "naver_map"),
                    width="stretch",
                )
                st.link_button(
                    "먹거리·숙소 같이 검색",
                    search_url(f"{spot['name']} 맛집 숙소 카페", "naver"),
                    width="stretch",
                )


def render_situation(query, situations):
    st.markdown("### 상황으로 찾기")
    st.caption("지역 이름이 아니라 계곡, 바다, 캠핑처럼 가고 싶은 장면을 입력한 경우예요. 계곡명·해변명처럼 실제 목적지를 먼저 보여주고, 지역은 보조 정보로 붙입니다.")

    for key, guide in situations:
        with st.container(border=True):
            st.markdown(f"#### {key}")
            st.write(guide["summary"])

            if guide.get("spots"):
                render_situation_spots(key, guide["spots"])

            with st.expander("관련 지역 후보 보기"):
                render_chip_row(guide["regions"])
                region_cols = st.columns(4)
                for index, region in enumerate(guide["regions"]):
                    with region_cols[index % 4]:
                        st.markdown(f"**{region}**")
                        st.caption(f"{key} 여행 후보")
                        st.link_button(f"{region} 지도 확인", search_url(f"{region} {query}", "naver_map"), width="stretch")

            st.markdown("**바로 써먹는 검색어**")
            for search in guide["searches"]:
                link_row(f"{query} {search}")


st.set_page_config(
    page_title="여행 지역 검색",
    page_icon="ᰔ",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #17212b;
        --muted: #64727f;
        --line: #d9e2e7;
        --sea: #1f8a9b;
        --leaf: #4d8b57;
        --sun: #f4a261;
        --paper: #fbfcfa;
    }
    .stApp {
        background: linear-gradient(180deg, #f5fbfc 0%, #fbfcfa 42%, #f7f4ee 100%);
        color: var(--ink);
    }
    .block-container {
        max-width: 1180px;
        padding-top: 1.8rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    div[data-testid="stSidebar"] {
        background: #edf6f7;
        border-right: 1px solid var(--line);
    }
    .app-title {
        display: flex;
        align-items: end;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: .75rem;
    }
    .title-copy h1 {
        font-size: 2.4rem;
        line-height: 1.08;
        margin: 0 0 .35rem 0;
    }
    .title-copy p {
        color: var(--muted);
        margin: 0;
        font-size: 1rem;
    }
    .hero {
        min-height: 320px;
        border-radius: 18px;
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: end;
        padding: 2rem;
        color: white;
        margin: .75rem 0 1rem 0;
        overflow: hidden;
    }
    .hero h1 {
        color: white;
        font-size: 3.6rem;
        line-height: .95;
        margin: .2rem 0 .5rem 0;
    }
    .hero-copy {
        font-size: 1.15rem;
        margin: 0;
        max-width: 680px;
    }
    .eyebrow {
        text-transform: uppercase;
        font-size: .78rem;
        letter-spacing: .08rem;
        margin: 0;
        opacity: .86;
    }
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: .45rem;
        margin: .4rem 0 1.1rem 0;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        min-height: 2rem;
        border: 1px solid #c7d6d8;
        border-radius: 999px;
        padding: .3rem .7rem;
        background: rgba(255,255,255,.78);
        color: #28424a;
        font-size: .9rem;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #d8e4e5;
        background: rgba(255, 255, 255, .74);
    }
    .stButton > button, .stLinkButton > a {
        border-radius: 999px;
        border-color: #b9d5d8;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.78);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .8rem 1rem;
    }
    @media (max-width: 760px) {
        .app-title {
            display: block;
        }
        .title-copy h1 {
            font-size: 2rem;
        }
        .hero {
            min-height: 250px;
            padding: 1.25rem;
        }
        .hero h1 {
            font-size: 2.5rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.sidebar.header("여행 메모")
memo = st.sidebar.text_area(
    "저장할 여행 아이디어",
    height=160,
    placeholder="예: 바다 캠핑 + 해산물 맛집 + 오션뷰 카페",
)

if st.sidebar.button("메모 저장", width="stretch"):
    if memo.strip():
        save_note(memo)
        st.sidebar.success("저장했어요.")
    else:
        st.sidebar.warning("메모 내용을 입력해 주세요.")

st.sidebar.divider()
st.sidebar.subheader("최근 메모")
saved_notes = get_saved_notes()
if saved_notes.strip():
    note_blocks = [block.strip() for block in saved_notes.split("---") if block.strip()]
    for note in reversed(note_blocks[-5:]):
        st.sidebar.info(note)
else:
    st.sidebar.caption("아직 저장된 메모가 없습니다.")


st.markdown(
    """
    <div class="app-title">
        <div class="title-copy">
            <h1>여행 지역 검색</h1>
            <p>지역을 입력하면 먹을 곳, 저렴한 숙소, 캠핑장, 갈 곳, 디저트를 한 번에 나눠서 찾아요.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"마지막 업데이트: {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')} KST")

search_cols = st.columns([3, 1])
query = search_cols[0].text_input(
    "지역이나 상황 검색",
    placeholder="예: 지역명, 계곡, 바다, 캠핑, 비오는날",
    label_visibility="collapsed",
)
search_type = search_cols[1].segmented_control(
    "검색 기준",
    ["자동", "지역", "상황"],
    default="자동",
    label_visibility="collapsed",
)

if not query.strip():
    st.markdown(
        """
        <section class="hero" style="background-image: linear-gradient(90deg, rgba(12, 33, 42, .72), rgba(12, 33, 42, .2)), url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80');">
            <div>
                <p class="eyebrow">Start with a place</p>
                <h1>어디서부터 볼까요?</h1>
                <p class="hero-copy">지역명을 입력해도 되고, 계곡이나 바다처럼 원하는 장면으로 시작해도 좋아요.</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    demo_cols = st.columns(3)
    demo_cols[0].metric("지역 검색", "먹거리·숙소·명소")
    demo_cols[1].metric("숙소", "가성비 우선")
    demo_cols[2].metric("캠핑", "별도 분리")

    st.markdown("### 상황으로 먼저 찾아보기")
    col1, col2, col3, col4 = st.columns(4)
    col1.link_button("계곡 캠핑", search_url("계곡 캠핑장", "naver"), width="stretch")
    col2.link_button("바다 여행", search_url("바다 여행지 추천", "naver"), width="stretch")
    col3.link_button("가성비 숙소", search_url("가성비 숙소 추천", "booking"), width="stretch")
    col4.link_button("디저트 카페", search_url("여행지 디저트 카페", "naver"), width="stretch")

else:
    if search_type == "상황":
        region_key = None
        situations = find_situations(query)
    elif search_type == "지역":
        region_key = find_region(query)
        situations = []
    else:
        situations = find_situations(query)
        region_key = None if situations else find_region(query)

    if situations:
        render_situation(query, situations)
    elif region_key:
        render_region(REGION_GUIDES[region_key])
    else:
        render_live_region(query.strip())
