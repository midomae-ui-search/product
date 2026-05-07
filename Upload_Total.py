import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 처리 함수들 ---

def process_dates(df):
    """날짜 형식 통일 및 비어있는 값 처리"""
    if df.empty:
        return df
    # 모든 데이터를 문자열로 변환하고 양쪽 공백 제거
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    df.loc[df['브랜드'] == '', '브랜드'] = '미지정'
    
    # 날짜 데이터 처리 (2026-04-28, 2026-04 모두 대응)
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & (df['제조사'] != '날짜없음')
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'], format='%Y-%m', errors='coerce')
    return df

@st.cache_data
def load_from_db():
    """DB 파일 자동 로드"""
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            # 이미지에서 확인한 테이블명 '상품검색v4' 사용
            df = pd.read_sql_query("SELECT 제조사, 브랜드 FROM 상품검색v4", conn)
            conn.close()
            return process_dates(df)
        except Exception as e:
            st.error(f"DB 읽기 실패: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

@st.cache_data
def load_from_excel(file):
    """엑셀 파일 업로드 로드"""
    try:
        df = pd.read_excel(file, usecols=['제조사', '브랜드'], engine='calamine')
        return process_dates(df)
    except Exception as e:
        st.error(f"엑셀 읽기 실패: {e}")
        return pd.DataFrame()

# --- 2. 메인 화면 구성 ---

st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 업로드 수량 통합 집계")

# 데이터 소스 선택
data_source = st.radio(
    "데이터 소스를 선택하세요",
    ("기본 데이터베이스 (자동)", "직접 엑셀 업로드"),
    horizontal=True
)

# [중요] df를 빈 상자로 먼저 선언해서 NameError 방지
df = pd.DataFrame()

if data_source == "기본 데이터베이스 (자동)":
    df = load_from_db()
    if df.empty:
        st.warning("데이터베이스를 불러올 수 없습니다. 파일명을 확인해주세요.")
else:
    uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])
    if uploaded_file:
        df = load_from_excel(uploaded_file)

# --- 3. 필터 및 결과 출력 (df가 비어있지 않을 때만 실행) ---

if not df.empty:
    st.sidebar.header("🔍 조건 설정")
    
    # 유효한 날짜가 있는지 확인
    valid_dates = df['제조사_일자'].dropna()
    
    if not valid_dates.empty:
        min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
        
        selected_range = st.sidebar.date_input(
            "📅 조회 기간 선택",
            value=(min_d, max_d),
            min_value=min_d,
            max_value=max_d,
            format="YYYY/MM/DD"
        )

        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            mask = (
                (df['제조사_일자'].dt.date >= start_date) & 
                (df['제조사_일자'].dt.date <= end_date) & 
                (df['브랜드'].isin(selected_brands))
            )
            filtered_df = df.loc[mask]

            # 최종 결과 표시
            st.divider()
            st.markdown(f"### 🚩 {start_date} ~ {end_date} 결과")
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
        st.error("조회 가능한 날짜 데이터가 없습니다.")
else:
    if data_source == "직접 엑셀 업로드":
        st.info("파일을 업로드하면 집계 결과가 나타납니다.")
