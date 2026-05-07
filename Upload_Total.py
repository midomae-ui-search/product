import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 통합 처리 함수 ---
def process_data(df):
    if df.empty: return df
    df.columns = [c.strip() for c in df.columns]
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    return df

# --- 2. 자동 로드 함수 ---
@st.cache_data
def auto_load_data():
    # 깃허브 저장소에서 '상품검색 V4.db' 파일을 직접 지목합니다.
    db_file = '상품검색 V4.db'
    
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            # 모든 테이블 목록 확인
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if not tables.empty:
                t_name = tables['name'].iloc[0] # 첫 번째 테이블명 추출
                df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                conn.close()
                return process_data(df)
            conn.close()
        except Exception as e:
            st.error(f"DB 파일 읽기 오류: {e}")
    return pd.DataFrame()

# --- 3. 메인 화면 ---
st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

# 자동 로드 시도
df = auto_load_data()

if not df.empty:
    st.success("✅ 저장소의 데이터를 성공적으로 불러왔습니다.")
    
    st.sidebar.header("🔍 필터 설정")
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
                st.write("📅 **날짜/월별 수량**")
                st.table(f_df['제조사'].value_counts().sort_index().rename("수량"))
            with c2:
                st.write("👤 **브랜드별 수량**")
                st.table(f_df['브랜드'].value_counts().rename("수량"))
else:
    st.warning("저장소에서 '상품검색 V4.db' 파일을 찾을 수 없거나 데이터가 비어있습니다.")
