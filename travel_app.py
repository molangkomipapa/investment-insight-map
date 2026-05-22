from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus

import pandas as pd
import streamlit as st


KST = timezone(timedelta(hours=9))


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
        "summary": "물놀이와 캠핑을 같이 보기 좋고, 숙소는 펜션·캠핑장 중심으로 비교하면 좋아요.",
        "regions": ["가평", "양양", "인제", "포천", "무주", "지리산"],
        "searches": ["계곡 캠핑장", "계곡 백숙 맛집", "계곡 근처 저렴한 숙소", "아이와 가기 좋은 계곡"],
    },
    "바다": {
        "summary": "동해는 조용한 바다와 드라이브, 부산은 도시와 야경, 제주는 긴 휴식에 좋아요.",
        "regions": ["동해", "강릉", "속초", "부산", "제주", "여수"],
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
        st.markdown("#### 식사 후보")
        for food in guide["foods"]:
            render_search_item(food, f"{guide['title']} {food} 맛집", "후기 수, 최근 리뷰, 영업시간을 같이 확인해 보세요.")

    with section_tabs[1]:
        st.markdown("#### 저렴하지만 괜찮은 숙소 찾기")
        st.info("숙소는 가격 변동과 예약 상황이 커서, 앱에서는 '가성비 검색어'를 잘 잡아주고 지도·후기 비교로 이어지게 만들었어요.")
        for stay in guide["affordable_stays"]:
            render_search_item(stay, f"{stay} 저렴한 숙소 후기", "가격, 청결, 위치, 주차 리뷰를 우선 확인하면 좋아요.", include_stay=True)

    with section_tabs[2]:
        st.markdown("#### 캠핑장")
        for camp in guide["camping"]:
            render_search_item(camp, f"{camp} 예약 후기", "화장실, 샤워실, 사이트 간격, 매점 여부를 꼭 확인해 보세요.")

    with section_tabs[3]:
        st.markdown("#### 명소와 즐길거리")
        for place in guide["places"]:
            render_search_item(place, f"{guide['title']} {place}", "동선에 넣기 전에 주차와 운영시간을 확인하면 좋아요.")

    with section_tabs[4]:
        st.markdown("#### 디저트와 커피")
        for dessert in guide["desserts"]:
            render_search_item(dessert, f"{dessert} 추천", "식사와 별개로 쉬는 시간을 잡을 때 좋아요.")


def render_situation(query, situations):
    st.markdown("### 상황으로 찾기")
    st.caption("지역 이름이 아니라 계곡, 바다, 캠핑처럼 가고 싶은 장면을 입력한 경우예요.")

    for key, guide in situations:
        with st.container(border=True):
            st.markdown(f"#### {key}")
            st.write(guide["summary"])
            render_chip_row(guide["regions"])

            st.markdown("**추천 지역**")
            region_cols = st.columns(3)
            for index, region in enumerate(guide["regions"]):
                with region_cols[index % 3]:
                    st.link_button(
                        f"{region} 검색",
                        search_url(f"{region} {query}", "naver"),
                        width="stretch",
                    )

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
    placeholder="예: 동해 캠핑 + 묵호항 물회 + 오션뷰 카페",
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
    placeholder="예: 동해, 강릉, 속초, 계곡, 바다, 캠핑",
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
                <p class="hero-copy">동해처럼 지역을 입력해도 되고, 계곡이나 바다처럼 원하는 장면으로 시작해도 좋아요.</p>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    demo_cols = st.columns(3)
    demo_cols[0].metric("지역 검색", "먹거리·숙소·명소")
    demo_cols[1].metric("숙소", "가성비 우선")
    demo_cols[2].metric("캠핑", "별도 분리")

    st.markdown("### 바로 눌러볼 추천 시작점")
    col1, col2, col3, col4 = st.columns(4)
    col1.link_button("동해 맛집", search_url("동해 맛집", "naver_map"), width="stretch")
    col2.link_button("동해 저렴한 숙소", search_url("동해 저렴한 숙소 후기", "booking"), width="stretch")
    col3.link_button("계곡 캠핑", search_url("계곡 캠핑장", "naver"), width="stretch")
    col4.link_button("바다 오션뷰 카페", search_url("바다 오션뷰 카페", "naver"), width="stretch")

else:
    region_key = find_region(query) if search_type in {"자동", "지역"} else None
    situations = find_situations(query) if search_type in {"자동", "상황"} else []

    if region_key:
        render_region(REGION_GUIDES[region_key])
    elif situations:
        render_situation(query, situations)
    else:
        st.warning("아직 앱 안에 준비된 지역/상황 데이터가 부족해요. 그래도 바로 검색할 수 있게 연결해둘게요.")
        fallback_tabs = st.tabs(["먹을 곳", "저렴한 숙소", "캠핑장", "갈 곳", "디저트"])
        with fallback_tabs[0]:
            link_row(f"{query} 맛집")
        with fallback_tabs[1]:
            link_row(f"{query} 저렴한 숙소 후기", include_stay=True)
        with fallback_tabs[2]:
            link_row(f"{query} 캠핑장")
        with fallback_tabs[3]:
            link_row(f"{query} 가볼만한곳")
        with fallback_tabs[4]:
            link_row(f"{query} 빵집 카페 디저트")

st.divider()
st.markdown("### 준비된 지역 데이터")
region_rows = [
    {
        "지역": guide["title"],
        "키워드": ", ".join(guide["tags"]),
        "대표 먹거리": ", ".join(guide["foods"][:3]),
        "캠핑": ", ".join(guide["camping"][:2]),
    }
    for guide in REGION_GUIDES.values()
]
st.dataframe(pd.DataFrame(region_rows), width="stretch", hide_index=True)
