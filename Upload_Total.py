import streamlit as st
import pandas as pd
import sqlite3
import os

@st.cache_data
def load_from_db():
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        try:
            # 이미지에서 확인된 정확한 테이블명 '상품검색v4' 사용
            df = pd.read_sql_query("SELECT 제조사, 브랜드 FROM 상품검색v4", conn)
            conn.close()
            
            # [해결 핵심 1] 데이터 청소: '브랜드'나 '제조사'가 비어있는 행 처리
            df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
            df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
            
            # 비어있는 문자열도 '미지정'으로 통일
            df.loc[df['브랜드'] == '', '브랜드'] = '미지정'
            
            return process_dates(df)
        except Exception as e:
            st.error(f"DB 읽기 오류: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

def process_dates(df):
    # 날짜 처리 (2026-04, 2026-04-28 모두 대응)
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & (df['제조사'] != '날짜없음')
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'], format='%Y-%m', errors='coerce')
    return df

# --- 이하 화면 구성 코드는 동일 ---
st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 업로드 수량 통합 집계")

# (방식 선택 라디오 버튼 및 데이터 로드 로직...)
# 위 소스에서 df를 가져온 후 필터 부분:

# [해결 핵심 2] 필터 선택지에서 에러 방지 (dropna 사용)
if not df.empty:
    st.sidebar.header("🔍 조건 설정")
    valid_dates = df['제조사_일자'].dropna()
    
    if not valid_dates.empty:
        # 달력 및 브랜드 필터 출력...
        all_brands = sorted(df['브랜드'].unique()) # 이제 모든 데이터가 문자열이라 에러 안 남
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)
        # (이후 필터링 및 st.table 출력 로직 그대로 사용)
