import streamlit as st
import sqlite3
import pandas as pd

# 1. 한글 초성 처리 함수들
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    result = []
    for char in str(text):
        if '가' <= char <= '힣':
            char_code = ord(char) - ord('가')
            chosung_index = char_code // 588
            result.append(CHOSUNG_LIST[chosung_index])
        else:
            result.append(char)
    return "".join(result)

def check_is_chosung(word):
    if not word: return False
    CHOSUNG_SET = set(['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'])
    return all(char in CHOSUNG_SET for char in word)

# 2. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="상품 카테고리 통합 검색기", layout="wide")

if "search_input" not in st.session_state:
    st.session_state.search_input = ""

def clear_search():
    st.session_state.search_input = ""

# 3. CSS: 에러 방지 및 버튼 수평 정렬 (마진 값 상향)
st.markdown("""
    <style>
    header, footer {visibility: hidden !important;}
    .stApp { margin-top: -50px; }
    
    /* X 버튼을 검색창 박스 높이에 맞추기 위해 강제로 아래로 내림 */
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

# --- 검색 영역 (컬럼 비율 명시) ---
col_cat, col_keyword, col_clear = st.columns([2, 5, 1])

with col_cat:
    selected_name = st.selectbox("📂 카테고리", list(category_data.keys()))
    selected_code = category_data[selected_name]

with col_keyword:
    keyword = st.text_input("🔎 검색어 입력", key="search_input", placeholder="엔터시 전체보기 가능,  초성+단어 조합 가능")

with col_clear:
    st.button("✖️", on_click=clear_search)

st.divider()

# 4. 데이터 로드 및 검색
conn = sqlite3.connect(DB_FILE)
if conn:
    if 'load_count' not in st.session_state: st.session_state.load_count = 100
    conditions = ['"판매상태" NOT IN ("숨김", "품절")']
    if selected_code != 'ALL':
        conditions.append(f'"카테고리ID" LIKE "%{selected_code}%"')
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    try:
        full_df = pd.read_sql(f'SELECT * FROM {TABLE_NAME} {where_clause}', conn)

        if keyword:
            search_terms = keyword.split()
            def match_search(row_name):
                name, chosung = str(row_name), get_chosung(str(row_name))
                return all((term in chosung if check_is_chosung(term) else term in name) for term in search_terms)
            full_df = full_df[full_df['상품명'].apply(match_search)]

        total_count = len(full_df)
        df = full_df.head(st.session_state.load_count)

        if total_count > 0:
            st.info(f"✅ 검색 결과: **{total_count:,}**건")
            for _, row in df.iterrows():
                # [수정] st.columns()에 [1, 4]를 넣어 'spec' 에러 해결
                res_col1, res_col2 = st.columns([1, 4])
                with res_col1:
                    if row.get('대표이미지URL'): st.image(row['대표이미지URL']) 
                with res_col2:
                    st.markdown(f"### {row.get('상품명', '')}")
                    st.write(f"**🔢 번호:** `{row.get('상품번호', '')}`")
                    st.link_button("🔗 상세페이지 바로가기", row.get('상품URL', '#'))
                st.divider()
        else:
            st.warning("검색 결과가 없습니다.")
    except Exception as e:
        st.error(f"오류 발생: {e}")
    conn.close()
