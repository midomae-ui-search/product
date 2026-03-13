import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """본인 사이트 도메인을 이용한 V2 토큰 발급"""
    print("🔑 V2 토큰 발급 시도 (https://api.midomae.com/admin/shopping/product)...")
    
    # [중요] 아임웹 V2는 본인 도메인 앞에 api. 을 붙여 호출하는 것이 정석입니다.
    # 만약 api.midomae.com 이 안되면 다시 api.imweb.me 로 시도합니다.
    url = "https://api.midomae.com/admin/shopping/product" 
    
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        # JSON 방식으로 전송
        res = requests.post(url, json=payload)
        
        # 만약 404나 에러가 나면 공식 API 서버로 재시도
        if res.status_code != 200:
            print("🔄 도메인 호출 실패, 공식 API 서버로 재시도...")
            url = "https://api.midomae.com/admin/shopping/product"
            res = requests.post(url, json=payload)

        if res.status_code == 200:
            data = res.json()
            token = data.get('access_token')
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
        
        print(f"❌ 인증 실패: {res.status_code}, {res.text[:100]}")
        return None
    except Exception as e:
        print(f"❌ 인증 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기"""
    print("📦 상품 목록 조회 중...")
    # 토큰 발급에 성공한 도메인과 동일하게 맞춥니다.
    url = "https://api.midomae.com/admin/shopping/product" 
    
    headers = {
        "Authorization": token, 
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            url = "https://api.midomae.com/admin/shopping/product" 
            res = requests.get(url, headers=headers)

        if res.status_code == 200:
            items = res.json().get('data', {}).get('list', [])
            print(f"📋 총 {len(items)}개의 상품을 아임웹에서 가져왔습니다.")
            return items
        else:
            print(f"❌ 상품 조회 실패: {res.status_code}")
            return []
    except Exception as e:
        print(f"❌ 조회 오류 발생: {e}")
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일 없음: {DB_FILE}")
        return

    token = get_v2_token()
    if not token: return

    products = get_imweb_products_v2(token)
    if not products: return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 테이블 이름 (날짜 확인: 260313)
        table_name = '"상품검색v4 260313"' 

        # 컬럼 추가
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
        except: pass 

        update_count = 0
        for p in products:
            p_id = p.get('prod_no') 
            reg_date = p.get('reg_date') 
            
            if p_id and reg_date:
                # DB의 '상품번호'와 API의 'prod_no' 매칭
                sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
                cursor.execute(sql, (str(reg_date), str(p_id)))
                if cursor.rowcount > 0:
                    update_count += 1

        conn.commit()
        conn.close()
        print(f"✨ 작업 완료! {update_count}개 상품 업데이트됨.")
    except Exception as e:
        print(f"❌ DB 오류: {e}")

if __name__ == "__main__":
    update_db()
