import requests
import pandas as pd # CSV를 쓰신다면 필수
import os
import json

# 1. 보안 서버에서 API 키 가져오기
API_KEY = os.environ.get('IMWEB_API_KEY')

def get_imweb_dates():
    # 아임웹 API로 최신 상품 100개의 등록일 가져오기
    url = "https://api.imweb.me"
    headers = {"Access-Token": API_KEY}
    res = requests.get(url, headers=headers).json()
    
    # {상품번호: 등록일} 형태의 딕셔너리 생성
    date_map = {}
    for p in res.get('list', []):
        date_map[str(p['idx'])] = p['created_at'] # Unix Timestamp 또는 날짜 형식
    return date_map

# 2. 기존 데이터 파일 로드 및 업데이트 (예: data.csv 기준)
file_name = 'data.csv' # 실제 사용 중인 파일명으로 수정하세요!
if os.path.exists(file_name):
    df = pd.read_csv(file_name)
    dates = get_imweb_dates()
    
    # '상품번호' 컬럼을 기준으로 등록일 매칭 (컬럼명은 기존 파일에 맞게 수정)
    df['등록일'] = df['상품번호'].astype(str).map(dates).fillna(df.get('등록일', ''))
    df.to_csv(file_name, index=False)
    print("데이터 업데이트 완료!")
