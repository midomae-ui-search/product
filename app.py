import os
import sqlite3
import zipfile  # 💡 [추가] 압축을 풀기 위한 파이썬 기본 내장 라이브러리
import pandas as pd
import streamlit as st

DB_FILE = '상품검색 V4.db'
ZIP_FILE = '상품검색 V4.zip'

# =========================================================
# [압축 우회 방식] 내장된 ZIP 파일 압축 해제 및 연결 로직
# =========================================================
def get_connection():
    try:
        # 💡 [핵심 개선] ZIP 파일과 DB 파일의 수정 시간을 비교하여 자동 업데이트 유도
        if os.path.exists(ZIP_FILE):
            zip_time = os.path.getmtime(ZIP_FILE)   # ZIP 파일의 최근 수정 시간
            db_time = os.path.getmtime(DB_FILE) if os.path.exists(DB_FILE) else 0
            
            # 가짜 파일 방지 (50MB 미만) 또는 ZIP 파일이 DB 파일보다 최신인 경우
            if os.path.exists(DB_FILE):
                is_too_small = os.path.getsize(DB_FILE) < 1024 * 1024 * 50
                is_new_zip_uploaded = zip_time > db_time
                
                if is_too_small or is_new_zip_uploaded:
                    os.remove(DB_FILE)  # 기존 구버전/가짜 DB 완전히 삭제
                    
        # DB 파일이 삭제되었거나 없는 경우 새로운 ZIP의 압축을 해제합니다.
        if not os.path.exists(DB_FILE) and os.path.exists(ZIP_FILE):
            with zipfile.ZipFile(ZIP_FILE, 'r') as zip_ref:
                zip_ref.extractall('.')
                
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Exception as e:
        st.error(f"❌ 데이터베이스 연결 및 압축 해제 실패: {e}")
        return None

# =========================================================
# 1. 페이지 설정 및 디자인 적용
# =========================================================
st.set_page_config(page_title="상품 검색기", layout="wide")

st.markdown("""
    <style>
    header, footer {visibility: hidden !important; display: none !important;}
    .stAppDeployButton, .viewerBadge_link__q6n6l, .viewerBadge_container__176p1, #MainMenu {
        display: none !important;
    }
    [data-testid="stToolbar"] { display: none !important; }
    .stApp { margin-top: 0px !important; }
    
    [data-testid="stMainViewContainer"] { margin-top: -60px !important; }
    .block-container { padding-top: 0rem !important; margin-top: -36px !important; padding-bottom: 0rem !important; }
    h2 { margin-top: 0px !important; padding-top: 0px !important; }

    [data-testid="column"] { flex: 1 1 0% !important; min-width: 0px !important; padding-right: 5px !important; }
    [data-testid="column"]:nth-of-type(1) { padding-right: 10px !important; }
    div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label { display: none !important; }
    div[data-testid="stButton"] { margin-top: 0px !important; display: flex !important; justify-content: center !important; }
    .stButton button { width: auto !important; padding: 2px 10px !important; font-size: 12px !important; }

    div[data-testid="column"]:nth-of-type(3) button {
        background-color: #333333 !important; color: white !important; border-radius: 50% !important;
        width: 40px !important; height: 40px !important; padding: 0 !important; border: none !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }

    div.stVerticalBlock > div.stButton > button {
        background-color: #333333 !important; color: white !important; border-radius: 20px !important;
        width: auto !important; padding: 8px 25px !important; margin: 20px auto !important; 
        display: flex !important; border: 1px solid #464855 !important; height: auto !important;
    }

    div.stButton > button:hover { background-color: #000000 !important; border-color: #ff4b4b !important; color: white !important; }

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

st.markdown('<div id="top"></div>', unsafe_allow_html=True)
st.markdown('<a class="top-btn" href="#top">↑</a>', unsafe_allow_html=True)

TABLE_NAME = '"상품검색v4"' 

category_data = {
    "전체": "ALL", "국내배송": "CATE118", "국내배송 특가 ~70%": "CATE128", "현지오늘배송": "CATE119", "개런티": "CATE117", "H1": "CATE72", "H2": "CATE73", "H3": "CATE74", 
    "CC 넘버원": "CATE75", "CC 티무역": "CATE76", "CC 팬더": "CATE77", "CC 나비/기타": "CATE78", "CC 일반": "CATE80",
    "[고퀄]기타 브랜드": "CATE79", "PD": "CATE84", "LV": "CATE85", "CD": "CATE86", "CL": "CATE87", "GY": "CATE88", 
    "LP": "CATE89", "BV": "CATE90", "MIU": "CATE91", "YSL": "CATE92", "DV": "CATE93", "THE ROW": "CATE116", 
    "GG": "CATE95", "FF": "CATE94", "BL": "CATE97", "BBR": "BBR", "LW": "CATE100", "VT": "CATE99", "CHL": "CATE96", 
    "BAOBAO": "CATE101", "기타브랜드": "CATE102", "여행구/캐리어": "CATE103", "여성 의류": "CATE47", "바람막이/경량": "CATE48", 
    "여성패딩(겨울용)": "CATE66", "코트/퍼/무스탕(겨울용)": "CATE129", "맨즈 의류": "CATE68", "맨즈 아우터": "CATE69", 
    "키즈의류": "CATE130", "키즈 아우터": "CATE131", "여성 신발": "CATE105", "[수공]H 신발": "CATE106", "[수공]CC 신발": "CATE107", 
    "[수공]기타 신발": "CATE108", "남성 신발": "CATE109", "[수공]남성 신발": "CATE110", "키즈 신발": "CATE111", 
    "시계": "CATE113", "시계정보": "CATE114", "악세서리": "CATE125", "18K 금 제작": "CATE126", "지갑": "CATE115", 
    "모자": "CATE134", "스카프/머플러": "CATE127", "선글라스/안경": "CATE133", "기타잡화/소품": "CATE135", "여성 벨트": "CATE136", 
    "맨즈 벨트/잡화": "CATE139"
}

st.markdown("<h2 style='font-size: 24px; margin-bottom: -5px;'>🔍 상품 검색기</h2>", unsafe_allow_html=True)

if "keyword_val" not in st.session_state:
    st.session_state.keyword_val = ""

def clear_search():
    st.session_state.keyword_val = ""

col_cat, col_keyword, col_clear = st.columns([1, 2.2, 0.5], gap="small")

with col_cat:
    selected_name = st.selectbox("카테고리", list(category_data.keys()), label_visibility="collapsed")
    selected_code = category_data[selected_name]

with col_keyword:
    keyword = st.text_input("검색어", placeholder="검색어 입력", key="keyword_val", label_visibility="collapsed")

with col_clear:
    st.button("X", on_click=clear_search)

st.markdown("""
    <div style="text-align: center; color: #ff4b4b; font-weight: bold; font-size: 17.5px;">
        ** 6/8 ~ 6/12 악세서리/시계 10% 할인
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin-top: 16px; margin-bottom: 10px; opacity: 0.2;'>", unsafe_allow_html=True)

conn = get_connection()
if conn:
    if 'load_count' not in st.session_state:
        st.session_state.load_count = 100

    conditions = ['"판매상태" NOT IN ("숨김", "품절")']

    if keyword:
        if keyword.startswith("#"):
            brand_k = keyword[1:].strip()
            if brand_k:
                conditions.append(f'"브랜드" LIKE "%{brand_k}%"')
        else:
            k_list = keyword.split()
            k_cond = " AND ".join([f'("상품명" LIKE "%{k}%" OR "원산지" LIKE "%{k}%")' for k in k_list])
            conditions.append(f"({k_cond})")
        
    if selected_code != 'ALL':
        conditions.append(f'"카테고리ID" LIKE "%{selected_code}%"')

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    try:
        count_query = f'SELECT COUNT(*) FROM {TABLE_NAME} {where_clause}'
        total_count = pd.read_sql(count_query, conn).iloc[0, 0] # 💡 완벽 연동 복구 완료

        query = f'SELECT * FROM {TABLE_NAME} {where_clause} LIMIT {st.session_state.load_count}'
        df = pd.read_sql(query, conn)

        if total_count > 0:
            st.markdown(f"""
                <div style="
                    background-color: #31333F;
                    padding: 5px 10px;
                    border-radius: 8px;
                    font-size: 14px;
                    margin-top: -25px;
                    margin-bottom: 0px;
                    color: #FFFFFF;
                ">
                    ✅ <b>{selected_name}</b> 검색 결과: <b>{total_count:,}</b>건
                </div>
            """, unsafe_allow_html=True)
    
            for i, row in df.iterrows():
                target_url = row['상품URL']
                img_url = row['대표이미지URL'] if row.get('대표이미지URL') else ""
                manufacturer = row.get('제조사', '-')
                brand = row.get('브랜드', '-')

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
                                <div style="margin: 0px 0; font-size: 13.5px; display: flex; gap: 10px; opacity: 0.7;">
                                    <span style="color: inherit;">{brand}</span>
                                    <span style="color: gray;">|</span>
                                    <span>{manufacturer}</span>
                                </div>
                                <p style="margin: 0; font-size: 13.5px; opacity: 0.7; color: inherit;">
                                    {row['원산지']}
                                </p>
                            </div>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

            if total_count > st.session_state.load_count:
                if st.button(f"🔽 더보기 ({st.session_state.load_count}/{total_count:,}) "):
                    st.session_state.load_count += 100
                    st.rerun()
        else:
            st.info("🔍 검색 조건에 맞는 상품이 존재하지 않습니다.")

    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
    
    conn.close()
