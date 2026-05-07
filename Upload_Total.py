import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 처리 핵심 함수 (강력한 날짜 변환 포함) ---
def process_data(df):
    if df.empty: return df
    
    df.columns = [c.strip() for c in df.columns]
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    # [날짜 변환] 2026-01 같은 월 단위 데이터도 1일로 인식
    def force_to_date(val):
        if val == '날짜없음': return pd.NaT
        val = val.replace('.', '-').replace('/', '-')
        try:
            return pd.to_datetime(val).date()
        except:
            try:
                return pd.to_datetime(val, format='%Y-%m').date()
            except:
                return pd.NaT

    df['제조사_일자'] = pd.to_datetime(df['제조사'].apply(force_to_date))
    return df

# --- 2. 데이터 로드 함수들 ---
# [수정] 캐시 이름을 바꿔서 이전 캐시와 충돌을 방지합니다.
@st.cache_data(show_spinner="데이터베이스 연결 중...")
def load_from_db_v2():
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        try:
            # 1. DB 연결 (타임아웃 설정 추가로 안정성 확보)
            conn = sqlite3.connect(db_file, timeout=10)
            
            # 2. 테이블명 확인 (이미지에서 확인된 '상품검색v4' 사용)
            # 테이블명이 다를 경우를 대비해 첫 번째 테이블을 자동으로 찾는 안전장치 유지
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if not tables.empty:
                t_name = tables['name'].iloc[0]
                df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                conn.close()
                return process_data(df)
            conn.close()
        except Exception as e:
            st.error(f"⚠️ DB를 읽는 중 오류가 발생했습니다: {e}")
    else:
        st.error(f"⚠️ '{db_file}' 파일을 찾을 수 없습니다. 깃허브 저장소를 확인해주세요.")
    return pd.DataFrame()

# --- 메인 화면 로직 부분 ---
if data_source == "저장소 데이터 자동 로드":
    df = load_from_db_v2() # 업데이트된 함수 호출
    if df.empty:
        st.info("데이터를 불러오는 중이거나 파일이 비어있습니다.")

else:
    u_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])
    if u_file:
        if u_file.name.endswith('.csv'):
            try: temp_df = pd.read_csv(u_file, encoding='utf-8-sig')
            except: temp_df = pd.read_csv(u_file, encoding='cp949')
        else:
            temp_df = pd.read_excel(u_file, engine='calamine')
        df = process_data(temp_df)
        st.success(f"✅ 업로드한 파일({u_file.name})을 분석 중입니다.")

# --- 4. 필터 및 결과 출력 ---
if not df.empty:
    st.sidebar.header("🔍 필터 설정")
    valid_df = df.dropna(subset=['제조사_일자'])
    
    if not valid_df.empty:
        min_d = valid_df['제조사_일자'].min().date()
        max_d = valid_df['제조사_일자'].max().date()
        
        selected_range = st.sidebar.date_input("📅 조회 기간", value=(min_d, max_d), format="YYYY/MM/DD")
        
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 브랜드 선택", all_brands, default=all_brands)

        if len(selected_range) == 2:
            start, end = selected_range
            mask = (df['제조사_일자'].dt.date >= start) & (df['제조사_일자'].dt.date <= end) & (df['브랜드'].isin(selected_brands))
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
