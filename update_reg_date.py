import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """아임웹 V2 인증 (JSON 방식 고정)"""
    print("🔑 V2 토큰 발급 시도 (api.imweb.me)...")
    url = "https://api.imweb.me" 
    
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        # json=payload로 보내야 400 에러(HTML)를 피할 수 있습니다.
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
    url = "https://api.imweb.me"
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('list', [])
            print(f"📋 총 {len(items)}개의 상품을 아임웹에서 가져왔습니다.")
            return items
        print(f"❌ 상품 조회 실패: {res.status_code}")
        return []
    except Exception as e:
        print(f"❌ 조회 오류 발생: {e}")
        return []

def update_db():
    """DB 업데이트 메인 함수"""
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
        
        # 테이블 이름 (날짜 확인: 260313)
        table_name = '"상품검색v4 260313"' 

        # '등록일' 컬럼 추가 시도
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 추가되었습니다.")
        except: 
            pass 

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
        print(f"❌ DB 작업 중 오류: {e}")

# [중요] 프로그램의 시작점 - 들여쓰기 없이 가장 왼쪽에 있어야 합니다.
if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets 설정 확인 필요")
