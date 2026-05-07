import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 처리 핵심 함수 ---
def process_data(df):
    if df.empty: return df
    df.columns = [c.strip() for c in df.columns]
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    def force_to_date(val):
        if val == '날짜없음': return pd.NaT
        val = val.replace('.', '-').replace('/', '-')
        try: return pd.to_datetime(val).date()
        except:
            try: return pd.to_datetime(val, format='%Y-%m').date()
            except: return pd.NaT

    df['제조사_일자'] = pd.to_datetime(df['제조사'].apply(force_to_date))
    return df

# --- 2. 데이터 로드 함수 (캐시 적용) ---
@st.cache_data(show_spinner="데이터 로딩 중...")
def load_from_db():
    db_file = '상품검색 V4.db'
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            if not tables.empty:
                t_name = tables['name'].iloc[0]
                df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                conn.close()
                return process_data(df)
            conn.close()
        except Exception as e:
            st.error(f"DB 오류: {e}")
    return pd.DataFrame()

# --- 3. 메인 화면 구성 (순서 중요!) ---
st.set_page_config(page_title="통합 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

# [해결포인트] 변수를 먼저 선언합니다.
data_source = st.radio(
    "📂 데이터 확인 방식을 선택하세요",
    ("저장소 데이터 자동 로드", "수기로 직접 파일 업로드"),
    horizontal=True
)

# df 상자를 미리 준비합니다.
df = pd.DataFrame()

# 이제 선택된 방식에 따라 데이터를 담습니다.
if data_source == "저장소 데이터 자동 로드":
    df = load_from_db()
else:
    u_file = st.file_uploader("엑셀 또는 CSV 파일을 업로드하세요", type=["xlsx", "csv"])
    if u_file:
        if u_file.name.endswith('.csv'):
            try: temp_df = pd.read_csv(u_file, encoding='utf-8-sig')
            except: temp_df = pd.read_csv(u_file, encoding='cp949')
        else:
            temp_df = pd.read_excel(u_file, engine='calamine')
        df = process_data(temp_df)

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
    else:
        st.warning("유효한 날짜 데이터가 없습니다.")
elif data_source == "수기로 직접 파일 업로드":
    st.info("파일을 업로드하면 집계 결과가 나타납니다.")
