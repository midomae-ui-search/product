import requests
import sqlite3
import os

# 1. 보안 서버에서 API 키 가져오기
API_KEY = os.environ.get('IMWEB_API_KEY')
DB_FILE = '상품검색 V4.db' # 이미지에 있는 파일명과 동일하게 설정

def get_imweb_dates():
    # 아임웹 API로 최신 상품의 등록일 가져오기
    url = "https://api.imweb.me"
    headers = {"Access-Token": API_KEY}
    res = requests.get(url, headers=headers).json()
    return res.get('list', [])

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"파일을 찾을 수 없습니다: {DB_FILE}")
        return

    # DB 연결
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # '등록일' 컬럼이 없다면 추가 (최초 1회 실행)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN 등록일 TEXT")
    except:
        pass # 이미 컬럼이 있으면 무시

    # 아임웹 데이터 가져오기
    products = get_imweb_dates()

    for p in products:
        p_id = str(p['idx'])
        # Unix Timestamp를 읽기 쉬운 날짜로 변환 (필요시 포맷 조정 가능)
        reg_date = p['created_at'] 
        
        # '상품번호' 컬럼명은 실제 DB 구조에 맞춰 'idx' 혹은 '상품번호'로 수정 필요할 수 있음
        # 여기서는 '상품번호'라고 가정하고 업데이트합니다.
        cursor.execute("UPDATE products SET 등록일 = ? WHERE 상품번호 = ?", (reg_date, p_id))

    conn.commit()
    conn.close()
    print("DB 업데이트 완료!")

if __name__ == "__main__":
    update_db()
