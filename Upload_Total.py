import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 데이터 로드 함수 정의 ---

@st.cache_data
def load_from_db():
    """깃허브의 DB 파일로부터 데이터를 자동으로 읽어옴"""
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        # 테이블 이름을 모르실 경우 전체 데이터를 가져오도록 처리 (테이블명이 다르면 'product' 수정)
        try:
            df = pd.read_sql_query("SELECT 제조사, 브랜드 FROM product", conn)
        except:
            # 테이블명을 모를 때 첫 번째 테이블을 자동으로 가져오는 안전장치
            table_name = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn).iloc[0,0]
            df = pd.read_sql_query(f"SELECT 제조사, 브랜드 FROM {table_name}", conn)
        conn.close()
        return process_dates(df)
    return pd.DataFrame()

@st.cache_data
def load_from_excel(file):
    """사용자가 업로드한 엑셀 파일을 읽어옴"""
    df = pd.read_excel(file, usecols=['제조사', '브랜드'], engine='calamine')
    return process_dates(df)

def process_dates(df):
    """날짜 형식 통일 로직"""
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & df['제조사'].notna()
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'].astype(str), format='%Y-%m', errors='coerce')
    return df

# --- 메인 화면 구성 ---

st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 업로드 수량 통합 집계")

# 1. 데이터 소스 선택
data_source = st.radio(
    "데이터 소스를 선택하세요",
    ("기본 데이터베이스 (자동)", "직접 엑셀 업로드"),
    horizontal=True
)

df = pd.DataFrame()

if data_source == "기본 데이터베이스 (자동)":
    with st.spinner("DB 로딩 중..."):
        df = load_from_db()
    if df.empty:
        st.error("깃허브 저장소에서 '상품검색 V4.db' 파일을 찾을 수 없습니다.")
    else:
        st.success("✅ 깃허브 DB를 성공적으로 불러왔습니다.")

else:
    uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])
    if uploaded_file:
        df = load_from_excel(uploaded_file)

# --- 공통 필터 및 결과 화면 ---

if not df.empty:
    st.sidebar.header("🔍 조건 설정")
    
    valid_dates = df['제조사_일자'].dropna()
    if not valid_dates.empty:
        min_date, max_date = valid_dates.min().date(), valid_dates.max().date()
        
        selected_range = st.sidebar.date_input(
            "📅 조회 기간 선택",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            format="YYYY/MM/DD"
        )

        all_brands = sorted(df['브랜드'].unique().astype(str))
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            mask = (
                (df['제조사_일자'].dt.date >= start_date) & 
                (df['제조사_일자'].dt.date <= end_date) & 
                (df['브랜드'].astype(str).isin(selected_brands))
            )
            filtered_df = df.loc[mask]

            # 결과 출력 영역
            st.divider()
            st.markdown(f"### 🚩 {start_date} ~ {end_date} 집계 결과")
            st.subheader(f"총 업로드 수: **{len(filtered_df):,} 개**")
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.write("📅 **날짜/월별 수량**")
                st.table(filtered_df['제조사'].value_counts().sort_index().rename("수량"))
            with col2:
                st.write("👤 **브랜드별 수량**")
                st.table(filtered_df['브랜드'].value_counts().rename("수량"))
    else:
        st.warning("데이터에 유효한 날짜 정보가 없습니다.")
else:
    if data_source == "직접 엑셀 업로드":
        st.info("파일을 업로드하면 집계 결과가 나타납니다.")
