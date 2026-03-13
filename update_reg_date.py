def get_v2_token():
    """V2 전용 인증 토큰 발급"""
    print("🔑 V2 토큰 발급 시도...")
    # 수정: /v2/auth 경로 추가
    url = "https://api.imweb.me/v2/auth" 
    payload = {
        "key": API_KEY,
        "secret": API_SECRET
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code == 200:
            token = res.json().get('data', {}).get('access_token')
            print("✅ V2 토큰 발급 성공!")
            return token
        else:
            print(f"❌ 인증 실패: {res.status_code}, {res.text}")
            return None
    except Exception as e:
        print(f"❌ 인증 오류: {e}")
        return None

def get_imweb_products_v2(token):
    """V2 API로 상품 목록 가져오기"""
    # 수정: /v2/shop/products 경로 추가
    url = "https://api.imweb.me/v2/shop/products"
    # 수정: Authorization 헤더 방식 적용 (Bearer 방식)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json().get('data', {})
            # 아임웹 V2는 보통 'list' 필드에 상품 목록이 들어있습니다.
            return data.get('list', []) 
        else:
            print(f"❌ 상품 조회 실패: {res.status_code}, {res.text}")
            return []
    except Exception as e:
        print(f"❌ 조회 오류: {e}")
        return []
