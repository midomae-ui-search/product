import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 처리 핵심 함수 ---
def process_data(df):
    if df.empty: return df
    # 컬럼명 앞뒤 공백 제거
    df.columns = [c.strip() for c in df.columns]
    
    # '제조사', '브랜드' 열 이름 통일
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    # 빈 값 처리
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    # 날짜 변환 로직 (2026-05-07, 2026-05 등 모두 대응)
    def force_to_date(val):
        if val == '날짜없음': return pd.NaT
        # 기호 통일
        val = val.replace('.', '-').replace('/', '-')
        try:
            # 1순위: 일자까지 있는 경우 (2026-05-07)
            return pd.to_datetime(val).date()
        except:
            try:
                # 2순위: 월만 있는 경우 (2026-05 -> 2026-05-01로 변환)
                return pd.to_datetime(val, format='%Y-%m').date()
            except:
                return pd.NaT

    df['제조사_일자'] = pd.to_datetime(df['제조사'].apply(force_to_date))
    return df

# --- 2. 기본 데이터 로드 (DB) ---
@st.cache_data(show_spinner="기본 데이터를 불러오는 중...")
def load_default_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_file = os.path.join(current_dir, '상품검색 V4.db')
    
    if not os.path.exists(db_file):
        db_file = '상품검색 V4.db'

    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if not tables.empty:
                t_names = tables['name'].tolist()
                # 이미지상 테이블명인 '상품검색v4' 우선 조회
                t_name = '상품검색v4' if '상품검색v4' in t_names else t_names[0]
                
                df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                conn.close()
                return process_data(df)
            conn.close()
        except Exception as e:
            st.error(f"데이터베이스 읽기 중 오류: {e}")
    return pd.DataFrame()

# --- 3. 메인 화면 구성 ---
st.set_page_config(page_title="업로드 수량 집계", layout="centered")
st.title("📊 업로드 수량 집계")

# 사이드바 구성
st.sidebar.markdown("### ⚙️ 시스템 설정")
# [추가] 새로운 DB 반영을 위한 새로고침 버튼
if st.sidebar.button("🔄 데이터 최신화 (새로고침)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📥 수기 파일 업로드")
uploaded_file = st.sidebar.file_uploader("새로운 엑셀/CSV 업로드", type=["xlsx", "csv"])

# 데이터 로드 결정 로직
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        try: raw_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: raw_df = pd.read_csv(uploaded_file, encoding='cp949')
    else:
        # requirements.txt에 python-calamine이 있을 때만 engine 사용 가능
        try:
            raw_df = pd.read_excel(uploaded_file, engine='calamine')
        except:
            raw_df = pd.read_excel(uploaded_file)
            
    df = process_data(raw_df)
    st.info(f"📂 업로드된 파일({uploaded_file.name})로 분석 중입니다.")
else:
    df = load_default_db()
    if not df.empty:
        st.success("✅ 저장소 기본 데이터를 불러왔습니다.")
    else:
        st.warning("⚠️ 저장소에서 기본 데이터 파일을 찾을 수 없습니다.")

# --- 4. 필터 및 결과 출력 ---
if not df.empty:
    st.sidebar.divider()
    st.sidebar.header("🔍 필터 설정")
    valid_df = df.dropna(subset=['제조사_일자'])
    
    if not valid_df.empty:
        # 데이터에 기반한 자동 날짜 범위 설정
        min_d = valid_df['제조사_일자'].min().date()
        max_d = valid_df['제조사_일자'].max().date()
        
        selected_range = st.sidebar.date_input(
            "📅 조회 기간", 
            value=(min_d, max_d), 
            format="YYYY/MM/DD"
        )
        
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 직원 선택", all_brands, default=all_brands)

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            mask = (df['제조사_일자'].dt.date >= start) & \
                   (df['제조사_일자'].dt.date <= end) & \
                   (df['브랜드'].isin(selected_brands))
            f_df = df.loc[mask]

            st.divider()
            st.subheader(f"총 업로드 수: **{len(f_df):,} 개**")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜별 수량**")
                # 실제 기록된 텍스트(제조사) 기준으로 요약 표 생성
                st.table(f_df['제조사'].value_counts().sort_index().rename("수량"))
            with c2:
                st.write("👤 **직원별 수량**")
                st.table(f_df['브랜드'].value_counts().rename("수량"))
    else:
        st.error("데이터 내에 유효한 날짜 형식이 없습니다.")
