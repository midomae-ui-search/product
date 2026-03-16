import streamlit as st
import sqlite3
import pandas as pd

# 1. 페이지 설정 및 디자인 적용
st.set_page_config(page_title="상품 카테고리 통합 검색기", layout="wide")

st.markdown("""
    <style>
    header, footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton, .viewerBadge_link__q6n6l, .viewerBadge_container__176p1, #MainMenu {
        display: none !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    .stApp { margin-top: -50px; }

    /* 위로 가기 버튼 스타일 */
    .top-btn { 
        position: fixed; 
        bottom: 80px; 
        right: 30px; 
        z-index: 999; 
        background: white; 
        border: 2px solid black; 
        border-radius: 50%; 
        width: 50px; 
        height: 50px; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        text-decoration: none; 
        color: black !important; 
        font-weight: bold; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.2); 
    }
    .top-btn:hover { background-color: #f0f2f6; }

    /* 초기화 X 버튼 블랙 스타일 커스텀 */
    div[data-testid="stButton"] > button:first-child {
        background-color: #333333; /* 버튼 배경색: 진한 회색/검정 */
        color: white !important;      /* X 아이콘 색상: 흰색 */
        border-radius: 50%;         /* 원형 모양 */
        width: 40px;
        height: 40px;
        border: none;
        padding: 0;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid="stButton"] > button:hover {
        background-color: #000000; /* 호버 시 완전 검정 */
        border: none;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 최상단 앵커 및 Top 버튼
st.markdown('<div id="top"></div>', unsafe_allow_html=True)
st.markdown('<a class="top-btn" href="#top">↑</a>', unsafe_allow_html=True)

# ---------------------------------------------------------
# [정보 설정] DB 및 테이블 정보
DB_FILE = '상품검색 V4.db' 
TABLE_NAME = '"상품검색v4 260316"' 
# ---------------------------------------------------------

def get_connection():
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Exception as e:
        st.error(f"❌ DB 연결 실패: {e}")
        return None

# 카테고리 매핑 데이터
category_data = {
    "전체": "ALL", "국내배송": "CATE118", "국내배송 특가 ~70%": "CATE128", "해외배송": "CATE119", "개런티": "CATE117", "H1": "CATE72", "H2": "CATE73", "H3": "CATE74", 
    "CC 넘버원": "CATE75", "CC 티무역": "CATE76", "CC 팬더": "CATE77", "CC 나비/기타": "CATE78", "CC 일반": "CATE80",
    "[고퀄]기타 브랜드": "CATE79", "PD": "CATE84", "LV": "CATE85", "CD": "CATE86", "CL": "CATE87", "GY": "CATE88", 
    "LP": "CATE89", "BV": "CATE90", "MIU": "CATE91", "YSL": "CATE92", "DV": "CATE93", "THE ROW": "CATE116", 
    "GG": "CATE95", "FF": "CATE94", "BL": "CATE97", "BBR": "CATE98", "LW": "CATE100", "VT": "CATE99", "CHL": "CATE96", 
    "BAOBAO": "CATE101", "기타브랜드": "CATE102", "여행구/캐리어": "CATE103", "여성 의류": "CATE47", "바람막이/경량": "CATE48", 
    "여성패딩(겨울용)": "CATE66", "코트/퍼/무스탕(겨울용)": "CATE129", "맨즈 의류": "CATE68", "맨즈 아우터": "CATE69", 
    "키즈의류": "CATE130", "키즈 아우터": "CATE131", "여성 신발": "CATE105", "[수공]H 신발": "CATE106", "[수공]CC 신발": "CATE107", 
    "[수공]기타 신발": "CATE108", "남성 신발": "CATE109", "[수공]남성 신발": "CATE110", "키즈 신발": "CATE111", 
    "시계": "CATE113", "시계정보": "CATE114", "악세서리": "CATE125", "18K 금 제작": "CATE126", "지갑": "CATE115", 
    "모자": "CATE134", "스카프/머플러": "CATE127", "선글라스/안경": "CATE133", "기타잡화/소품": "CATE135", "여성 벨트": "CATE136", 
    "맨즈 벨트/잡화": "CATE139"
}

st.title("🔍 상품 카테고리 통합 검색기")

# --- 검색어 초기화 로직 ---
if "keyword_val" not in st.session_state:
    st.session_state.keyword_val = ""

def clear_search():
    st.session_state.keyword_val = ""

# 4. 검색 영역
col_cat, col_keyword, col_clear = st.columns([1, 2.5, 0.4])

with col_cat:
    selected_name = st.selectbox("📂 카테고리 선택", list(category_data.keys()))
    selected_code = category_data[selected_name]

with col_keyword:
    keyword = st.text_input(
        "🔎 검색어 입력", 
        placeholder="엔터만 치면 전체를 보여줍니다.",
        key="keyword_val"
    )

with col_clear:
    st.write(" ") # 수직 정렬용 여백
    st.write(" ") 
    # CSS로 블랙 원형 버튼이 적용될 버튼
    st.button("X", on_click=clear_search)

st.divider()

# 5. 데이터 검색 및 출력 로직
conn = get_connection()
if conn:
    if 'load_count' not in st.session_state:
        st.session_state.load_count = 100

    conditions = ['"판매상태" NOT IN ("숨김", "품절")']

    if keyword:
        k_list = keyword.split()
        k_cond = " AND ".join([f'("상품명" LIKE "%{k}%" OR "원산지" LIKE "%{k}%" OR "상품번호" LIKE "%{k}%")' for k in k_list])
        conditions.append(f"({k_cond})")
        
    if selected_code != 'ALL':
        conditions.append(f'"카테고리ID" LIKE "%{selected_code}%"')

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    try:
        count_query = f'SELECT COUNT(*) FROM {TABLE_NAME} {where_clause}'
        total_count = pd.read_sql(count_query, conn).iloc[0, 0]

        query = f'SELECT * FROM {TABLE_NAME} {where_clause} LIMIT {st.session_state.load_count}'
        df = pd.read_sql(query, conn)

        if total_count > 0:
            st.info(f"✅ **{selected_name}** 검색 결과: **{total_count:,}**건")
            
            for _, row in df.iterrows():
                res_col1, res_col2 = st.columns([1, 4])
                with res_col1:
                    if row.get('대표이미지URL'):
                        st.image(row['대표이미지URL']) 
                with res_col2:
                    st.markdown(f"### {row['상품명']}")
                    st.write(f"**🔢 번호:** `{row['상품번호']}` | {row['원산지']}")
                    st.link_button("🔗 상세페이지 바로가기", row['상품URL'])
                st.divider()

            if total_count > st.session_state.load_count:
                if st.button(f"🔽 나머지 {total_count - st.session_state.load_count:,}개 더보기"):
                    st.session_state.load_count += 100
                    st.rerun()
        else:
            st.warning("검색 결과가 없습니다.")
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
    
    conn.close()
