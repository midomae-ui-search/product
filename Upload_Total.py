import streamlit as st
import pandas as pd
import sqlite3
import os
import zipfile  
import io  
import datetime
import plotly.express as px  

# --- 1. 데이터 처리 핵심 함수 ---
def process_data(df):
    if df.empty: return df
    df.columns = [c.strip() for c in df.columns]
    
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df.loc[df['브랜드'] == '', '브랜드'] = '미지정'
    
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

# --- 2. 기본 데이터 로드 (경로 탐색 완벽 보완 버전) ---
@st.cache_data(show_spinner="압축 파일에서 기본 데이터를 불러오는 중...")
def load_default_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # [오류 해결 포인트] 경로 탐색을 순차적으로 안전하게 크로스 체크합니다.
    zip_file = os.path.join(current_dir, '상품검색 V4.zip')
    if not os.path.exists(zip_file):
        zip_file = '상품검색 V4.zip'

    if os.path.exists(zip_file):
        try:
            # 1. 파일 경로를 확실하게 지정하여 바이너리로 열기
            with open(zip_file, 'rb') as raw_f:
                zip_bytes = io.BytesIO(raw_f.read())
            
            # 2. 메모리 상에서 zip 파일 언팩
            with zipfile.ZipFile(zip_bytes, 'r') as z:
                db_in_zip = [f for f in z.namelist() if f.endswith('.db')]
                
                if not db_in_zip:
                    st.error("⚠️ 압축 파일 내부에 .db 파일이 존재하지 않습니다.")
                    return pd.DataFrame()
                
                target_db_name = db_in_zip[0]  # 확실하게 첫번째 파일 문자열 추출
                db_data = z.read(target_db_name)
                
                # 3. 임시 DB 생성 및 조회 처리
                unique_temp_path = os.path.join(current_dir, f"_temp_dashboard_db_{datetime.datetime.now().strftime('%H%M%S')}.db")
                with open(unique_temp_path, "wb") as temp_f:
                    temp_f.write(db_data)
                
                conn = sqlite3.connect(unique_temp_path)
                tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                
                if not tables.empty:
                    t_names = tables['name'].tolist()
                    t_name = '상품검색v4' if '상품검색v4' in t_names else t_names[0]
                    df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                    conn.close()
                    
                    if os.path.exists(unique_temp_path):
                        os.remove(unique_temp_path)
                    return process_data(df)
                    
                conn.close()
                if os.path.exists(unique_temp_path):
                    os.remove(unique_temp_path)
                    
        except Exception as e:
            st.error(f"기본 압축 데이터베이스 읽기 중 오류: {e}")
    else:
        st.error(f"⚠️ 시스템에서 '상품검색 V4.zip' 파일을 찾을 수 없습니다. 경로를 확인해 주세요. (조회 경로: {zip_file})")
    return pd.DataFrame()

# --- 3. 메인 화면 구성 ---
st.set_page_config(page_title="업로드 수량 집계", layout="wide") 
st.title("📊 업로드 수량 집계")

st.sidebar.markdown("### ⚙️ 시스템 설정")
if st.sidebar.button("🔄 데이터 최신화 (새로고침)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📥 수기 파일 업로드")
uploaded_file = st.sidebar.file_uploader("새로운 엑셀/CSV/ZIP 업로드", type=["xlsx", "csv", "zip"])

df = pd.DataFrame()

if uploaded_file:
    file_name = uploaded_file.name.lower()
    if file_name.endswith('.zip'):
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                internal_files = z.namelist()
                valid_files = [f for f in internal_files if f.endswith(('.xlsx', '.csv', '.db')) and not f.startswith('__MACOSX')]
                
                if not valid_files:
                    st.error("⚠️ 업로드한 ZIP 파일 내에 읽을 수 있는 파일이 없습니다.")
                else:
                    target_file = valid_files[0]
                    extracted_data = z.read(target_file)
                    
                    if target_file.endswith('.csv'):
                        try: raw_df = pd.read_csv(io.BytesIO(extracted_data), encoding='utf-8-sig')
                        except: raw_df = pd.read_csv(io.BytesIO(extracted_data), encoding='cp949')
                    elif target_file.endswith('.xlsx'):
                        try: raw_df = pd.read_excel(io.BytesIO(extracted_data), engine='calamine')
                        except: raw_df = pd.read_excel(io.BytesIO(extracted_data))
                    elif target_file.endswith('.db'):
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        temp_upload_db = os.path.join(current_dir, "_temp_upload_db.db")
                        with open(temp_upload_db, "wb") as f:
                            f.write(extracted_data)
                        conn = sqlite3.connect(temp_upload_db)
                        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                        if not tables.empty:
                            t_name = '상품검색v4' if '상품검색v4' in tables['name'].tolist() else tables['name'].iloc[0]
                            raw_df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                        conn.close()
                        if os.path.exists(temp_upload_db): os.remove(temp_upload_db)
                        
                    df = process_data(raw_df)
                    st.info(f"📂 알집 내부 파일({target_file}) 분석 완료")
        except Exception as e:
            st.error(f"업로드된 ZIP 파일 해제 오류: {e}")
            
    elif file_name.endswith('.csv'):
        try: raw_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: raw_df = pd.read_csv(uploaded_file, encoding='cp949')
        df = process_data(raw_df)
    else:
        try: raw_df = pd.read_excel(uploaded_file, engine='calamine')
        except: raw_df = pd.read_excel(uploaded_file)
        df = process_data(raw_df)
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
    
    today_year = datetime.date.today().year
    chart_df_clean = df.dropna(subset=['제조사_일자']).copy()
    
    if not chart_df_clean.empty:
        chart_df_clean = chart_df_clean[
            (chart_df_clean['제조사_일자'].dt.year >= 2020) & 
            (chart_df_clean['제조사_일자'].dt.year <= today_year + 1)
        ]

    if not chart_df_clean.empty:
        min_d = chart_df_clean['제조사_일자'].min().date()
        max_d = chart_df_clean['제조사_일자'].max().date()
        
        if (max_d - min_d).days > 365 * 5:
            min_d = max_d - datetime.timedelta(days=365)
            
        selected_range = st.sidebar.date_input("📅 조회 기간", value=(min_d, max_d))
        all_brands = sorted(df['브랜드'].unique())
        
        brand_options = ["전체"] + all_brands
        selected_option = st.sidebar.selectbox("👤 직원 선택", brand_options, index=0)

        if selected_option == "전체":
            final_selected = all_brands
        else:
            final_selected = [selected_option]
            
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            mask = (df['제조사_일자'].dt.date >= start) & \
                   (df['제조사_일자'].dt.date <= end) & \
                   (df['브랜드'].isin(final_selected))
            f_df = df.loc[mask]

            st.subheader(f"총 업로드: **{len(f_df):,} 개**")
            
            # --- 5. 기간별 그래프 분석 ---
            st.divider()
            st.subheader("📊 기간별 업로드 추이")
            unit = st.radio(" ", ["일별", "주별", "월별"], horizontal=True)
            
            chart_df = f_df.copy()
            if unit == "일별":
                plot_data = chart_df.groupby(chart_df['제조사_일자'].dt.date).size().reset_index(name='수량')
                x_col = '제조사_일자'
            elif unit == "주별":
                chart_df['주차'] = chart_df['제조사_일자'].dt.to_period('W').apply(lambda r: r.start_time)
                plot_data = chart_df.groupby('주차').size().reset_index(name='수량')
                x_col = '주차'
            else: # 월별
                chart_df['월'] = chart_df['제조사_일자'].dt.to_period('M').astype(str)
                plot_data = chart_df.groupby('월').size().reset_index(name='수량')
                x_col = '월'

            if not plot_data.empty:
                fig = px.bar(plot_data, x=x_col, y='수량', text='수량', color_discrete_sequence=['#3366FF'])
                fig.update_traces(texttemplate='%{text:,}', textposition='outside', hovertemplate='수량: %{y:,}개<extra></extra>')
                fig.update_xaxes(tickformat="%Y년 %m월" if unit == "월별" else "%Y-%m-%d", dtick="M1" if unit == "월별" else None)
                fig.update_layout(xaxis_title="", yaxis_title="업로드 수(개)", yaxis=dict(tickformat=",.0f"), height=500, hovermode="x")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("선택 기간에 시각화할 데이터가 없습니다.")

            # 상세 테이블 구역 (직원별 표 정상 출력 패치 적용)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("📅 **날짜별**")
                date_summary = f_df['제조사'].value_counts().reset_index()
                date_summary.columns = ['날짜', '수량']
                date_summary = date_summary.sort_values(by='날짜')
                st.dataframe(date_summary, use_container_width=True, hide_index=True)

            # --- 6. 상품명이 미수정된 제품 상세 조회 ---
            st.divider()
            st.subheader("📦 상품명 미수정 카테고리 리스트")
            
            # 카테고리 코드 ID 번역을 위한 매핑 딕셔너리
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
                "모자": "CATE134", "스카프/머플러": "CATE127", "선글라스/안경": "CATE133", "기타잡화/소품": "CATE135", "여성 벨트": "CATE136", "맨즈 벨트/잡화": "CATE139"
            }
            inv_map = {v: k for k, v in category_data.items()}

            # 카테고리명을 한글로 변환하는 서브 함수
            def map_cate_name(code):
                if not code: return "미지정"
                return ", ".join([inv_map.get(c.strip(), c.strip()) for c in str(code).split(',')])

            # 상품명 컬럼 탐색 및 미수정(파이프라인 '|' 포함 등) 조건 필터링
            name_col = next((c for c in f_df.columns if '상품명' in c or '명칭' in c), None)
            if name_col:
                target_df = f_df[(f_df[name_col] == '-') | (f_df[name_col].astype(str).str.contains(r'\|', na=False)) | (f_df[name_col].isna())].copy()
            else:
                target_df = f_df[f_df['상품명'] == '-'].copy()

            # 미수정 데이터 존재 시 시각화 및 테이블 렌더링
            if not target_df.empty:
                cat_col = next((c for c in target_df.columns if '카테고리' in c or '분류' in c), None)
                if cat_col:
                    target_df['카테고리명'] = target_df[cat_col].apply(map_cate_name)
                    cat_summary = target_df['카테고리명'].value_counts().reset_index()
                    cat_summary.columns = ['카테고리명', '수량']

                    # 미수정 카테고리 가로 막대 그래프 출력
                    fig_cat = px.bar(cat_summary, x='수량', y='카테고리명', orientation='h', text='수량', color='수량', color_continuous_scale='Oranges')
                    fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, height=300, showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_cat, use_container_width=True)

                    # 셀렉트박스를 활용한 상세 리스트 바인딩
                    selected_cat = st.selectbox("🔗 상세 목록을 보려는 카테고리를 선택하세요", cat_summary['카테고리명'])
                    if selected_cat:
                        detail_df = target_df[target_df['카테고리명'] == selected_cat].copy()
                        display_cols = [c for c in ['상품번호', '상품명', '상품URL', '원산지', '제조사', '브랜드'] if c in detail_df.columns]
                        
                        st.write(f"### '{selected_cat}' 상세 리스트")
                        st.data_editor(
                            detail_df[display_cols], 
                            column_config={"상품URL": st.column_config.LinkColumn("제품 링크", display_text="바로가기")}, 
                            use_container_width=True, 
                            hide_index=True, 
                            disabled=True
                        )
                else: 
                    st.warning("⚠️ '카테고리' 컬럼을 찾을 수 없습니다.")
            else: 
                st.info("✅ 선택한 기간 내에 상품명이 미수정 상태인 데이터가 존재하지 않습니다. 전부 가공이 완료되었습니다.")
        else:
            st.info("📅 종료 날짜를 마저 선택해주세요.")
    else:
        st.error("데이터 내에 유효한 날짜 형식이 없거나 너무 오래된 날짜 데이터만 존재합니다.")

