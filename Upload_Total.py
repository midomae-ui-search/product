@st.cache_data
def auto_load_data():
    search_pattern = "*상품검색*"
    files = glob.glob(search_pattern + ".*")
    
    if not files:
        return pd.DataFrame()

    target_file = max(files, key=os.path.getmtime)
    ext = os.path.splitext(target_file).lower()

    try:
        if ext == '.db':
            conn = sqlite3.connect(target_file)
            # [수정] DB 내 모든 테이블 이름을 가져옵니다.
            tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
            
            # DB가 비어있는지 확인
            if tables_df.empty:
                st.error(f"파일({target_file}) 내부에 데이터 테이블이 없습니다.")
                conn.close()
                return pd.DataFrame()
            
            # 첫 번째 테이블 이름을 가져와서 모든 데이터 읽기
            table_name = tables_df['name'].iloc[0]
            df = pd.read_sql_query(f"SELECT * FROM `{table_name}`", conn)
            conn.close()
            
            if df.empty:
                st.warning(f"'{table_name}' 테이블에 데이터가 한 줄도 없습니다.")
                return pd.DataFrame()
                
            return process_data(df)
        
        # ... (엑셀/CSV 읽기 부분은 동일) ...
