import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 안전하게 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    # 수정 전: url = "https://api.imweb.me"
    url = "https://api.imweb.me"  # /v2/auth 추가
    
    params = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    # ... 이하 동일

    
    try:
        res = requests.post(url, params=params)
        if res.status_code == 200:
            data = res.json()
            token = data.get('data', {}).get('access_token')
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
            else:
                print(f"❌ 토큰 추출 실패: {data}")
                return None
        else:
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    # 수정 전: url = "https://api.imweb.me"
    url = "https://api.imweb.me"  # 경로 추가
    
    headers = {
        "Authorization": token,  # 아임웹 V2는 Bearer를 생략하거나 포함하는 형식이 버전에 따라 다를 수 있으니 확인 필요
        "Content-Type": "application/json"
    }
    # ... 이하 동일

    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('list', [])
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
        
        # 수정됨: 테이블 이름을 새로운 날짜로 업데이트
        table_name = '"상품검색v4 260313"' 

        # '등록일' 컬럼 자동 생성 시도
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 새로 추가되었습니다.")
        except: 
            pass 

        update_count = 0
        for p in products:
            p_id = p.get('prod_no') 
            reg_date = p.get('reg_date')
            
            if p_id and reg_date:
                # DB의 '상품번호' 컬럼과 아임웹의 'prod_no'를 대조
                sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
                cursor.execute(sql, (str(reg_date), str(p_id)))
                if cursor.rowcount > 0:
                    update_count += 1

        conn.commit()
        conn.close()
        print(f"✨ 작업 완료! {table_name} 테이블의 {update_count}개 상품 업데이트됨.")

    except Exception as e:
        print(f"❌ DB 작업 중 오류: {e}")

if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets 설정 확인 필요")
