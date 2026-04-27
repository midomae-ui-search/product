import streamlit as st
import sqlite3
import pandas as pd

# 1. 페이지 설정 및 디자인 적용
st.set_page_config(page_title="상품 검색기", layout="wide")

st.markdown("""
    <style>
    /* 1. 기본 설정 (헤더/푸러 숨김 등) */
    header, footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton, .viewerBadge_link__q6n6l, .viewerBadge_container__176p1, #MainMenu {
        display: none !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    .stApp { margin-top: 0px !important; }
    /* 1. 메인 컨테이너 자체를 더 위로 끌어올림 */
    [data-testid="stMainViewContainer"] {
        margin-top: -60px !important; /* -45에서 -60으로 더 키워보세요 */
    }

    /* 2. 내부 콘텐츠 박스의 위쪽 여백을 강제로 '마이너스' 처리 */
    .block-container { 
        padding-top: 0rem !important; 
        margin-top: -36px !important; /* 이 코드를 추가해서 내용물을 강제로 위로 붙입니다 */
        padding-bottom: 0rem !important; 
    }

    /* 3. 제목의 기본 마진 제거 */
    h2 {
        margin-top: 0px !important;
        padding-top: 0px !important;
    }

    /* 2. 초기화 X 버튼 (원형 고정) */
    /* col_clear(3번째 컬럼)에 있는 버튼만 집어서 원형으로 만듭니다 */
    div[data-testid="column"]:nth-of-type(3) button {
        background-color: #333333 !important;
        color: white !important;
        border-radius: 50% !important; /* 원형 */
        width: 40px !important;        /* 가로 고정 */
        height: 40px !important;       /* 세로 고정 */
        padding: 0 !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. 더보기 버튼 (글자 길이에 맞춰 늘어나는 타원형) */
    div.stVerticalBlock > div.stButton > button {
        background-color: #333333 !important; 
        color: white !important;
        border-radius: 20px !important;
        width: auto !important;
        padding: 8px 25px !important;
        margin: 20px auto !important; 
        display: flex !important;
        border: 1px solid #464855 !important;
        height: auto !important;
    }


    /* 4. 모든 버튼 공통 호버 효과 */
    div.stButton > button:hover {
        background-color: #000000 !important;
        border-color: #ff4b4b !important;
        color: white !important;
    }

    /* 위로 가기 버튼 스타일 */
    .top-btn { 
        position: fixed; bottom: 80px; right: 30px; z-index: 999; 
        background: white; border: 2px solid black; border-radius: 50%; 
        width: 50px; height: 50px; display: flex; align-items: center; 
        justify-content: center; text-decoration: none; color: black !important; 
        font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); 
    }
    .top-btn:hover { background-color: #f0f2f6; }
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
        **
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 16px; margin-bottom: 10px; opacity: 0.2;'>", unsafe_allow_html=True)

# 5. 데이터 검색 및 출력 로직
conn = get_connection()
if conn:
    if 'load_count' not in st.session_state:
        st.session_state.load_count = 100

    conditions = ['"판매상태" NOT IN ("숨김", "품절")']

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
            for i, row in df.iterrows(): # i를 인덱스로 활용
                target_url = row['상품URL']
                img_url = row['대표이미지URL'] if row.get('대표이미지URL') else ""
                reg_date = row.get('등록일', '-') 

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
                            <div style="flex: 4; display: flex; flex-direction: column; justify-content: center;">
                                <h5 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: inherit; line-height: 1.2;">
                                    {row['상품명']}
                                </h5>
                                <p style="margin: 0px 0 0px 0; padding-left: 0px; font-size: 12px; opacity: 0.8; color: inherit;">
                                    등록일: {reg_date}
                                </p>
                                <p style="margin: 0; font-size: 13.5px; opacity: 0.7; color: inherit;">
                                    {row['원산지']}
                                </p>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            # 4. 더보기 버튼 (수정된 디자인 적용됨)
            if total_count > st.session_state.load_count:
                # 텍스트에 이모지를 포함하면 이미지처럼 글자 길이에 맞춰 배경이 생깁니다.
                if st.button(f"🔽 더보기 ({st.session_state.load_count}/{total_count:,}) "):
                    st.session_state.load_count += 100
                    st.rerun()


    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
    
    conn.close()
