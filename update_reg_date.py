import requests
import sqlite3
import os

# 1. 설정
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급"""
    print("🔑 V2 토큰 발급 시도...")
    url = "https://api.imweb.me" # V2 인증 주소
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            token = res.json().get('data', {}).get('access_token')
            print("✅ V2 토큰 발급 성공!")
            return token
        else:
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기"""
    url = "https://api.imweb.me"
    headers = {
        "access-token": token, # V2는 헤더 이름이 소문자일 수 있음
        "Content-Type": "application/json"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # V2 응답 구조에 맞춰 데이터 추출
            return res.json().get('data', {}).get('items', [])
        else:
            print(f"❌ 상품 조회 실패: {res.status_code}")
            return []
    except Exception as e:
        print(f"❌ 조회 오류: {e}")
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일 없음: {DB_FILE}")
        return

    token = get_v2_token()
    if not token: return

    products = get_imweb_products_v2(token)
    if not products:
        print("📭 상품 데이터가 없습니다.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    table_name = '"상품검색v4 260312"' 

    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
    except: pass 

    update_count = 0
    for p in products:
        p_id = p.get('idx')
        reg_date = p.get('created_at')
        if p_id and reg_date:
            # V2 날짜 형식(Timestamp) 처리 또는 문자열 그대로 입력
            sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
            cursor.execute(sql, (str(reg_date), str(p_id)))
            if cursor.rowcount > 0:
                update_count += 1

    conn.commit()
    conn.close()
    print(f"✨ 완료! {update_count}개 업데이트됨.")

if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ Key 또는 Secret 설정 확인 필요")
