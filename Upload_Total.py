import streamlit as st
import pandas as pd
import sqlite3
import os
import glob

# --- 1. 데이터 통합 처리 함수 (동일) ---
def process_data(df):
    if df.empty: return df
    df.columns = [c.strip() for c in df.columns]
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & (df['제조사'] != '날짜없음')
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'], format='%Y-%m', errors='coerce')
    return df[['제조사', '브랜드', '제조사_일자']]

# --- 2. [강력수정] 이름이 비슷하면 무조건 읽어오는 함수 ---
@st.cache_data
def auto_load_data():
    # '상품검색'이라는 글자가 포함된 모든 파일을 찾습니다.
    search_pattern = "*상품검색*"
    files = glob.glob(search_pattern + ".*")
    
    if not files:
        return pd.DataFrame()

    # 찾은 파일 중 가장 최근에 수정된 파일 하나를 선택합니다.
    target_file = max(files, key=os.path.getmtime)
    ext = os.path.splitext(target_file)[1].lower()

    try:
        # 1. DB 파일일 때
        if ext == '.db':
            conn = sqlite3.connect(target_file)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            table = tables.iloc[0, 0] # 첫 번째 테이블
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            conn.close()
            return process_data(df)
        
        # 2. 엑셀 파일일 때
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(target_file, engine='calamine')
            return process_data(df)
        
        # 3. CSV 파일일 때
        elif ext == '.csv':
            try:
                df = pd.read_csv(target_file, encoding='utf-8-sig')
            except:
                df = pd.read_csv(target_file, encoding='cp949')
            return process_data(df)
    except Exception as e:
        st.error(f"파일({target_file}) 읽기 오류: {e}")
        return pd.DataFrame()
    
    return pd.DataFrame()

# --- 3. 메인 화면 ---
st.set_page_config(page_title="만능 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

# 어떤 파일을 찾았는지 화면에 작게 표시해줍니다 (확인용)
found_files = glob.glob("*상품검색*.*")
if found_files:
    st.caption(f"🔎 찾은 파일: {', '.join(found_files)}")
else:
    st.caption("🔎 저장소에서 '상품검색' 관련 파일을 찾지 못했습니다.")

data_source = st.radio("데이터 소스 선택", ("저장소 파일 자동 로드", "직접 파일 업로드"), horizontal=True)

df = pd.DataFrame()

if data_source == "저장소 파일 자동 로드":
    df = auto_load_data()
    if df.empty:
        st.warning("저장소에 '상품검색'이라는 이름이 포함된 파일(db, xlsx, csv)이 없습니다.")
else:
    u_file = st.file_uploader("파일을 업로드하세요", type=["xlsx", "csv"])
    if u_file:
        if u_file.name.endswith('.csv'):
            try: df = pd.read_csv(u_file, encoding='utf-8-sig')
            except: df = pd.read_csv(u_file, encoding='cp949')
        else:
            df = pd.read_excel(u_file, engine='calamine')
        df = process_data(df)

# --- 4. 필터 및 결과 (기존 코드 사용) ---
if not df.empty:
    st.sidebar.header("🔍 조건 설정")
    valid_dates = df['제조사_일자'].dropna()
    if not valid_dates.empty:
        min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
        selected_range = st.sidebar.date_input("📅 조회 기간", value=(min_d, max_d), format="YYYY/MM/DD")
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 브랜드", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            mask = (df['제조사_일자'].dt.date >= start_date) & (df['제조사_일자'].dt.date <= end_date) & (df['브랜드'].isin(selected_brands))
            f_df = df.loc[mask]

            st.divider()
            st.subheader(f"총 업로드 수: **{len(f_df):,} 개**")
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜/월별**")
                st.table(f_df['제조사'].value_counts().sort_index().rename("수량"))
            with c2:
                st.write("👤 **브랜드별**")
                st.table(f_df['브랜드'].value_counts().rename("수량"))
