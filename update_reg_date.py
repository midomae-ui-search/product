import requests
import sqlite3
import os

# 1. 설정 (GitHub Secrets에서 미도매의 전용 키를 가져옴)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get('IMWEB_API_SECRET')
DB_FILE = '상품검색 V4.db' 

def get_v2_token():
    """아임웹 본사 API 서버에 미도매 전용 키로 인증 요청"""
    print("🔑 V2 토큰 발급 시도 (공식 API 서버)...")
    # [중요] 주소는 반드시 api.imweb.me여야 합니다.
    url = "https://api.imweb.me" 
    
    payload = {
        "key": API_KEY,      # 미도매 전용 API KEY
        "secret": API_SECRET # 미도매 전용 API SECRET
    }
    
    try:
        # 400 에러 방지: json=payload 방식으로 전송
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            data = res.json()
            token = data.get('access_token')
            if token:
                print("✅ 미도매 데이터 접근 권한(토큰) 획득 성공!")
                return token
        
        print(f"❌ 인증 실패: {res.status_code}, {res.text[:100]}")
        return None
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def get_imweb_products_v2(token):
    """획득한 권한으로 미도매의 상품 목록 조회"""
    print("📦 미도매 상품 목록 조회 중...")
    url = "https://api.imweb.me"
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            items = res.json().get('data', {}).get('list', [])
            print(f"📋 총 {len(items)}개의 상품을 미도매 사이트에서 가져왔습니다.")
            return items
        return []
    except Exception as e:
        print(f"❌ 조회 오류: {e}")
        return []

# ... (이후 update_db 함수는 동일)

if __name__ == "__main__":
    update_db()
