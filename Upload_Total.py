import streamlit as st
import pandas as pd
import sqlite3
import os

# --- 1. 데이터 통합 처리 함수 ---
def process_data(df):
    """날짜/브랜드 데이터 청소 및 형식 통일"""
    if df.empty: return df
    # 컬럼명 공백 제거 및 필수 열 확인
    df.columns = [c.strip() for c in df.columns]
    
    # '제조사', '브랜드' 열이 포함된 컬럼 찾기 (유연한 대응)
    name_map = {col: '제조사' for col in df.columns if '제조사' in col}
    name_map.update({col: '브랜드' for col in df.columns if '브랜드' in col})
    df = df.rename(columns=name_map)

    # 데이터 정리
    df['브랜드'] = df['브랜드'].fillna('미지정').astype(str).str.strip()
    df['제조사'] = df['제조사'].fillna('날짜없음').astype(str).str.strip()
    
    # 날짜 변환 (일자 및 월 단위 대응)
    df['제조사_일자'] = pd.to_datetime(df['제조사'], errors='coerce')
    mask = df['제조사_일자'].isna() & (df['제조사'] != '날짜없음')
    df.loc[mask, '제조사_일자'] = pd.to_datetime(df.loc[mask, '제조사'], format='%Y-%m', errors='coerce')
    
    return df[['제조사', '브랜드', '제조사_일자']]

# --- 2. 세 가지 형식 자동 탐색 로드 ---
@st.cache_data
def auto_load_data():
    """DB -> 엑셀 -> CSV 순서로 파일을 찾아 읽어옴"""
    base_name = '상품검색v4' # 공통 파일 이름
    
    # 1순위: SQLite DB (.db)
    if os.path.exists(f"{base_name}.db"):
        conn = sqlite3.connect(f"{base_name}.db")
        # 테이블명을 자동으로 찾아 첫 번째 테이블 읽기
        table = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn).iloc[0,0]
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        conn.close()
        return process_data(df)
    
    # 2순위: 엑셀 (.xlsx)
    elif os.path.exists(f"{base_name}.xlsx"):
        df = pd.read_excel(f"{base_name}.xlsx", engine='calamine')
        return process_data(df)
    
    # 3순위: CSV (.csv)
    elif os.path.exists(f"{base_name}.csv"):
        try:
            df = pd.read_csv(f"{base_name}.csv", encoding='utf-8-sig')
        except:
            df = pd.read_csv(f"{base_name}.csv", encoding='cp949')
        return process_data(df)
    
    return pd.DataFrame()

# --- 3. 메인 화면 ---
st.set_page_config(page_title="만능 집계 시스템", layout="centered")
st.title("📊 통합 업로드 수량 집계")

data_source = st.radio("데이터 소스 선택", ("저장소 파일 자동 로드", "직접 파일 업로드"), horizontal=True)

df = pd.DataFrame()

if data_source == "저장소 파일 자동 로드":
    df = auto_load_data()
    if df.empty:
        st.warning("저장소에서 상품검색v4 (db, xlsx, csv) 파일을 찾을 수 없습니다.")
else:
    u_file = st.file_uploader("파일을 업로드하세요", type=["xlsx", "csv"])
    if u_file:
        if u_file.name.endswith('.csv'):
            try: df = pd.read_csv(u_file, encoding='utf-8-sig')
            except: df = pd.read_csv(u_file, encoding='cp949')
        else:
            df = pd.read_excel(u_file, engine='calamine')
        df = process_data(df)

# --- 4. 필터 및 결과 (이전과 동일) ---
if not df.empty:
    # (여기서부터는 기존의 필터 및 수량 출력 코드를 사용하시면 됩니다)
    st.success("✅ 데이터를 성공적으로 불러왔습니다.")
    # ... [생략] ...
