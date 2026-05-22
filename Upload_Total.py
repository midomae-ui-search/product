import streamlit as st
import pandas as pd
import sqlite3
import os
import zipfile  
import io  
import plotly.express as px  

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

# --- 2. 기본 데이터 로드 (서버 내 ZIP 파일 내부 DB 읽기) ---
@st.cache_data(show_spinner="압축 파일에서 기본 데이터를 불러오는 중...")
def load_default_db():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    zip_file = os.path.join(current_dir, '상품검색 V4.zip')
    if not os.path.exists(zip_file):
        zip_file = '상품검색 V4.zip'

    if os.path.exists(zip_file):
        try:
            with zipfile.ZipFile(zip_file, 'r') as z:
                db_in_zip = [f for f in z.namelist() if f.endswith('.db')]
                
                if not db_in_zip:
                    st.error("⚠️ 시스템 압축 파일(.zip) 내부에 .db 확장자 파일이 존재하지 않습니다.")
                    return pd.DataFrame()
                
                target_db_name = db_in_zip[0]
                db_data = z.read(target_db_name)
                mem_db = io.BytesIO(db_data)
                
                temp_db_path = os.path.join(current_dir, "_temp_cloud_db.db")
                with open(temp_db_path, "wb") as f:
                    f.write(mem_db.getbuffer())
                
                conn = sqlite3.connect(temp_db_path)
                tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
                
                if not tables.empty:
                    t_names = tables['name'].tolist()
                    t_name = '상품검색v4' if '상품검색v4' in t_names else t_names[0]
                    df = pd.read_sql_query(f"SELECT * FROM `{t_name}`", conn)
                    conn.close()
                    
                    if os.path.exists(temp_db_path):
                        os.remove(temp_db_path)
                    return process_data(df)
                    
                conn.close()
                if os.path.exists(temp_db_path):
                    os.remove(temp_db_path)
                    
        except Exception as e:
            st.error(f"기본 압축 데이터베이스 읽기 중 오류: {e}")
            temp_db_path = os.path.join(current_dir, "_temp_cloud_db.db")
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)
    else:
        st.warning(f"⚠️ '{zip_file}' 파일을 찾을 수 없습니다. GitHub 저장소를 확인해 주세요.")
        
    return pd.DataFrame()

# --- 3. 메인 화면 구성 ---
st.set_page_config(page_title="업로드 수량 집계", layout="wide") 
st.title("📊 업로드 수량 집계")

# 사이드바 구성
st.sidebar.markdown("### ⚙️ 시스템 설정")
if st.sidebar.button("🔄 데이터 최신화 (새로고침)"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 📥 수기 파일 업로드")

# [개선 적용] 수기 업로드 허용 유형에 zip 추가
uploaded_file = st.sidebar.file_uploader("새로운 엑셀/CSV/ZIP 업로드", type=["xlsx", "csv", "zip"])

df = pd.DataFrame()

if uploaded_file:
    file_name = uploaded_file.name.lower()
    
    # CASE A: 사용자가 수기 파일로 ZIP(알집)을 올렸을 때의 처리 로직
    if file_name.endswith('.zip'):
        try:
            with zipfile.ZipFile(uploaded_file, 'r') as z:
                # 압축 내부에서 분석 타겟 데이터 유형(.xlsx, .csv, .db) 식별
                internal_files = z.namelist()
                valid_files = [f for f in internal_files if f.endswith(('.xlsx', '.csv', '.db')) and not f.startswith('__MACOSX')]
                
                if not valid_files:
                    st.error("⚠️ 업로드한 ZIP 파일 내에 읽을 수 있는 엑셀(.xlsx), CSV(.csv), DB(.db) 파일이 없습니다.")
                else:
                    target_file = valid_files[0]  # 첫 번째 유효 파일 선택
                    extracted_data = z.read(target_file)
                    
                    if target_file.endswith('.csv'):
                        try: raw_df = pd.read_csv(io.BytesIO(extracted_data), encoding='utf-8-sig')
                        except: raw_df = pd.read_csv(io.BytesIO(extracted_data), encoding='cp949')
                    elif target_file.endswith('.xlsx'):
                        try: raw_df = pd.read_excel(io.BytesIO(extracted_data), engine='calamine')
                        except: raw_df = pd.read_excel(io.BytesIO(extracted_data))
                    elif target_file.endswith('.db'):
                        # 업로드된 zip 내부에 db가 있을 경우 가상 메모리 매핑 처리
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
            st.error(f"업로드된 ZIP 파일 해제 및 데이터 파싱 중 오류 발생: {e}")
            
    # CASE B: 기존 단일 CSV 파일 처리
    elif file_name.endswith('.csv'):
        try: raw_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        except: raw_df = pd.read_csv(uploaded_file, encoding='cp949')
        df = process_data(raw_df)
        st.info(f"📂 업로드된 CSV 파일({uploaded_file.name}) 분석 중")
        
    # CASE C: 기존 단일 엑셀 파일 처리
    else:
        try: raw_df = pd.read_excel(uploaded_file, engine='calamine')
        except: raw_df = pd.read_excel(uploaded_file)
        df = process_data(raw_df)
        st.info(f"📂 업로드된 엑셀 파일({uploaded_file.name}) 분석 중")
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

            # 상단 지표
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

            fig = px.bar(
                plot_data, 
                x=x_col, 
                y='수량', 
                text='수량', 
                color_discrete_sequence=['#3366FF']
            )

            fig.update_traces(
                texttemplate='%{text:,}', 
                textposition='outside',    
                hovertemplate='수량: %{y:,}개<extra></extra>' 
            )

            fig.update_xaxes(
                tickformat="%Y년 %m월" if unit == "월별" else "%Y-%m-%d", 
                dtick="M1" if unit == "월별" else None
            )

            fig.update_layout(
                xaxis_title="", 
                yaxis_title="업로드 수(개)", 
                yaxis=dict(tickformat=",.0f"), 
                height=500,
                hovermode="x"
            )
            st.plotly_chart(fig, use_container_width=True)

            # 기존 상세 테이블
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("📅 **날짜별**")
                date_summary = f_df['제조사'].value_counts().sort_index()
                date_summary.index.name = "날짜" 
                st.table(date_summary.rename("수량"))
            with c2:
                st.write("👤 **직원별**")
