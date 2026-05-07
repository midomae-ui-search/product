import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 처리 핵심 함수 ---
def process_data(df):
    if df.empty: return df
    
    # 컬럼명 공백 제거 및 이름 통일
    df.columns = [c.strip() for c in df.columns]
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    # 기본 청소
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    # [날짜 변환 최강화] 어떤 형식이든 1일로 변환
    def force_to_date(val):
        if val == '날짜없음': return pd.NaT
        # 기호 통일 (2026.01 -> 2026-01)
        val = val.replace('.', '-').replace('/', '-')
        try:
            # 2026-01-28 같은 일자형 시도
            return pd.to_datetime(val).date()
        except:
            try:
                # 2026-01 같은 월형 시도 (자동으로 1일이 됨)
                return pd.to_datetime(val, format='%Y-%m').date()
            except:
                return pd.NaT

    df['제조사_일자'] = df['제조사'].apply(force_to_date)
    # datetime 형식으로 한 번 더 변환 (필터링용)
    df['제조사_일자'] = pd.to_datetime(df['제조사_일자'])
    
    return df

# --- 2. DB 로드 함수 ---
@st.cache_data
def load_from_db():
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            # 모든 데이터(*)를 다 가져오도록 수정
            df = pd.read_sql_query("SELECT * FROM `상품검색v4`", conn)
            conn.close()
            return process_data(df)
        except Exception as e:
            st.error(f"DB 읽기 오류: {e}")
    return pd.DataFrame()

# --- 3. 메인 화면 ---
st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

df = load_from_db()

if not df.empty:
    st.sidebar.header("🔍 필터 설정")
    
    # 날짜가 있는 데이터만 필터링 대상으로 삼음
    valid_df = df.dropna(subset=['제조사_일자'])
    
    if not valid_df.empty:
        # 달력의 최소/최대 범위를 실제 데이터에 맞게 자동 설정
        min_date = valid_df['제조사_일자'].min().date()
        max_date = valid_df['제조사_일자'].max().date()
        
        selected_range = st.sidebar.date_input(
            "📅 조회 기간",
            value=(min_date, max_date), # 처음 열 때 전체 기간이 잡히게 설정
            format="YYYY/MM/DD"
        )
        
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start_date, end_date = selected_range
            
            # 필터 적용
            mask = (df['제조사_일자'].dt.date >= start_date) & \
                   (df['제조사_일자'].dt.date <= end_date) & \
                   (df['브랜드'].isin(selected_brands))
            f_df = df.loc[mask]

            st.divider()
            st.subheader(f"총 업로드 수: **{len(f_df):,} 개**")
            
            # 요약 표 출력
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜/월별 수량**")
                # 제조사(원본글자) 기준으로 집계하여 2026-01 등이 그대로 보이게 함
                st.table(f_df['제조사'].value_counts().sort_index().rename("수량"))
            with c2:
                st.write("👤 **브랜드별 수량**")
                st.table(f_df['브랜드'].value_counts().rename("수량"))
    else:
        st.warning("데이터는 있으나 유효한 날짜 형식이 없습니다.")
else:
    st.error("데이터를 불러오지 못했습니다. 파일명을 확인해주세요.")
