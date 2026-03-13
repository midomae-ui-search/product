import requests
import sqlite3
import os

# 설정
API_KEY = os.environ.get('IMWEB_API_KEY')
DB_FILE = '상품검색 V4.db' 

def get_imweb_dates():
    # ⚠️ 아임웹 V1 API 주소
    url = "https://api.imweb.me"
    
    # ⚠️ 중요: Access-Token 앞에 빈칸이나 오타가 없는지 확인
    headers = {
        "Access-Token": str(API_KEY).strip(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0" # 일부 서버 거부 방지용
    }
    
    try:
        print(f"🌐 API 요청 중... (Key 앞부분: {str(API_KEY)[:5]}***)")
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"❌ API 호출 실패! 상태코드: {res.status_code}")
            print(f"응답 내용: {res.text}") # 에러 원인 출력
            return []

        data = res.json()
        return data.get('data', {}).get('list', [])
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return []

def update_db():
    if not os.path.exists(DB_FILE):
        print(f"❌ DB 파일을 찾을 수 없습니다: {DB_FILE}")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    table_name = '"상품검색v4 260312"' 

    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN 등록일 TEXT")
    except:
        pass 

    products = get_imweb_dates()
    update_count = 0

    print(f"🔄 총 {len(products)}개의 상품 데이터를 가져왔습니다.")

    for p in products:
        p_id = p.get('idx')
        reg_date = p.get('created_at')
        
        if p_id and reg_date:
            # 숫자로 비교하기 위해 CAST 사용
            sql = f"UPDATE {table_name} SET 등록일 = ? WHERE CAST(상품번호 AS TEXT) = ?"
            cursor.execute(sql, (reg_date, str(p_id)))
            if cursor.rowcount > 0:
                update_count += 1

    conn.commit()
    conn.close()
    print(f"✨ 업데이트 완료! 총 {update_count}개의 상품에 날짜가 입력되었습니다.")

if __name__ == "__main__":
    if not API_KEY:
        print("❌ IMWEB_API_KEY가 설정되지 않았습니다.")
    else:
        update_db()
