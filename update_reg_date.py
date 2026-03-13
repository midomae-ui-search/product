import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """V2 전용 인증 토큰 발급 (JSON Body 방식 수정)"""
    print("🔑 V2 토큰 발급 시도...")
    # 경로 끝에 /v2/auth를 반드시 추가해야 합니다.
    url = "https://api.imweb.me" 
    
    # 400 에러 방지: params가 아니라 json(Body) 방식으로 전달
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    
    try:
        # json=payload로 데이터 전송
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            data = res.json()
            # V2 응답 구조: {'access_token': '...', 'expire_at': ...}
            token = data.get('access_token')
            if token:
                print("✅ V2 토큰 발급 성공!")
                return token
            else:
                print(f"❌ 토큰 추출 실패 (응답 구조 확인): {data}")
                return None
        else:
            # 여기서 400 HTML이 출력된다면 URL이나 Payload 형식이 틀린 것임
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기 (Endpoint 수정)"""
    print("📦 상품 목록 조회 중...")
    # 상품 조회를 위한 정확한 경로 추가
    url = "https://api.imweb.me"
    
    headers = {
        "Authorization": token,  # V2는 보통 Bearer 없이 토큰값만 넣습니다.
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            # V2 응답 구조: {'data': {'list': [...]}}
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
        
        # 테이블 이름 (공백/한글 포함 시 따옴표 처리)
        table_name = '"상품검색v4 260313"' 

        # '등록일' 컬럼 자동 생성 시도
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 새로 추가되었습니다.")
        except: 
            pass 

        update_count = 0
        for p in products:
            # V2 응답 필드명 확인 (prod_no -> prod_no)
            p_id = p.get('prod_no') 
            reg_date = p.get('reg_date') # 유닉스 타임스탬프 또는 문자열
            
            if p_id and reg_date:
                # DB 업데이트 실행
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
        print("❌ GitHub Secrets 설정 확인 필요 (API_KEY, API_SECRET)")
