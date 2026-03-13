import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 안전하게 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급 (400 에러 해결 버전)"""
    print("🔑 V2 토큰 발급 시도...")
    # 아임웹 V2 인증 엔드포인트
    url = "https://api.imweb.me" 
    
    # 400 에러 해결을 위해 params(쿼리 스트링) 방식으로 전달
    params = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        # 인증 요청 (V2 규격: POST 방식 + URL 파라미터)
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
    """V2 API로 상품 목록 가져오기"""
    print("📦 상품 목록 조회 중...")
    url = "https://api.imweb.me"
    
    # V2 공식 인증 헤더 (Bearer 방식)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # V2 응답 구조의 'list' 필드에서 상품 추출
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
    # DB 파일 존재 여부 확인
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일이 저장소에 없습니다: {DB_FILE}")
        return

    # 1. 토큰 발급
    token = get_v2_token()
    if not token: 
        print("🛑 인증 단계에서 중단되었습니다.")
        return

    # 2. 아임웹 상품 정보 가져오기
    products = get_imweb_products_v2(token)
    if not products:
        print("📭 업데이트할 상품 데이터가 없습니다.")
        return

    # 3. DB 업데이트 실행
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 테이블 이름 (공백 주의)
        table_name = '"상품검색v4 260312"' 

        # '등록일' 컬럼이 없으면 자동 생성
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 새로 추가되었습니다.")
        except: 
            pass 

        update_count = 0
        for p in products:
            # 아임웹 V2 필드명: prod_no(번호), reg_date(등록일)
            p_id = p.get('prod_no') 
            reg_date = p.get('reg_date')
            
            if p_id and reg_date:
                # DB의 '상품번호'와 아임웹의 'prod_no' 대조하여 '등록일' 업데이트
                sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
                cursor.execute(sql, (str(reg_date), str(p_id)))
                if cursor.rowcount > 0:
                    update_count += 1

        conn.commit()
        conn.close()
        print(f"✨ 작업 완료! 총 {update_count}개의 상품 정보를 DB에 기록했습니다.")

    except Exception as e:
        print(f"❌ DB 작업 중 오류: {e}")

if __name__ == "__main__":
    # Key 존재 여부 최종 확인
    if API_KEY and API_SECRET:
        update_db()
    else:
        print("❌ GitHub Secrets에 API_KEY 또는 API_SECRET이 설정되지 않았습니다.")
