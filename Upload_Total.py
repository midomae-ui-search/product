import streamlit as st
import pandas as pd
import sqlite3
import os
import plotly.express as px  # 시각화를 위해 추가

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
        try:
            return pd.to_datetime(val).date()
        except:
            try:
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
                t_name = '상품검색v4' if '상품검색v4' in t_names else t_names[0]
                df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                conn.close()
                return process_data(df)
            conn.close()
        except Exception as e:
            st.error(f"데이터베이스 읽기 중 오류: {e}")
    return pd.DataFrame()

# --- 3. 메인 화면 구성 ---
st.set_page_config(page_title="업로드 수량 집계", layout="wide") # 그래프를 위해 넓게 설정
st.title("📊 업로드 수량 집계")

# 사이드바 구성
st.sidebar.markdown("### ⚙️ 시스템 설정")
if st.sidebar.button("🔄 데이터 최신화 (새로고침)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📥 수기 파일 업로드")
uploaded_file = st.sidebar.file_uploader("새로운 엑셀/CSV 업로드", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        try: raw_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: raw_df = pd.read_csv(uploaded_file, encoding='cp949')
    else:
        try: raw_df = pd.read_excel(uploaded_file, engine='calamine')
        except: raw_df = pd.read_excel(uploaded_file)
    df = process_data(raw_df)
    st.info(f"📂 업로드된 파일({uploaded_file.name}) 분석 중")
else:
    df = load_default_db()
    if not df.empty:
        st.success("✅ 기본 데이터를 불러왔습니다.")
    else:
        st.warning("⚠️ 데이터를 찾을 수 없습니다.")

# --- 4. 필터 및 결과 출력 ---
if not df.empty:
    st.sidebar.divider()
    st.sidebar.header("🔍 필터 설정")
    valid_df = df.dropna(subset=['제조사_일자'])
    
    if not valid_df.empty:
        min_d = valid_df['제조사_일자'].min().date()
        max_d = valid_df['제조사_일자'].max().date()
        
        selected_range = st.sidebar.date_input("📅 조회 기간", value=(min_d, max_d))
        all_brands = sorted(df['브랜드'].unique())
        selected_brands = st.sidebar.multiselect("👤 직원 선택", all_brands, default=all_brands)

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            mask = (df['제조사_일자'].dt.date >= start) & \
                   (df['제조사_일자'].dt.date <= end) & \
                   (df['브랜드'].isin(selected_brands))
            f_df = df.loc[mask]

            # 상단 지표
            st.subheader(f"✅ 필터 결과 총 업로드: **{len(f_df):,} 개**")
            
            # --- 5. 기간별 그래프 분석 (추가된 부분) ---
            st.divider()
            st.subheader("📈 기간별 업로드 추이")
            unit = st.segmented_control("분석 단위 선택", ["일별", "주별", "월별"], default="일별")
            
            chart_df = f_df.copy()
            if unit == "일별":
                plot_data = chart_df.groupby(chart_df['제조사_일자'].dt.date).size().reset_index(name='수량')
                x_col = '제조사_일자'
            elif unit == "주별":
                # 월요일 기준 주차
                chart_df['주차'] = chart_df['제조사_일자'].dt.to_period('W').apply(lambda r: r.start_time)
                plot_data = chart_df.groupby('주차').size().reset_index(name='수량')
                x_col = '주차'
            else: # 월별
                chart_df['월'] = chart_df['제조사_일자'].dt.to_period('M').astype(str)
                plot_data = chart_df.groupby('월').size().reset_index(name='수량')
                x_col = '월'

            fig = px.bar(plot_data, x=x_col, y='수량', text_auto=True, color_discrete_sequence=['#3366FF'])
            fig.update_layout(xaxis_title=unit, yaxis_title="수량(개)", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # 기존 상세 테이블
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜별**")
                st.table(f_df['직원'].value_counts().sort_index().rename("수량"))
            with c2:
                st.write("👤 **직원별**")
                st.table(f_df['직원'].value_counts().rename("수량"))
    else:
        st.error("데이터 내에 유효한 날짜 형식이 없습니다.")
