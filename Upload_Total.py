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
        
        brand_options = ["전체"] + all_brands
        selected_option = st.sidebar.selectbox("👤 직원 선택", brand_options, index=0)

        # 선택된 옵션에 따른 데이터 처리
        if selected_option == "전체":
            final_selected = all_brands
        else:
            # 리스트 형태로 감싸주어야 아래 .isin()에서 정상 작동합니다.
            final_selected = [selected_option]
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            mask = (df['제조사_일자'].dt.date >= start) & \
                   (df['제조사_일자'].dt.date <= end) & \
                   (df['브랜드'].isin(final_selected)) # <--- 이 부분을 selected_brands에서 final_selected로 꼭 바꿔주세요!
            f_df = df.loc[mask]

            # 상단 지표
            st.subheader(f"총 업로드: **{len(f_df):,} 개**")
            
            # --- 5. 기간별 그래프 분석 (추가된 부분) ---
            st.divider()
            st.subheader("📊기간별 업로드 추이")
            unit = st.radio(" ", ["일별", "주별", "월별"], horizontal=True)
            
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

                        # --- 5. 기간별 그래프 분석 ---
            # text='수량'을 추가하여 그래프 위에 숫자가 표시되도록 설정
            fig = px.bar(
                plot_data, 
                x=x_col, 
                y='수량', 
                text='수량', # 막대 위에 표시될 텍스트 데이터
                color_discrete_sequence=['#3366FF']
            )

            # 1. 막대 위 텍스트 설정: 천 단위 쉼표(,) 표시 및 위치
            fig.update_traces(
                texttemplate='%{text:,}', # 16,435 형태로 표시
                textposition='outside',    # 막대 바깥쪽 상단에 고정
                hovertemplate='수량: %{y:,}개<extra></extra>' # 마우스 오버 시 수량만 표시 (제조사_일자 제거)
            )

            # 2. 축 레이블 및 한국어 형식 설정
            fig.update_xaxes(
                tickformat="%Y년 %m월", 
                dtick="M1" if unit == "월별" else None
            )

            # 3. 레이아웃 설정 (y축 k 단위 제거)
            fig.update_layout(
                xaxis_title="", 
                yaxis_title="업로드 수(개)", 
                yaxis=dict(tickformat=",.0f"), # y축 숫자도 1단위까지 표시
                height=500,
                hovermode="x"
            )
            
            st.plotly_chart(fig, use_container_width=True)



            # 기존 상세 테이블
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜별**")
        # '제조사' 데이터를 가져와서 결과 상의 이름을 '날짜'로 변경
                date_summary = f_df['제조사'].value_counts().sort_index()
                date_summary.index.name = "날짜" # 인덱스 이름을 날짜로 변경
                st.table(date_summary.rename("수량"))
            with c2:
                st.write("👤 **직원별**")
             # '브랜드' 데이터를 가져와서 결과 상의 이름을 '직원'으로 변경
                staff_summary = f_df['브랜드'].value_counts()
                staff_summary.index.name = "직원" # 인덱스 이름을 직원으로 변경
                st.table(staff_summary.rename("수량"))
    else:
        st.error("데이터 내에 유효한 날짜 형식이 없습니다.")

# --- 6. 상품명이 '-'인 제품 상세 조회 (링크 포함) ---
st.divider()
st.subheader("📦 상품명 미기재('-') 카테고리별 상세")

# [함수 정의] 반드시 실행 코드보다 위에 있어야 합니다.
def get_category_map():
    category_data = {
        "전체": "ALL", "국내배송": "CATE118", "국내배송 특가 ~70%": "CATE128", "현지오늘배송": "CATE119", "개런티": "CATE117", "H1": "CATE72", "H2": "CATE73", "H3": "CATE74", 
        "CC 넘버원": "CATE75", "CC 티무역": "CATE76", "CC 팬더": "CATE77", "CC 나비/기타": "CATE78", "CC 일반": "CATE80",
        "[고퀄]기타 브랜드": "CATE79", "PD": "CATE84", "LV": "CATE85", "CD": "CATE86", "CL": "CATE87", "GY": "CATE88", 
        "LP": "CATE89", "BV": "CATE90", "MIU": "CATE91", "YSL": "CATE92", "DV": "CATE93", "THE ROW": "CATE116", 
        "GG": "CATE95", "FF": "CATE94", "BL": "CATE97", "BBR": "CATE98", "LW": "CATE100", "VT": "CATE99", "CHL": "CATE96", 
        "BAOBAO": "CATE101", "기타브랜드": "CATE102", "여행구/캐리어": "CATE103", "여성 의류": "CATE47", "바람막이/경량": "CATE48", 
        "여성패딩(겨울용)": "CATE66", "코트/퍼/무스탕(겨울용)": "CATE129", "맨즈 의류": "CATE68", "맨즈 아우터": "CATE69", 
        "키즈의류": "CATE130", "키즈 아우터": "CATE131", "여성 신발": "CATE105", "[수공]H 신발": "CATE106", "[수공]CC 신발": "CATE107", 
        "[수공]기타 신발": "CATE108", "남성 신발": "CATE109", "[수공]남성 신발": "CATE110", "키즈 신발": "CATE111", 
        "시계": "CATE113", "시계정보": "CATE114", "악세서리": "CATE125", "18K 금 제작": "CATE126", "지갑": "CATE115", 
        "모자": "CATE134", "스카프/머플러": "CATE127", "선글라스/안경": "CATE133", "기타잡화/소품": "CATE135", "여성 벨트": "CATE136", 
        "맨즈 벨트/잡화": "CATE139"
    }
    return {v: k for k, v in category_data.items()}

inv_map = get_category_map()

def map_cate_name(code):
    if not code: return "미지정"
    codes = [c.strip() for c in str(code).split(',')]
    names = [inv_map.get(c, c) for c in codes]
    return ", ".join(names)

# [메인 로직]
target_df = f_df[f_df['상품명'] == '-'].copy()

if not target_df.empty:
    # 카테고리 컬럼 찾기
    cat_col = next((c for c in target_df.columns if '카테고리' in c or '분류' in c), None)
    
    if cat_col:
        # 에러 발생 지점 수정: 함수가 위에서 정의됨
        target_df['카테고리명'] = target_df[cat_col].apply(map_cate_name)
        cat_summary = target_df['카테고리명'].value_counts().reset_index()
        cat_summary.columns = ['카테고리명', '수량']

        # 상단 요약 그래프
        fig_cat = px.bar(cat_summary, x='수량', y='카테고리명', orientation='h', text='수량',
                         color='수량', color_continuous_scale='Oranges')
        fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, height=300, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_cat, use_container_width=True)

        # 상세 조회를 위한 선택창
        selected_cat = st.selectbox("🔗 상세 목록을 보려는 카테고리를 선택하세요", cat_summary['카테고리명'])

        if selected_cat:
            detail_df = target_df[target_df['카테고리명'] == selected_cat].copy()
            # 링크/URL 관련 컬럼 찾기
            link_col = next((c for c in detail_df.columns if any(keyword in c.lower() for keyword in ['링크', 'url', '주소', 'link'])), None)
            
            st.write(f"### '{selected_cat}' 상세 리스트")
            
            if link_col:
                st.dataframe(
                    detail_df,
                    column_config={
                        link_col: st.column_config.LinkColumn("제품 링크")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.dataframe(detail_df, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ '카테고리' 컬럼을 찾을 수 없습니다.")
else:
    st.info("✅ 상품명이 '-'인 데이터가 없습니다.")
