import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급 (정확한 엔드포인트 및 JSON 방식)"""
    print("🔑 V2 토큰 발급 시도...")
    # 아임웹 V2는 반드시 뒤에 /v2/auth 경로가 있어야 합니다.
    url = "https://api.imweb.me" 
    
    # 아임웹 V2는 데이터를 JSON 바디로 받습니다.
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            # V2 응답의 토큰 필드명은 access_token입니다.
            token = data.get('access_token')
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
            else:
                print(f"❌ 토큰 추출 실패: {data}")
                return None
        else:
            # 여기서 HTML이 출력된다면 URL 오타일 확률이 높습니다.
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기"""
    print("📦 상품 목록 조회 중...")
    # 상품 목록을 가져오는 정확한 경로
    url = "https://api.imweb.me"
    
    headers = {
        "Authorization": token,  # V2는 보통 Bearer 없이 토큰만 넣습니다.
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # V2 응답 구조: {'data': {'list': [...]}}
            items = res.json().get('data', {}).get('list', [])
            
            # 스크린샷의 data-id(상품번호)가 잘 오는지 첫 번째 데이터 확인
            if items:
                print(f"📌 첫 번째 상품 샘플 - 번호: {items[0].get('prod_no')}, 이름: {items[0].get('prod_name')}")
            
            print(f"📋 총 {len(items)}개의 상품을 아임웹에서 가져왔습니다.")
            return items
        else:
            print(f"❌ 상품 조회 실패: {res.status_code}, {res.text}")
            return []
    except Exception as e:
        print(f"❌ 조회 오류 발생: {e}")
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일이 저장소에 없습니다: {DB_FILE}")
        return

    token = get_v2_token()
    if not token: 
        return

    products = get_imweb_products_v2(token)
    if not products:
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 테이블 이름 (스크린샷 기준 날짜 반영)
        table_name = '"상품검색v4 260313"' 

        # '등록일' 컬럼 자동 생성 시도
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 새로 추가되었습니다.")
        except: 
            pass 

        update_count = 0
        for p in products:
            # 스크린샷의 data-id에 해당하는 값이 prod_no입니다.
            p_id = p.get('prod_no') 
            reg_date = p.get('reg_date') # 아임웹에서 준 등록일
            
            if p_id and reg_date:
                # DB의 '상품번호' 컬럼과 아임웹의 'prod_no'를 대조하여 등록일 업데이트
                sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
                cursor.execute(sql, (str(reg_date), str(p_id)))
                if cursor.rowcount > 0:
                    update_count += 1

        conn.commit()
        conn.close()
        print(f"✨ 작업 완료! {table_name} 테이블의 {update_count}개 상품 등록일 업데이트됨.")

    except Exception as e:
        print(f"❌ DB 작업 중 오류: {e}")

if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets 설정 확인 필요 (IMWEB_API_KEY, IMWEB_API_SECRET)")
