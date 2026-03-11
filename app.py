import streamlit as st
import sqlite3
import pandas as pd

# 1. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="상품 카테고리 통합 검색기", layout="wide")

if "search_input" not in st.session_state:
    st.session_state.search_input = ""

def clear_search():
    st.session_state.search_input = ""

# 2. CSS: 버튼 정렬 및 스타일
st.markdown("""
    <style>
    header, footer {visibility: hidden !important;}
    .stApp { margin-top: -50px; }
    div[data-testid="stColumn"]:nth-child(3) button {
        margin-top: 32px !important; 
        height: 42px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
DB_FILE = '상품검색 V4.db' 
TABLE_NAME = '"상품검색v4 260311"' 
# ---------------------------------------------------------

# [최적화 1] 데이터 불러오기 캐싱 (서버 메모리에 저장하여 1초 이내 응답)
@st.cache_data(ttl=3600) # 1시간 동안 데이터를 메모리에 유지
def get_all_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(f'SELECT * FROM {TABLE_NAME} WHERE "판매상태" NOT IN ("숨김", "품절")', conn)
    conn.close()
    return df

category_data = {
    "전체": "ALL", "개런티": "CATE117", "H1": "CATE72", "H2": "CATE73", "H3": "CATE74", 
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

col_cat, col_keyword, col_clear = st.columns([1.5, 4, 0.5])
with col_cat:
    selected_name = st.selectbox("📂 카테고리", list(category_data.keys()))
    selected_code = category_data[selected_name]
with col_keyword:
    keyword = st.text_input("🔎 검색어 입력", key="search_input", placeholder="검색어 입력 후 엔터")
with col_clear:
    st.button("✖️", on_click=clear_search)

st.divider()

# [최적화 2] 데이터 필터링 로직 개선
full_df = get_all_data()

if 'load_count' not in st.session_state:
    st.session_state.load_count = 100

# 검색 필터 적용
filtered_df = full_df.copy()

if selected_code != 'ALL':
    filtered_df = filtered_df[filtered_df['카테고리ID'].str.contains(selected_code, na=False)]

if keyword.strip():
    k_list = keyword.split()
    for k in k_list:
        # 상품명, 원산지, 상품번호 중 하나라도 포함되면 필터링
        filtered_df = filtered_df[
            filtered_df['상품명'].str.contains(k, case=False, na=False) |
            filtered_df['상품번호'].astype(str).str.contains(k, na=False)
        ]

total_count = len(filtered_df)
df_to_show = filtered_df.head(st.session_state.load_count)

# 4. 결과 출력
if total_count > 0:
    st.info(f"✅ 검색 결과: **{total_count:,}**건")
    for _, row in df_to_show.iterrows():
        res_col1, res_col2 = st.columns([1, 4])
        with res_col1:
            if row.get('대표이미지URL'): 
                st.image(row['대표이미지URL'], use_container_width=True) 
        with res_col2:
            st.markdown(f"### {row.get('상품명', '')}")
            st.write(f"**🔢 번호:** `{row.get('상품번호', '')}`")
            st.link_button("🔗 상세페이지 바로가기", row.get('상품URL', '#'))
        st.divider()

    if total_count > st.session_state.load_count:
        if st.button("더보기"):
            st.session_state.load_count += 100
            st.rerun()
else:
    st.warning("검색 결과가 없습니다.")
