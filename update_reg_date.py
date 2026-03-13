import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급 (수정됨)"""
    print("🔑 V2 토큰 발급 시도...")
    # 수정: 공식 V2 인증 엔드포인트
    url = "https://api.imweb.me" 
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            # 응답 구조: { "code": 200, "data": { "access_token": "..." } }
            token = res.json().get('data', {}).get('access_token')
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
            else:
                print("❌ 토큰 데이터가 응답에 없습니다.")
                return None
        else:
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기 (수정됨)"""
    # 수정: 공식 V2 상품 조회 엔드포인트
    url = "https://api.imweb.me"
    # 수정: Authorization: Bearer 방식 헤더 적용
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        # V2는 기본적으로 한 페이지에 여러 상품을 가져옵니다.
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # V2 응답 구조: { "data": { "list": [ ... ] } }
            data = res.json().get('data', {})
            return data.get('list', []) 
        else:
            print(f"❌ 상품 조회 실패: {res.status_code}, {res.text}")
            return []
    except Exception as e:
        print(f"❌ 조회 오류: {e}")
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일 없음: {DB_FILE}")
        return

    token = get_v2_token()
    if not token: 
        print("❌ 유효한 토큰이 없어 종료합니다.")
        return

    products = get_imweb_products_v2(token)
    if not products:
        print("📭 상품 데이터가 없습니다. (API 응답 비어있음)")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # 테이블 이름에 공백이 있으므로 큰따옴표 유지
    table_name = '"상품검색v4 260312"' 

    try:
        # 컬럼이 없을 경우를 대비해 추가
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
    except: 
        pass 

    update_count = 0
    for p in products:
        # V2 API 응답 필드: 상품번호(prod_no 또는 idx), 등록일(reg_date) 확인 필요
        # 공식 규격상 'prod_no' 또는 'prod_idx'를 주로 사용합니다.
        p_id = p.get('prod_no') or p.get('idx') 
        reg_date = p.get('reg_date') or p.get('created_at')
        
        if p_id and reg_date:
            sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
            cursor.execute(sql, (str(reg_date), str(p_id)))
            if cursor.rowcount > 0:
                update_count += 1

    conn.commit()
    conn.close()
    print(f"✨ 완료! {update_count}개 상품 업데이트됨.")

if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets 설정 확인 필요 (API_KEY 또는 API_SECRET 누락)")
