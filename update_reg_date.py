import requests
import sqlite3
import os

# 1. 설정 (파일명 및 API 키)
API_KEY = os.environ.get('IMWEB_API_KEY')
DB_FILE = '상품검색 V4.db' 

def get_imweb_dates():
    """아임웹 API에서 상품 정보를 가져오는 함수"""
    # ⚠️ 중요: 주소 끝에 /v1/shop/products가 반드시 있어야 합니다.
    url = "https://api.imweb.me"
    headers = {
        "Access-Token": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"❌ API 호출 실패: {res.status_code}")
            return []
        
        # 아임웹 데이터 구조: data -> list 순서로 접근
        data = res.json()
        return data.get('data', {}).get('list', [])
    except Exception as e:
        print(f"❌ API 요청 중 오류 발생: {e}")
        return []

def update_db():
    """가져온 데이터를 DB에 업데이트하는 함수"""
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일을 찾을 수 없습니다: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 테이블 이름 (띄어쓰기가 있어 큰따옴표로 감쌈)
    table_name = '"상품검색v4 260312"' 

    # 1. '등록일' 컬럼이 없으면 새로 추가
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
        print("🆕 '등록일' 컬럼을 새로 추가했습니다.")
    except:
        print("ℹ️ '등록일' 컬럼이 이미 존재합니다.")

    # 2. 데이터 가져오기 및 업데이트 실행
    products = get_imweb_dates()
    update_count = 0

    print(f"🔄 총 {len(products)}개의 상품 데이터를 대조 중...")

    for p in products:
        p_id = p.get('idx')         # 아임웹 상품 고유 번호
        reg_date = p.get('created_at') # 상품 등록일
        
        if not p_id or not reg_date:
            continue
        
        # ⭐ 핵심 수정: CAST를 사용하여 DB의 상품번호와 아임웹 ID의 형식을 강제로 맞춤
        # DB의 상품번호가 숫자든 문자든 상관없이 비교하여 업데이트합니다.
        sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
        cursor.execute(sql, (reg_date, str(p_id)))
        
        if cursor.rowcount > 0:
            update_count += 1

    conn.commit()
    conn.close()
    print(f"✨ 업데이트 완료! 총 {update_count}개의 상품에 날짜가 입력되었습니다.")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ 에러: IMWEB_API_KEY 환경변수가 설정되지 않았습니다.")
    else:
        update_db()
