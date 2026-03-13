import requests
import sqlite3
import os

# 1. 설정값 (GitHub Secrets에 등록된 API 키 사용)
API_KEY = os.environ.get('IMWEB_API_KEY')
DB_FILE = '상품검색 V4.db' # 실제 파일명과 대소문자까지 일치해야 합니다.

def get_imweb_dates():
    """아임웹 API로부터 상품 리스트를 가져오는 함수"""
    print("🌐 아임웹 API 연결 시도 중...")
    
    # 아임웹 상품 목록 API 엔드포인트 (V1 기준)
    url = "https://api.imweb.me"
    headers = {
        "Access-Token": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        res = requests.get(url, headers=headers)
        
        # 응답 상태 확인
        if res.status_code != 200:
            print(f"❌ API 호출 실패! 상태코드: {res.status_code}")
            print(f"응답 내용: {res.text}")
            return []

        # JSON 데이터 변환 및 상품 리스트 추출
        data = res.json()
        # 아임웹 API는 보통 {'data': {'list': [...]}} 구조입니다.
        product_list = data.get('data', {}).get('list', [])
        
        print(f"✅ 성공적으로 {len(product_list)}개의 상품 정보를 가져왔습니다.")
        return product_list

    except Exception as e:
        print(f"❌ API 요청 중 오류 발생: {e}")
        return []

def update_db():
    """가져온 데이터를 SQLite DB에 업데이트하는 함수"""
    # 1. DB 파일 존재 확인
    if not os.path.exists(DB_FILE):
        print(f"❌ 파일을 찾을 수 없습니다: {DB_FILE}")
        print("현재 경로의 파일 목록:", os.listdir('.'))
        return

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print(f"📂 DB 연결 완료: {DB_FILE}")

        # 2. '등록일' 컬럼이 없으면 추가
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN 등록일 TEXT")
            print("🆕 '등록일' 컬럼이 새로 추가되었습니다.")
        except sqlite3.OperationalError:
            print("ℹ️ '등록일' 컬럼이 이미 존재합니다.")

        # 3. 데이터 업데이트
        products = get_imweb_dates()
        update_count = 0

        for p in products:
            p_id = str(p.get('idx'))        # 아임웹 상품 번호
            reg_date = p.get('created_at')  # 등록일 (YYYY-MM-DD HH:MM:SS)
            
            if not p_id or not reg_date:
                continue

            # DB의 '상품번호' 컬럼과 아임웹의 'idx'를 매칭하여 업데이트
            # 만약 DB의 컬럼명이 '상품번호'가 아니라면 아래 이름을 수정하세요.
            cursor.execute("UPDATE products SET 등록일 = ? WHERE 상품번호 = ?", (reg_date, p_id))
            
            if cursor.rowcount > 0:
                update_count += 1

        conn.commit()
        print(f"✨ 업데이트 완료! (총 {update_count}개 상품)")

    except Exception as e:
        print(f"❌ DB 처리 중 오류 발생: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if not API_KEY:
        print("❌ 에러: API 키(IMWEB_API_KEY)가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
    else:
        update_db()
