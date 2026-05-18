import re
from datetime import datetime, timedelta, timezone
from collections import Counter

import streamlit as st
import yfinance as yf
import feedparser
import requests

try:
    from kiwipiepy import Kiwi
except ImportError:
    Kiwi = None


KST = timezone(timedelta(hours=9))
kiwi = Kiwi() if Kiwi else None


def get_kst_now():
    return datetime.now(KST)


# =============================
# 기본 설정
# =============================
st.set_page_config(
    page_title="투자 인사이트 맵",
    page_icon="🗺️",
    layout="centered"
)


# =============================
# 사이드바 메모
# =============================
st.sidebar.header("시장 흐름 메모")

memo = st.sidebar.text_area(
    "오늘 떠오른 투자 연결",
    height=250,
    placeholder="예: AI 데이터센터 → 전력 → 전선 → 변압기"
)

if st.sidebar.button("메모 저장"):
    if memo.strip():
        with open("market_memo.txt", "a", encoding="utf-8") as f:
            f.write("\n---\n")
            f.write(get_kst_now().strftime("%Y-%m-%d %H:%M:%S KST") + "\n")
            f.write(memo + "\n")
        st.sidebar.success("메모가 저장되었습니다.")
    else:
        st.sidebar.warning("메모 내용을 입력해 주세요.")

st.sidebar.divider()
st.sidebar.subheader("최근 저장 메모")

try:
    with open("market_memo.txt", "r", encoding="utf-8") as f:
        memo_history = f.read()

    memo_blocks = memo_history.split("---")
    recent_memos = memo_blocks[-5:]
    has_memo = False

    for memo_item in reversed(recent_memos):
        if memo_item.strip():
            has_memo = True
            st.sidebar.info(memo_item.strip())

    if not has_memo:
        st.sidebar.caption("아직 저장된 메모가 없습니다.")

except FileNotFoundError:
    st.sidebar.caption("아직 저장된 메모가 없습니다.")


# =============================
# 제목
# =============================
st.title("🗺️ 투자 인사이트 맵")

if st.button("🔄 데이터 새로고침"):
    st.rerun()

now_kst = get_kst_now()
st.caption(f"마지막 업데이트: {now_kst.strftime('%Y-%m-%d %H:%M:%S')} KST")
st.write(f"오늘 날짜: {now_kst.strftime('%Y-%m-%d')}")

st.divider()


# =============================
# 경제 흐름
# =============================
st.subheader("경제 흐름")


def get_price(ticker, suffix=""):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if data.empty:
            return "데이터 없음"

        price = round(data["Close"].iloc[-1], 2)
        return f"{price}{suffix}"
    except Exception:
        return "데이터 없음"


economic_data = {
    "미국 10년물 금리": get_price("^TNX", "%"),
    "원달러 환율": get_price("KRW=X", "원"),
    "나스닥 지수": get_price("^IXIC", ""),
    "WTI 유가": get_price("CL=F", "달러"),
    "코스피": get_price("^KS11", ""),
    "코스닥": get_price("^KQ11", ""),
}

for name, value in economic_data.items():
    st.write(f"**{name}** : {value}")

st.info(
    "경제 지표는 실시간 매매용이 아니라 시장 분위기를 보는 참고 지표입니다. "
    "금리·환율·유가·국내 지수 흐름을 뉴스 흐름과 함께 보는 것이 중요합니다."
)

st.divider()


# =============================
# 뉴스 설정
# =============================
rss_urls = [
    "https://www.yna.co.kr/rss/news.xml",
    "https://www.mk.co.kr/rss/30000001/",
    "https://www.sedaily.com/rss/NewsAll.xml",
    "https://rss.joins.com/joins_news_list.xml",
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
]

noise_words = {
    "오늘", "관련", "뉴스", "기자", "단독", "속보", "이번", "지난",
    "최대", "최소", "전망", "가능성", "발표", "정부", "시장", "기업",
    "그대로", "만에", "까지", "부터", "에게", "에서", "으로", "하고",
    "일부", "첫날", "하루", "사흘", "나흘", "오전", "오후", "당시",
    "최근", "관련해", "통해", "위해", "대해", "대상", "대비", "기준",
    "되나요", "되나", "되나?", "될까", "된다", "합니다", "했다", "한다",
    "나선", "두고", "뒤에", "앞두고", "속에", "중인", "올해", "내년",
    "작년", "전년", "개월", "분기", "상반기", "하반기", "업계", "관계자",
    "이유", "사람", "우리", "여기", "저기", "어디", "누가", "무엇",
    "공개", "확인", "논의", "추진", "검토", "요청", "방침", "예정",
    "시작", "종료", "개최", "참석", "진행", "상황", "모습", "현장",
    "quot", "amp", "종합", "포토", "영상", "속보", "단독",
    "the", "and", "for", "with", "from", "that", "this", "are", "was",
    "were", "have", "will", "news", "says", "after", "about", "into",
    "over", "under", "amid", "against", "first", "more", "year", "years",
    "they", "their", "them", "than", "when", "where", "what", "how",
}

noise_endings = (
    "되나요", "되나", "하나요", "했나요", "있나요", "없나요",
    "입니다", "합니다", "했다", "한다", "된다", "된다면",
    "했다가", "하면서", "된다며", "라며", "지만", "는데", "거나",
)

important_short_terms = {
    "ai", "2차전지", "ev", "ipo", "gpu", "hbm", "금리", "환율", "유가",
    "증시", "코스피", "코스닥", "반도체", "전력", "전선", "원전", "조선",
    "방산", "로봇", "바이오", "해운", "정유", "철강", "구리", "니켈",
}

market_signal_words = {
    "경제", "증시", "주식", "주가", "코스피", "코스닥", "나스닥", "금리",
    "환율", "달러", "원화", "유가", "원유", "물가", "인플레이션", "채권",
    "국채", "수출", "수입", "무역", "관세", "공급망", "실적", "매출",
    "영업이익", "수주", "계약", "투자", "증설", "공장", "생산", "반도체",
    "배터리", "2차전지", "전기차", "자동차", "조선", "방산", "전력", "전선",
    "원전", "로봇", "바이오", "제약", "철강", "화학", "정유", "해운",
    "항공", "건설", "부동산", "은행", "보험", "증권", "ai", "hbm", "gpu",
    "데이터센터", "엔비디아", "테슬라", "삼성전자", "sk하이닉스",
}

macro_context_words = {
    "미국", "중국", "일본", "유럽", "중동", "이란", "러시아", "우크라이나",
    "전쟁", "분쟁", "제재", "협상", "합의", "규제", "정책", "예산",
}

politics_social_noise_words = {
    "대통령", "국회", "정당", "의원", "후보", "선거", "총선", "대선",
    "여당", "야당", "검찰", "경찰", "재판", "법원", "구속", "기소",
    "수사", "혐의", "사건", "사고", "화재", "살인", "폭행", "논란",
    "사과", "입장", "비판", "시위", "집회", "교육", "학교", "학생",
}


def clean_title(title):
    title = re.sub("<.*?>", "", title)
    title = title.split(" - ")[0]
    title = title.replace("[속보]", "").replace("[단독]", "").replace("[종합]", "")
    return re.sub(r"\s+", " ", title).strip()


def get_candidate_words(title):
    if kiwi:
        return [
            token.form
            for token in kiwi.tokenize(title)
            if token.tag in {"NNG", "NNP", "SL"}
        ]

    return re.findall(r"[가-힣A-Za-z0-9]+", title)


def is_noise_term(word):
    lower = word.lower()

    if lower in noise_words or word in noise_words:
        return True

    if lower.endswith(noise_endings):
        return True

    if re.search(r"(첫날|일부|기준|대상|관련)$", word):
        return True

    if re.search(r"(한다|했다|된다|였다|왔다|없다|있다|된다며|라며)$", word):
        return True

    return False


def is_signal_term(term):
    lower = term.lower()

    if is_noise_term(term):
        return False

    if lower in important_short_terms:
        return True

    if re.match(r"^[a-z]+$", lower):
        return len(lower) >= 3

    if re.match(r"^[가-힣]+$", term):
        if len(term) < 3:
            return False

        return not re.search(r"(일보|기자|신문|방송|뉴스|닷컴)$", term)

    return len(lower) >= 3


def get_market_relevance_score(title, terms):
    text = (title + " " + " ".join(terms)).lower()
    score = 0

    for word in market_signal_words:
        if word.lower() in text:
            score += 2

    for word in macro_context_words:
        if word.lower() in text:
            score += 1

    for word in politics_social_noise_words:
        if word in text:
            score -= 1

    return score


def is_market_relevant_news(title, terms):
    score = get_market_relevance_score(title, terms)

    if score >= 2:
        return True

    return any(term in important_short_terms for term in terms)


def extract_terms(title):
    words = get_candidate_words(title)
    result = []

    for word in words:
        lower = word.lower()

        if len(lower) < 2:
            continue

        if is_noise_term(word):
            continue

        if re.match(r"^[a-z]+$", lower) and len(lower) < 4:
            continue

        if sum(c.isdigit() for c in lower) / len(lower) >= 0.5:
            continue

        if lower not in result:
            result.append(lower)

    return result


def get_source_score(source):
    source = source.lower()
    score = 0

    if "mk.co.kr" in source:
        score += 1

    if "sedaily.com" in source:
        score += 1

    if "joins.com" in source:
        score += 0.5

    if "yna.co.kr" in source:
        score += 0.5

    if "news.google.com" in source:
        score += 0.5

    if "naver" in source:
        score += 0.5

    return score

def get_article_nature_score(text):
    score = 0

    text = text.lower()

    # 숫자, 금액, 실적, 증감 표현
    if re.search(r"\d", text):
        score += 1

    impact_words = [
        "영업이익", "매출", "실적", "수주", "계약", "투자", "공급",
        "증설", "흑자", "적자", "상승", "하락", "급등", "급락",
        "돌파", "사상", "최대", "최저", "인수", "합병", "상장",
        "생산", "공장", "수출", "수입", "승인", "허가", "개발",
        "확산", "감염", "백신", "치료제", "규제", "제재", "관세",
        "협상", "합의", "분쟁", "전쟁", "충돌", "위기"
    ]

    for word in impact_words:
        if word in text:
            score += 1

    # 시장 전체와 연결되는 표현
    market_words = [
        "금리", "환율", "유가", "물가", "증시", "코스피", "코스닥",
        "나스닥", "달러", "원화", "국채", "채권", "원자재", "공급망"
    ]

    for word in market_words:
        if word in text:
            score += 2

    # 단순 정치·행사·논란성 표현은 약한 감점
    weak_words = [
        "후보", "공약", "기자회견", "비판", "논란", "사과",
        "입장", "주장", "반박", "고소", "폭로"
    ]

    for word in weak_words:
        if word in text:
            score -= 1

    return score

def get_naver_news(query="경제", display=20, require_market=True):
    url = "https://openapi.naver.com/v1/search/news.json"

    try:
        headers = {
            "X-Naver-Client-Id": st.secrets["NAVER_CLIENT_ID"],
            "X-Naver-Client-Secret": st.secrets["NAVER_CLIENT_SECRET"],
        }

        params = {
            "query": query,
            "display": display,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params, timeout=5)

        if response.status_code != 200:
            return []

        data = response.json()
        results = []

        for item in data.get("items", []):
            title = clean_title(item["title"])
            terms = extract_terms(title)

            if len(terms) < 2:
                continue

            if require_market and not is_market_relevant_news(title, terms):
                continue

            results.append({
                "title": title,
                "link": item["link"],
                "terms": terms,
                "term_set": set(terms),
                "source": "naver",
                "source_score": get_source_score("naver")
            })

        return results

    except Exception:
        return []


def make_connection_guide(issue, keywords):
    text = issue.lower() + " " + " ".join(keywords).lower()

    guide_rules = [
        {
            "signals": ["폭염", "더위", "전력", "전기", "냉방", "에어컨"],
            "guide": "전력 수요·냉방 수요·전력 인프라 흐름으로 확장되는지 살펴볼 수 있습니다.",
            "watch": ["전력 수요", "냉방", "전력기기", "전선", "원전"]
        },
        {
            "signals": ["ai", "데이터센터", "반도체", "엔비디아", "gpu", "자율주행"],
            "guide": "AI 확산이 반도체, 데이터센터, 전력·냉각 인프라로 이어지는지 살펴볼 필요가 있습니다.",
            "watch": ["반도체", "데이터센터", "전력", "냉각", "클라우드"]
        },
        {
            "signals": ["전기차", "배터리", "2차전지", "완성차", "충전"],
            "guide": "전기차 흐름이 배터리, 충전 인프라, 완성차 경쟁, 부품 공급망으로 이어지는지 볼 수 있습니다.",
            "watch": ["배터리", "충전 인프라", "완성차", "부품", "중국 전기차"]
        },
        {
            "signals": ["로봇", "휴머노이드", "피지컬", "자동화"],
            "guide": "로봇과 자동화 흐름이 제조업 투자, 부품, 센서, AI칩 수요로 이어지는지 볼 수 있습니다.",
            "watch": ["로봇", "자동화", "센서", "AI칩", "공장 자동화"]
        },
        {
            "signals": ["유가", "원유", "중동", "이란", "호르무즈", "석유"],
            "guide": "에너지 가격과 물류 리스크가 정유, 해운, 원자재, 방산 흐름으로 번지는지 관찰할 필요가 있습니다.",
            "watch": ["유가", "정유", "해운", "원자재", "방산"]
        },
        {
            "signals": ["코스피", "코스닥", "증시", "급등", "급락", "하락", "상승"],
            "guide": "시장 심리, 외국인 수급, 환율, 대형주 쏠림 여부를 함께 확인할 필요가 있습니다.",
            "watch": ["시장 심리", "외국인 수급", "환율", "대형주", "성장주"]
        },
    ]

    matched = []

    for rule in guide_rules:
        if any(signal in text for signal in rule["signals"]):
            matched.append(rule)

    if not matched:
        return (
            "아직 뚜렷한 산업 연결은 보이지 않습니다. 반복 노출이 이어지는지, 정책·실적·수급 변화로 번지는지 관찰할 필요가 있습니다.",
            []
        )

    guide_texts = [rule["guide"] for rule in matched[:2]]

    watch_terms = []
    for rule in matched[:2]:
        watch_terms.extend(rule["watch"])

    watch_terms = list(dict.fromkeys(watch_terms))

    return " ".join(guide_texts), watch_terms[:8]


# =============================
# 뉴스 수집
# =============================
news_data = []
seen_titles = set()

for url in rss_urls:
    try:
        feed = feedparser.parse(
            url,
            request_headers={"User-Agent": "Mozilla/5.0"}
        )

        for entry in feed.entries[:30]:
            title = clean_title(entry.title)

            if len(title) < 8:
                continue

            if title in seen_titles:
                continue

            terms = extract_terms(title)

            if len(terms) < 2:
                continue

            if not is_market_relevant_news(title, terms):
                continue

            seen_titles.add(title)

            news_data.append({
                "title": title,
                "link": entry.link,
                "terms": terms,
                "term_set": set(terms),
                "source": url,
                "source_score": get_source_score(url)
            })

    except Exception:
        pass


naver_queries = [
    "경제", "증시", "주식", "산업", "기업", "국제경제",
    "반도체", "전력", "방산", "조선", "환율", "금리"
]

for query in naver_queries:
    for news in get_naver_news(query, display=20):
        if news["title"] in seen_titles:
            continue

        if len(news["terms"]) < 2:
            continue

        seen_titles.add(news["title"])
        news_data.append(news)


# 고정 검색어만 보면 놓치는 흐름이 생길 수 있어, 오늘 감지된 키워드로 2차 확장 수집을 합니다.
seed_counter = Counter()

for news in news_data:
    for term in news["terms"]:
        if not is_signal_term(term):
            continue

        seed_counter[term] += 1

expansion_queries = [
    term for term, count in seed_counter.most_common(8)
    if count >= 2 and term not in naver_queries
]

for query in expansion_queries:
    for news in get_naver_news(query, display=8):
        if news["title"] in seen_titles:
            continue

        if len(news["terms"]) < 2:
            continue

        seen_titles.add(news["title"])
        news_data.append(news)


# =============================
# 뉴스 묶기
# =============================
clusters = []
used = set()

for i, news1 in enumerate(news_data):
    if i in used:
        continue

    cluster = [news1]
    used.add(i)

    for j, news2 in enumerate(news_data):
        if j in used:
            continue

        common_terms = news1["term_set"].intersection(news2["term_set"])

        if len(common_terms) >= 2:
            cluster.append(news2)
            used.add(j)

    clusters.append(cluster)


# =============================
# 이슈 계산
# =============================
issue_results = []

for cluster in clusters:
    all_terms = []

    for item in cluster:
        all_terms.extend(item["terms"])

    term_counts = Counter(all_terms)
    top_terms = [
        word for word, count in term_counts.most_common()
        if is_signal_term(word)
    ][:5]

    representative = cluster[0]
    issue_name = representative["title"]

    if len(issue_name) > 48:
        issue_name = issue_name[:48] + "..."

    weekly_count = len(cluster)

    source_score = len(set(x.get("source", "unknown") for x in cluster))
    media_score = sum(x.get("source_score", 0) for x in cluster)

    article_text = issue_name + " " + " ".join(top_terms)
    nature_score = get_article_nature_score(article_text)

    attention_score = (
       (len(cluster) * 3)
       + source_score
       + media_score
       + min(weekly_count, 50) / 5
       + nature_score
    )

    guide_text, watch_terms = make_connection_guide(issue_name, top_terms)

    issue_results.append({
        "issue": issue_name,
        "cluster_size": len(cluster),
        "weekly_count": weekly_count,
        "attention_score": round(attention_score, 1),
        "keywords": top_terms,
        "guide_text": guide_text,
        "watch_terms": watch_terms,
        "representative": representative,
        "items": cluster
    })

issue_results = sorted(
    issue_results,
    key=lambda x: x["attention_score"],
    reverse=True
)


# =========================
# 오늘 감지 키워드 TOP 7
# =========================

keyword_counter = {}

for news in news_data:
    for term in news["terms"]:
        if len(term) < 2:
            continue

        if not is_signal_term(term):
            continue

        keyword_counter[term] = keyword_counter.get(term, 0) + 1

top_keywords = sorted(
    [(keyword, count) for keyword, count in keyword_counter.items() if count >= 2],
    key=lambda x: (x[1], len(x[0])),
    reverse=True
)[:7]

st.subheader("🔥 오늘 감지 키워드 TOP 7")

if top_keywords:
    for idx, (keyword, count) in enumerate(top_keywords, start=1):
        st.write(f"{idx}. {keyword}")
else:
    st.caption("아직 반복 감지된 핵심 키워드가 없습니다.")

if expansion_queries:
    st.caption("2차 확장 검색어: " + ", ".join(expansion_queries))

st.divider()


# =========================
# 관심 키워드 검색
# =========================

def matches_search_terms(text, query):
    search_terms = [term.lower() for term in query.split() if term.strip()]
    text = text.lower()

    return all(term in text for term in search_terms)


def issue_search_text(item):
    issue_parts = [
        item["issue"],
        " ".join(item["keywords"]),
        " ".join(item["watch_terms"]),
        item["guide_text"],
    ]

    issue_parts.extend(news["title"] for news in item["items"])

    return " ".join(issue_parts)


def news_search_text(news):
    return " ".join([
        news["title"],
        " ".join(news["terms"]),
    ])


st.subheader("🔎 관심 키워드 직접 검색")

search_query = st.text_input(
    "더 보고 싶은 키워드",
    placeholder="예: 전력, 반도체, 환율, 로봇, 조선, 방산"
).strip()

if search_query:
    matched_issues = [
        item for item in issue_results
        if matches_search_terms(issue_search_text(item), search_query)
    ]

    matched_news = []
    seen_links = set()

    for news in news_data:
        if not matches_search_terms(news_search_text(news), search_query):
            continue

        if news["link"] in seen_links:
            continue

        seen_links.add(news["link"])
        matched_news.append(news)

    st.caption(
        f"현재 수집 뉴스 기준: 이슈 묶음 {len(matched_issues)}개 / 개별 뉴스 {len(matched_news)}개"
    )

    if matched_issues:
        st.markdown("#### 관련 이슈 묶음")

        for item in matched_issues[:5]:
            st.markdown(f"**{item['issue']}**")
            st.caption(
                f"묶인 뉴스: {item['cluster_size']}개 / 관심 집중도: {item['attention_score']}"
            )

            if item["keywords"]:
                st.write("반복 키워드:", ", ".join(item["keywords"]))

            st.info("연결 가이드: " + item["guide_text"])
            st.markdown(f"- [대표 뉴스 보기]({item['representative']['link']})")

            with st.expander("이 묶음의 뉴스 보기"):
                for news in item["items"][:8]:
                    st.markdown(f"- [{news['title']}]({news['link']})")

    if matched_news:
        st.markdown("#### 관련 개별 뉴스")

        for news in matched_news[:10]:
            st.markdown(f"- [{news['title']}]({news['link']})")

    extra_news = get_naver_news(search_query, display=10, require_market=False)

    if extra_news:
        st.markdown("#### 네이버 추가 검색")

        for news in extra_news[:10]:
            st.markdown(f"- [{news['title']}]({news['link']})")

    if not matched_issues and not matched_news and not extra_news:
        st.warning("검색 결과가 없습니다. 다른 키워드로 다시 검색해 주세요.")

st.divider()

# =========================
# 주요 뉴스
# =========================

st.subheader("주요 뉴스")

if not issue_results:
    st.warning("현재 감지된 뉴스 흐름이 없습니다. 잠시 후 다시 새로고침해 주세요.")

for item in issue_results[:10]:
    st.markdown(f"### {item['issue']}")

    st.caption(
        f"묶인 뉴스: {item['cluster_size']}개 / 현재 묶음 반복: {item['weekly_count']}회 / 관심 집중도: {item['attention_score']}"
    )

    st.caption("판단 기준: 반복성 + 출처 확산성 + 기사 성격")

    if item["keywords"]:
        st.write("반복 키워드:", ", ".join(item["keywords"]))

    st.info("연결 가이드: " + item["guide_text"])

    if item["watch_terms"]:
        st.write("확장해서 볼 흐름:", ", ".join(item["watch_terms"]))

    st.markdown(f"- [대표 뉴스 보기]({item['representative']['link']})")

    with st.expander("묶인 뉴스 보기"):
        for news in item["items"][:5]:
            st.markdown(f"- [{news['title']}]({news['link']})")
