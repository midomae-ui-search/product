import streamlit as st
import sqlite3
import pandas as pd

# 1. 페이지 설정 및 디자인 적용
st.set_page_config(page_title="상품 검색기", layout="wide")

st.markdown("""
    <style>
    header, footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton, .viewerBadge_link__q6n6l, .viewerBadge_container__176p1, #MainMenu {
        display: none !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    
    /* 여기서부터 추가/수정 */
    .stApp { margin-top: -45px !important; } /* 숫자를 -80 정도로 더 키우면 바짝 붙습니다 */
    
    .block-container {
        padding-top: 0rem !important; /* 위쪽 내부 여백 완전 제거 */
        padding-bottom: 0rem !important;
    }

    [data-testid="stHeader"] {
        display: none !important; /* 상단 헤더 영역 숨김 */
    }

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
TABLE_NAME = '"상품검색v4"' 
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
    "전체": "ALL", "국내배송": "CATE118", "국내배송 특가 ~70%": "CATE128", "현지오늘배송": "CATE119", "개런티": "CATE117", "H1": "CATE72", "H2": "CATE73", "H3": "CATE74", 
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

# font-size를 24px 정도로 줄이고 간격을 조정합니다.
st.markdown("<h2 style='font-size: 24px; margin-bottom: -20px;'>🔍 상품 검색기</h2>", unsafe_allow_html=True)


# --- 검색어 초기화 로직 ---
# 검색 UI 최적화: 모바일 가로 유지 및 버튼 간격 조정
st.markdown("""
    <style>
    /* 1. 모바일에서도 컬럼이 밑으로 떨어지지 않게 강제 가로 배치 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }

    /* 이미지와 텍스트 사이 간격 미세 조정 */
    [data-testid="column"]:nth-of-type(1) {
        padding-right: 10px !important;
    }

    /* 2. 입력창과 버튼 사이의 간격(여백) 확보 */
    [data-testid="column"] {
        padding-right: 5px !important;
    }

    /* 3. 라벨 숨겨서 위쪽 여백 제거 */
    div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label {
        display: none !important;
    }

    /* 4. 버튼 위치 수직 중앙 맞춤 */
    div[data-testid="stButton"] {
        margin-top: 0px !important;
        display: flex;
        justify-content: center;

    /* 5. 버튼 크기 조절 (버튼 때문에 밀리는 경우 방지) */
    .stButton button {
        width: auto !important;
        padding: 2px 10px !important;
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)


if "keyword_val" not in st.session_state:
    st.session_state.keyword_val = ""

def clear_search():
    st.session_state.keyword_val = ""

# 컬럼 비율: 카테고리(1) : 검색어(2.2) : X버튼(0.5)
# gap="small"을 주어 너무 붙지 않게 설정합니다.
col_cat, col_keyword, col_clear = st.columns([1, 2.2, 0.5], gap="small")

with col_cat:
    selected_name = st.selectbox("카테고리", list(category_data.keys()), label_visibility="collapsed")
    selected_code = category_data[selected_name]

with col_keyword:
    keyword = st.text_input("검색어", placeholder="검색어 입력", key="keyword_val", label_visibility="collapsed")

with col_clear:
    st.button("X", on_click=clear_search)

# --- 여기까지 교체 ---

st.markdown("""
    <div style="text-align: center; color: #ff4b4b; font-weight: bold; font-size: 17.5px;">
        * 국내배송/현지오늘배송은 사이트 내 진열 목록에서 확인 부탁드립니다.
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 16px; margin-bottom: 10px; opacity: 0.2;'>", unsafe_allow_html=True)

# 5. 데이터 검색 및 출력 로직
conn = get_connection()
if conn:
    if 'load_count' not in st.session_state:
        st.session_state.load_count = 100

    conditions = ['"판매상태" NOT IN ("숨김", "품절")', '"상품명" NOT LIKE "%배송%"']

    if keyword:
        k_list = keyword.split()
        k_cond = " AND ".join([f'("상품명" LIKE "%{k}%" OR "원산지" LIKE "%{k}%")' for k in k_list])
        conditions.append(f"({k_cond})")
        
    if selected_code != 'ALL':
        conditions.append(f'"카테고리ID" LIKE "%{selected_code}%"')

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    try:
        # 1. 데이터 가져오기 (들여쓰기 교정 완료)
        count_query = f'SELECT COUNT(*) FROM {TABLE_NAME} {where_clause}'
        total_count = pd.read_sql(count_query, conn).iloc[0, 0]

        query = f'SELECT * FROM {TABLE_NAME} {where_clause} LIMIT {st.session_state.load_count}'
        df = pd.read_sql(query, conn)

        if total_count > 0:
            # 2. 상단 검색 결과 요약 바 (배경은 어둡게 고정하되 텍스트는 흰색으로 명시)
            st.markdown(f"""
                  <div style="
                    background-color: #31333F;   /* 배경색: 어두운 회색(Streamlit 기본 다크 테마색) */
                    padding: 5px 10px;           /* 안쪽 여백: 위아래 10px, 좌우 15px */
                    border-radius: 8px;            /* 테두리 곡률: 모서리를 8px만큼 둥글게 처리 */
                    font-size: 14px;                /* 글자 크기: 14px */
                    margin-top: -25px;    /* 위쪽 여백 강제 축소 (숫자가 클수록 위로 올라감) */
                    margin-bottom: 0px;          /* 아래쪽 바깥 여백: 0으로 설정하여 다음 요소와 밀착 */
                    color: #FFFFFF;                 /* 글자 색상: 흰색 */
                  ">
                    ✅ <b>{selected_name}</b> 검색 결과: <b>{total_count:,}</b>건
                </div>
            """, unsafe_allow_html=True)
    
            # 3. 상품 리스트 출력
            for _, row in df.iterrows():
                target_url = row['상품URL']
                img_url = row['대표이미지URL'] if row.get('대표이미지URL') else ""
                
                st.markdown(f"""
                    <a href="{target_url}" target="_blank" style="text-decoration: none; color: inherit;">
                        <div style="
                            display: flex; 
                            gap: 20px; 
                            padding: 15px 0; 
                            border-bottom: 1px solid rgba(128, 128, 128, 0.2); 
                            align-items: center;
                            cursor: pointer;">
                            <div style="flex: 1; min-width: 140px; max-width: 160px;">
                                <img src="{img_url}" style="width: 100%; border-radius: 8px; aspect-ratio: 1/1; object-fit: cover;">
                            </div>
                            <div style="flex: 4;">
                                <!-- 색상을 직접 지정하지 않고 inherit를 사용하여 시스템 테마 폰트색을 따름 -->
                                <h5 style="margin: 0 0 8px 0; font-size: 1.1rem; font-weight: 600; color: inherit;">{row['상품명']}</h5>
                                <p style="margin: 0; font-size: 14px; opacity: 0.7; color: inherit;"> {row['원산지']}</p>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            # 4. 더보기 버튼
            if total_count > st.session_state.load_count:
                if st.button(f"🔽 나머지 {total_count - st.session_state.load_count:,}개 더보기"):
                    st.session_state.load_count += 100
                    st.rerun()
        else:
            st.warning("검색 결과가 없습니다.")

    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
    
    conn.close()
