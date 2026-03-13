import requests
import os

# 1. 설정 (GitHub Secrets)
API_KEY = os.environ.get('IMWEB_API_KEY')
API_SECRET = os.environ.get	('IMWEB_API_SECRET')

def get_v2_token_final():
    print("🔑 미도매 V2 인증 시도 중...")
    # [중요] V2 공식 엔드포인트 주소
    url = "https://api.imweb.me/v2/auth/token" 
    
    # 아임웹 V2가 요구하는 정확한 데이터 구조
    payload = {
        "client_id": API_KEY,      # 'key'를 'client_id'로 변경
        "client_secret": API_SECRET # 'secret'을 'client_secret'으로 변경
    }
    
    # 헤더에 JSON 형식임을 명시 (400 HTML 방지 핵심)
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        # json=payload를 사용하여 데이터를 전송합니다.
        res = requests.post(url, json=payload, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            token = data.get('access_token')
            if token:
                print("✅ 인증 성공! 토큰을 발급받았습니다.")
                return token
        
        # 실패 시 서버가 보낸 메시지를 정확히 출력합니다.
        print(f"❌ 인증 실패 (코드: {res.status_code})")
        print(f"❌ 서버 메시지: {res.text[:200]}")
        return None
        
    except Exception as e:
        print(f"❌ 네트워크 오류: {e}")
        return None

if __name__ == "__main__":
    token = get_v2_token_final()
    if token:
        print(f"발급된 토큰: {token[:10]}...")
