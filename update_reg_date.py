import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급 (응답 구조 정밀 수정)"""
    print("🔑 V2 토큰 발급 시도...")
    # 경로 끝에 /v2/auth가 반드시 포함되어야 합니다.
    url = "https://api.imweb.me" 
    
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        # 아임웹 V2는 JSON 형식으로 데이터를 보낼 때 가장 안정적입니다.
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            data = res.json()
            # 아임웹 V2 응답 형태에 따라 access_token을 직접 가져오거나 data 내부에서 가져옵니다.
            token = data.get('access_token') or data.get('data', {}).get('access_token')
            
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
            else:
                print(f"❌ 토큰 필드를 찾을 수 없음: {data}")
                return None
        else:
            # 400 에러 시 서버가 보낸 텍스트 내용을 출력하여 원인을 더 구체적으로 파악합니다.
            print(f"❌ 인증 실패: {res.status_code}")
            if "<html>" in res.text:
                print("⚠️ 원인: 서버가 API 요청을 이해하지 못하고 에러 페이지(HTML)를 보냈습니다. (URL 또는 요청방식 오류)")
            else:
                print(f"메시지: {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기"""
    print("📦 상품 목록 조회 중...")
    url = "https://api.imweb.me"
    
    headers = {
        # V2는 토큰 앞에 'Bearer '를 붙이지 않는 것이 기본 설정인 경우가 많습니다.
        "Authorization": token, 
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            res_data = res.json()
            # V2 응답 구조: {'data': {'list': [...]}}
            items = res_data.get('data', {}).get('list', [])
            print(f"📋 총 {len(items)}개의 상품 데이터를 가져왔습니다.")
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
        
        # 테이블 이름 (날짜 확인: 260313)
        table_name = '"상품검색v4 260313"' 

        # '등록일' 컬럼 추가 (없을 경우에만)
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
                # DB의 '상품번호'와 API의 'prod_no'를 매칭
                sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
                cursor.execute(sql, (str(reg_date), str(p_id)))
                if cursor.rowcount > 0:
                    update_count += 1

        conn.commit()
        conn.close()
        print(f"✨ 작업 완료! {update_count}개 상품 업데이트됨.")

    except Exception as e:
        print(f"❌ DB 작업 중 오류: {e}")

if __name__ == "__main__":
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets 설정 확인 필요")
