from pywebio.input import input_group, input as p_input, select
from pywebio.output import put_markdown, put_success, put_warning, put_error, put_info, clear
from pywebio import start_server
import requests
import os

# 1. API 인증키 입력 공간 (발급받은 키를 여기에 넣으세요!)
KMA_API_KEY = "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba"
KHOA_API_KEY = "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba"

# 2. 지역 번역 사전 (더 많은 지역은 나중에 추가할 수 있습니다)
LOCATION_MAP = {
    "속초": {"nx": 82, "ny": 143, "obs_code": "TW_0079"},
    "포항": {"nx": 102, "ny": 94, "obs_code": "TW_0062"},
    "부산": {"nx": 98, "ny": 76, "obs_code": "TW_0008"}
}

# 3. 어종 데이터베이스
FISH_DB = {
    "농어": {"min_wave": 0.5, "max_wave": 1.5, "max_wind": 6.0, "best_time": ["오전", "저녁", "야간"], "min_temp": 14, "max_temp": 22, "best_current": ["보통", "빠름"]},
    "광어": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"], "min_temp": 14, "max_temp": 21, "best_current": ["느림", "보통"]},
    "우럭": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 7.0, "best_time": ["저녁", "야간"], "min_temp": 12, "max_temp": 20, "best_current": ["느림", "보통"]},
    "놀래미": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"], "min_temp": 11, "max_temp": 19, "best_current": ["느림", "보통"]},
    "삼치": {"min_wave": 0.0, "max_wave": 1.2, "max_wind": 7.0, "best_time": ["오전", "오후"], "min_temp": 17, "max_temp": 24, "best_current": ["보통", "빠름"]}
}

# 4. 실제 API 서버와 통신하여 데이터를 가져오는 함수
def get_real_ocean_data(location_name, target_date):
    # 만약 사전에 없는 지역을 입력하거나, API 키를 아직 안 넣었다면 안전하게 가상 데이터 반환
    if location_name not in LOCATION_MAP or KMA_API_KEY == "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba":
        return {"condition": "맑음(가상)", "temperature": 18, "wind_speed": 3.5, "wind_direction": "북서풍", "wave_height": 0.6, "water_temp": 16.5, "is_real": False}

    loc_info = LOCATION_MAP[location_name]
    result_data = {"is_real": True}

    try:
        # 가. 기상청 API 호출 (단기예보) - 기온, 풍속, 하늘상태
        kma_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        kma_params = {
            'ServiceKey': KMA_API_KEY, 'pageNo': '1', 'numOfRows': '100', 'dataType': 'JSON',
            'base_date': target_date, 'base_time': '0500', # 오전 5시 발표 기준
            'nx': str(loc_info['nx']), 'ny': str(loc_info['ny'])
        }
        kma_res = requests.get(kma_url, params=kma_params).json()
        kma_items = kma_res['response']['body']['items']['item']
        
        # 복잡한 기상청 데이터 속에서 우리가 필요한 것만 골라냅니다.
        for item in kma_items:
            if item['category'] == 'TMP': # 기온
                result_data['temperature'] = float(item['fcstValue'])
            elif item['category'] == 'WSD': # 풍속
                result_data['wind_speed'] = float(item['fcstValue'])

        result_data['condition'] = "예보확인" # (하늘 상태 로직은 복잡하여 단순화)
        result_data['wind_direction'] = "예보확인"

        # 나. 국립해양조사원 API 호출 (바다낚시지수) - 수온, 파고
        khoa_url = "http://www.khoa.go.kr/oceangrid/grid/api/callApi.do"
        khoa_params = {
            'ServiceKey': KHOA_API_KEY, 'Type': 'JSON',
            'Target': 'OceanFishing', 'ObsCode': loc_info['obs_code'], 'Date': target_date
        }
        khoa_res = requests.get(khoa_url, params=khoa_params).json()
        
        # 해양 데이터 추출
        khoa_item = khoa_res['result']['data'][0] # 첫 번째 예보 데이터 가져오기
        result_data['water_temp'] = float(khoa_item['water_temp'])
        result_data['wave_height'] = float(khoa_item['wave_height'])

        return result_data

    except Exception as e:
        # 통신 에러가 나면 앱이 꺼지지 않도록 가상 데이터로 보호합니다.
        return {"condition": "통신오류", "temperature": 18, "wind_speed": 3.0, "wind_direction": "?", "wave_height": 0.5, "water_temp": 15.0, "is_real": False}

# 5. 조과 확률 분석 함수 (이전과 동일)
def analyze_fish_probability(fish, ocean_data, time_of_day, current_speed):
    score = 80
    reasons = []

    if fish in FISH_DB:
        db = FISH_DB[fish]
        if time_of_day not in db["best_time"]:
            score -= 15
            reasons.append(f"⚠️ [감점] {fish} 낚시는 주로 {', '.join(db['best_time'])} 시간대가 가장 유리합니다.")
        else:
            score += 10
            reasons.append(f"✨ [가점] 좋은 시간대입니다!")

        w_temp = ocean_data["water_temp"]
        if db["min_temp"] <= w_temp <= db["max_temp"]:
            score += 10
            reasons.append(f"✨ [가점] 수온({w_temp}°C)이 적당합니다.")
        else:
            score -= 20
            reasons.append(f"⚠️ [감점] 수온({w_temp}°C)이 적정 범위를 벗어났습니다.")

        if current_speed in db["best_current"]:
            score += 10
            reasons.append(f"✨ [가점] 물때(조류: {current_speed})가 적합합니다.")
        else:
            score -= 20
            reasons.append(f"⚠️ [감점] 조류 속도('{current_speed}')가 다소 불리합니다.")

        wave = ocean_data["wave_height"]
        if wave < db["min_wave"]:
            score -= 20
            reasons.append(f"⚠️ [감점] 파도가 너무 잔잔합니다.")
        elif wave > db["max_wave"]:
            score -= 25
            reasons.append(f"⚠️ [감점] 파도가 높아 낚시가 힘듭니다.")

        if ocean_data["wind_speed"] > db["max_wind"]:
            score -= 15
            reasons.append(f"⚠️ [감점] 바람이 강합니다.")
    else:
        reasons.append("ℹ️ DB에 없는 어종입니다.")
        
    return max(0, min(100, score)), reasons

def get_recommendation(fish):
    return {"date": "추후 업데이트", "location": "다른 지역", "time_of_day": "오전", "current": "보통"}

# 6. 메인 화면 로직
def main():
    put_markdown("# 🎣 스마트 낚시 출조 도우미 (실시간 데이터 연동)")
    
    data = input_group("출조 정보 입력", [
        p_input("1. 출조 날짜 (예: 20240501 - 당일이나 내일 날짜 입력)", name='date'),
        select("2. 출조 시간대", options=['오전', '오후', '저녁', '야간'], name='time_of_day'),
        select("3. 물때(조류 속도)", options=['느림 (조금~무시)', '보통 (1~4물, 11~14물)', '빠름 (사리 부근)'], name='current_speed'),
        p_input("4. 출조 지역 (지원지역: 속초, 포항, 부산)", name='location'),
        p_input("5. 대상 어종 (예: 농어, 광어, 우럭, 놀래미, 삼치)", name='fish')
    ])
    
    current_speed = data['current_speed'].split(' ')[0] 
    clear()
    put_markdown(f"## 📊 [{data['location']}] 출조 분석 결과")
    
    # 진짜 API 데이터를 요청합니다!
    ocean = get_real_ocean_data(data['location'], data['date'])
    
    put_markdown("---")
    if ocean['is_real']:
         put_success("📡 기상청 & 해양조사원 실시간 데이터 연결 성공!")
    else:
         put_error("⚠️ 테스트 모드 (인증키 오류, 미지원 지역, 또는 과거 날짜 입력 시 가상 데이터 출력)")

    put_markdown("### 🌊 해양 및 기상 정보")
    put_markdown(f"- **기온:** {ocean['temperature']}°C\n- **풍속:** {ocean['wind_speed']}m/s\n- **수온/조류:** {ocean['water_temp']}°C, {current_speed}\n- **파고:** {ocean['wave_height']}m")
    
    score, reasons = analyze_fish_probability(data['fish'], ocean, data['time_of_day'], current_speed)
    
    put_markdown("---")
    put_markdown("### 🤖 AI 조과 확률 분석")
    
    if score >= 70:
        put_success(f"**예상 낚시 성공률: {score}%** 🤩")
    elif score >= 50:
        put_warning(f"**예상 낚시 성공률: {score}%** 🤔")
    else:
        put_markdown(f"### 🚨 **예상 낚시 성공률: {score}%** 😥 (조건 불량)")
        
    for r in reasons:
        put_markdown(f"- {r}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    start_server(main, port=port, debug=True)
