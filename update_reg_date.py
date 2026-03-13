import requests
import sqlite3
import os

# 1. 설정 (파일명에 띄어쓰기 주의!)
API_KEY = os.environ.get('IMWEB_API_KEY')
DB_FILE = '상품검색 V4.db' 

def get_imweb_dates():
    # 주소 끝에 /v1/shop/products 가 반드시 있어야 합니다.
    url = "https://api.imweb.me"
    headers = {
        "Access-Token": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"❌ API 실패: {res.status_code}")
            return []
        
        # 아임웹 데이터 구조: data -> list
        return res.json().get('data', {}).get('list', [])
    except:
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ 파일을 찾을 수 없습니다: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # ⭐ 중요: 테이블 이름을 '상품검색v4 260312'로 수정 (따옴표 필수)
    table_name = '"상품검색v4 260312"' 

    # '등록일' 컬럼 추가 (없을 경우만)
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
    except:
        pass 

    products = get_imweb_dates()
    update_count = 0

    for p in products:
        p_id = str(p['idx'])
        reg_date = p['created_at'] 
        
        # '상품번호' 기준으로 등록일 업데이트
        cursor.execute(f"UPDATE {table_name} SET 등록일 = ? WHERE 상품번호 = ?", (reg_date, p_id))
        if cursor.rowcount > 0:
            update_count += 1

    conn.commit()
    conn.close()
    print(f"✨ 완료! {update_count}개의 상품 등록일이 업데이트되었습니다.")

if __name__ == "__main__":
    if API_KEY:
        update_db()
    else:
        print("❌ API 키가 없습니다.")
