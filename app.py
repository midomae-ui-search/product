import streamlit as st
import sqlite3
import pandas as pd

# 1. DB 연결 (본인의 .db 파일 이름으로 수정하세요)
conn = sqlite3.connect('상품검색 Ver3.db') 

st.title("🔍 상품 이미지 검색기")

# 2. 검색창 (고객이 입력할 곳)
keyword = st.text_input("검색어를 입력하세요", placeholder="예: 구두")

if keyword:
    # 1. 검색어 나누기 및 쿼리 생성
    keywords = keyword.split()
    conditions = " AND ".join([f'("상품명" LIKE "%{word}%" OR "원산지" LIKE "%{word}%")' for word in keywords])
    
    # 2. 버튼 클릭 횟수를 저장할 공간 (State)
    if 'load_count' not in st.session_state:
        st.session_state.load_count = 100 # 처음엔 100개

    # 3. 데이터 가져오기 (저장된 개수만큼)
    query = f'SELECT * FROM "상품검색 ver3 260304 test3" WHERE {conditions} LIMIT {st.session_state.load_count}'
    df = pd.read_sql(query, conn)

    # 4. 화면 출력 (가장 안정적인 방식)
    for _, row in df.iterrows():
        # 열(column)을 나눠서 배치하면 화면 꼬임 현상이 훨씬 줄어듭니다.
        col1, col2 = st.columns([1, 3]) # 이미지 칸(1)과 텍스트 칸(3)
        
        with col1:
            st.image(row['대표이미지URL'], width=150)
            
        with col2:
            # 기존 정보들 (그대로 유지)
            st.write(f"**상품명:** {row['상품명']}")
            st.write(f"**상품번호:** {row['상품번호']}")
            st.write(f"**원산지:** {row['원산지']}")
            
            # 새롭게 추가하는 버튼 (row['상품URL'] 부분은 DB 필드명에 맞춰주세요)
            st.link_button("🔗 상세페이지 보기", row['상품URL'])
            
        st.divider() # 상품마다 구분선

    # 5. [더보기] 버튼 (누르면 100개씩 추가)
    if len(df) >= st.session_state.load_count:
        if st.button("🔽 100개 더보기"):
            st.session_state.load_count += 100
            st.rerun() # 화면 새로고침