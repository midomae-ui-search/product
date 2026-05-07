import streamlit as st
import pandas as pd
import sqlite3
import os
import glob

# --- 1. 데이터 통합 처리 함수 ---
def process_data(df):
    if df.empty: return df
    # 컬럼명 공백 제거
    df.columns = [c.strip() for c in df.columns]
    
    # '제조사', '브랜드' 열 찾기 (유연한 대응)
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    # 데이터 청소
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    # 날짜 처리
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & (df['제조사'] != '날짜없음')
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'], format='%Y-%m', errors='coerce')
    
    return df[['제조사', '브랜드', '제조사_일자']]

# --- 2. 만능 파일 자동 로드 함수 ---
@st.cache_data
def auto_load_data():
    search_pattern = "*상품검색*"
    files = glob.glob(search_pattern + ".*")
    
    if not files:
        return pd.DataFrame()

    # 가장 최근 파일 선택
    target_file = max(files, key=os.path.getmtime)
    ext = os.path.splitext(target_file).lower()

    try:
        if ext == '.db':
            conn = sqlite3.connect(target_file)
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if tables_df.empty:
                conn.close()
                return pd.DataFrame()
            
            # 첫 번째 테이블 이름을 가져와서 읽기 (백틱 처리로 특수문자 대응)
            table_name = tables_df['name'].iloc[0]
            df = pd.read_sql_query(f"SELECT * FROM `{table_name}`", conn)
            conn.close()
            return process_data(df)
        
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(target_file, engine='calamine')
            return process_data(df)
        
        elif ext == '.csv':
            try:
                df = pd.read_csv(target_file, encoding='utf-8-sig')
            except:
                df = pd.read_csv(target_file, encoding='cp949')
            return process_data(df)
            
    except Exception as e:
        st.error(f"파일({target_file}) 로드 중 오류: {e}")
        return pd.DataFrame()
    
    return pd.DataFrame()

# --- 3. 메인 화면 구성 ---
st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

# 찾은 파일 목록 표시
found_files = glob.glob("*상품검색*.*")
if found_files:
    st.caption(f"🔎 현재 감지된 파일: {', '.join(found_files)}")

data_source = st.radio("데이터 소스 선택", ("저장소 파일 자동 로드", "직접 파일 업로드"), horizontal=True)

df = pd.DataFrame()

if data_source == "저장소 파일 자동 로드":
    df = auto_load_data()
    if df.empty:
        st.warning("저장소에 '상품검색' 관련 파일이 없거나 내부 데이터가 비어있습니다.")
else:
    u_file = st.file_uploader("파일을 업로드하세요", type=["xlsx", "csv"])
    if u_file:
        if u_file.name.endswith('.csv'):
            try: df = pd.read_csv(u_file, encoding='utf-8-sig')
            except: df = pd.read_csv(u_file, encoding='cp949')
        else:
            df = pd.read_excel(u_file, engine='calamine')
        df = process_data(df)

# --- 4. 필터 및 결과 출력 ---
if not df.empty:
    st.sidebar.header("🔍 조건 설정")
    valid_dates = df['제조사_일자'].dropna()
    
    if not valid_dates.empty:
        min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
        selected_range = st.sidebar.date_input("📅 조회 기간", value=(min_d, max_d), format="YYYY/MM/DD")
        
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            mask = (df['제조사_일자'].dt.date >= start_date) & \
                   (df['제조사_일자'].dt.date <= end_date) & \
                   (df['브랜드'].isin(selected_brands))
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
