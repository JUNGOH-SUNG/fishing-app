from pywebio.input import input_group, input as p_input, select
from pywebio.output import put_markdown, put_success, put_warning, put_error, put_info, clear
from pywebio import start_server
import requests
import os

# 1. API 인증키 입력
KMA_API_KEY = "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba"
KHOA_API_KEY = "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba"

# 2. 전국 주요 바다낚시 지역 시/군 단위 상세 확대
# 기상청은 해당 시군의 좌표, 해양조사원은 가장 가까운 해역의 관측소 코드를 사용합니다.
LOCATION_MAP = {
    # 🌊 서해안 (경기, 충남, 전북)
    "인천": {"nx": 55, "ny": 124, "obs_code": "TW_0006"},
    "안산": {"nx": 58, "ny": 121, "obs_code": "TW_0006"}, # 인천 관측소 공유
    "화성": {"nx": 57, "ny": 119, "obs_code": "TW_0006"},
    "태안": {"nx": 51, "ny": 109, "obs_code": "TW_0056"}, # 보령 관측소 공유
    "서산": {"nx": 51, "ny": 114, "obs_code": "TW_0056"},
    "당진": {"nx": 53, "ny": 114, "obs_code": "TW_0056"},
    "보령": {"nx": 54, "ny": 100, "obs_code": "TW_0056"},
    "서천": {"nx": 55, "ny": 94, "obs_code": "TW_0035"},  # 군산 관측소 공유
    "군산": {"nx": 57, "ny": 90, "obs_code": "TW_0035"},
    "부안": {"nx": 56, "ny": 87, "obs_code": "TW_0035"},
    "목포": {"nx": 50, "ny": 67, "obs_code": "TW_0055"},
    "신안": {"nx": 50, "ny": 66, "obs_code": "TW_0055"},

    # 🌊 남해안 (전남, 경남, 부산)
    "해남": {"nx": 54, "ny": 57, "obs_code": "TW_0055"},
    "완도": {"nx": 57, "ny": 56, "obs_code": "TW_0055"},
    "고흥": {"nx": 66, "ny": 58, "obs_code": "TW_0069"},  # 여수 관측소 공유
    "여수": {"nx": 73, "ny": 66, "obs_code": "TW_0069"},
    "남해": {"nx": 77, "ny": 68, "obs_code": "TW_0066"},  # 통영 관측소 공유
    "사천": {"nx": 81, "ny": 68, "obs_code": "TW_0066"},
    "통영": {"nx": 87, "ny": 68, "obs_code": "TW_0066"},
    "거제": {"nx": 90, "ny": 69, "obs_code": "TW_0066"},
    "창원": {"nx": 90, "ny": 77, "obs_code": "TW_0008"},  # 부산 관측소 공유
    "부산": {"nx": 98, "ny": 76, "obs_code": "TW_0008"},

    # 🌊 동해안 (울산, 경북, 강원)
    "울산": {"nx": 102, "ny": 84, "obs_code": "TW_0068"},
    "경주": {"nx": 100, "ny": 91, "obs_code": "TW_0068"},
    "포항": {"nx": 102, "ny": 94, "obs_code": "TW_0062"},
    "영덕": {"nx": 102, "ny": 103, "obs_code": "TW_0062"}, # 포항 관측소 공유
    "울진": {"nx": 102, "ny": 115, "obs_code": "TW_0062"},
    "삼척": {"nx": 98, "ny": 125, "obs_code": "TW_0079"},  # 속초 관측소 공유
    "동해": {"nx": 97, "ny": 127, "obs_code": "TW_0079"},
    "강릉": {"nx": 92, "ny": 131, "obs_code": "TW_0079"},
    "양양": {"nx": 88, "ny": 138, "obs_code": "TW_0079"},
    "속초": {"nx": 82, "ny": 143, "obs_code": "TW_0079"},
    "고성(강원)": {"nx": 85, "ny": 145, "obs_code": "TW_0079"},

    # 🌊 제주권
    "제주시": {"nx": 52, "ny": 38, "obs_code": "TW_0070"},
    "서귀포시": {"nx": 53, "ny": 32, "obs_code": "TW_0071"}
}

# 3. 대상 어종 및 생태 조건 (유지)
FISH_DB = {
    "농어": {"min_wave": 0.5, "max_wave": 1.5, "max_wind": 6.0, "best_time": ["오전", "저녁", "야간"], "min_temp": 14, "max_temp": 22, "best_current": ["보통", "빠름"]},
    "광어": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"], "min_temp": 14, "max_temp": 21, "best_current": ["느림", "보통"]},
    "우럭": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 7.0, "best_time": ["저녁", "야간"], "min_temp": 12, "max_temp": 20, "best_current": ["느림", "보통"]},
    "놀래미": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"], "min_temp": 11, "max_temp": 19, "best_current": ["느림", "보통"]},
    "삼치": {"min_wave": 0.0, "max_wave": 1.2, "max_wind": 7.0, "best_time": ["오전", "오후"], "min_temp": 17, "max_temp": 24, "best_current": ["보통", "빠름"]},
    "감성돔": {"min_wave": 0.5, "max_wave": 1.2, "max_wind": 6.0, "best_time": ["오전", "저녁"], "min_temp": 15, "max_temp": 20, "best_current": ["보통"]},
    "벵에돔": {"min_wave": 0.0, "max_wave": 1.0, "max_wind": 5.0, "best_time": ["오전", "오후"], "min_temp": 16, "max_temp": 22, "best_current": ["느림", "보통"]},
    "참돔": {"min_wave": 0.0, "max_wave": 1.2, "max_wind": 6.0, "best_time": ["오전", "오후"], "min_temp": 16, "max_temp": 24, "best_current": ["보통", "빠름"]},
    "볼락": {"min_wave": 0.0, "max_wave": 0.5, "max_wind": 4.0, "best_time": ["저녁", "야간"], "min_temp": 12, "max_temp": 18, "best_current": ["느림"]},
    "갈치": {"min_wave": 0.0, "max_wave": 1.5, "max_wind": 8.0, "best_time": ["저녁", "야간"], "min_temp": 18, "max_temp": 26, "best_current": ["보통"]},
    "무늬오징어": {"min_wave": 0.0, "max_wave": 0.5, "max_wind": 4.0, "best_time": ["새벽", "야간"], "min_temp": 16, "max_temp": 24, "best_current": ["느림", "보통"]},
    "쭈꾸미": {"min_wave": 0.0, "max_wave": 0.5, "max_wind": 5.0, "best_time": ["오전", "오후"], "min_temp": 15, "max_temp": 22, "best_current": ["느림"]}
}

def convert_tide_to_speed(tide_text):
    if not tide_text:
        return "보통"
    tide_text = str(tide_text)
    if any(keyword in tide_text for keyword in ["조금", "무시", "1물", "2물", "3물", "12물", "13물", "14물"]):
        return "느림"
    elif any(keyword in tide_text for keyword in ["6물", "7물", "8물", "9물", "10물", "사리", "대조"]):
        return "빠름"
    else:
        return "보통"

# 4. 실제 API 서버 연동 함수
def get_real_ocean_data(location_name, target_date):
    if location_name not in LOCATION_MAP or KMA_API_KEY == "2a52c711a2f81cc1feafb94b55e0e52e39d069ab5b55352ebb691d83217e1cba":
        return {"condition": "맑음", "temperature": 18, "wind_speed": 3.5, "wind_direction": "북서풍", "wave_height": 0.6, "water_temp": 16.5, "current_speed": "보통", "raw_tide": "7물(가상)", "is_real": False}

    loc_info = LOCATION_MAP[location_name]
    result_data = {"is_real": True}

    try:
        kma_url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
        kma_params = {
            'ServiceKey': KMA_API_KEY, 'pageNo': '1', 'numOfRows': '100', 'dataType': 'JSON',
            'base_date': target_date, 'base_time': '0500',
            'nx': str(loc_info['nx']), 'ny': str(loc_info['ny'])
        }
        kma_res = requests.get(kma_url, params=kma_params).json()
        kma_items = kma_res['response']['body']['items']['item']
        
        for item in kma_items:
            if item['category'] == 'TMP':
                result_data['temperature'] = float(item['fcstValue'])
            elif item['category'] == 'WSD':
                result_data['wind_speed'] = float(item['fcstValue'])

        khoa_url = "http://www.khoa.go.kr/oceangrid/grid/api/callApi.do"
        khoa_params = {
            'ServiceKey': KHOA_API_KEY, 'Type': 'JSON',
            'Target': 'OceanFishing', 'ObsCode': loc_info['obs_code'], 'Date': target_date
        }
        khoa_res = requests.get(khoa_url, params=khoa_params).json()
        khoa_item = khoa_res['result']['data'][0] 
        
        result_data['water_temp'] = float(khoa_item['water_temp'])
        result_data['wave_height'] = float(khoa_item['wave_height'])
        raw_tide = khoa_item.get('tide_name', khoa_item.get('tide_time', '정보없음'))
        result_data['raw_tide'] = raw_tide
        result_data['current_speed'] = convert_tide_to_speed(raw_tide)

        return result_data

    except Exception as e:
        return {"condition": "오류", "temperature": 0, "wind_speed": 0, "wave_height": 0, "water_temp": 0, "current_speed": "보통", "raw_tide": "통신오류", "is_real": False}

# 5. 조과 확률 분석 알고리즘
def analyze_fish_probability(fish, ocean_data, time_of_day):
    score = 80
    reasons = []
    current_speed = ocean_data["current_speed"]
    db = FISH_DB[fish]
    
    if time_of_day not in db["best_time"]:
        score -= 15
        reasons.append(f"⚠️ [감점] {fish} 낚시는 주로 {', '.join(db['best_time'])} 시간대가 가장 유리합니다.")
    else:
        score += 10
        reasons.append(f"✨ [가점] 대상어종이 먹이활동을 하기 좋은 시간대입니다!")

    w_temp = ocean_data["water_temp"]
    if db["min_temp"] <= w_temp <= db["max_temp"]:
        score += 10
        reasons.append(f"✨ [가점] 수온({w_temp}°C)이 적당합니다.")
    else:
        score -= 20
        reasons.append(f"⚠️ [감점] 수온({w_temp}°C)이 적정 범위를 벗어났습니다.")

    if current_speed in db["best_current"]:
        score += 10
        reasons.append(f"✨ [가점] 현재의 조류 속도({current_speed})가 적합합니다.")
    else:
        score -= 20
        reasons.append(f"⚠️ [감점] 현재 조류 속도({current_speed})가 다소 불리합니다.")

    wave = ocean_data["wave_height"]
    if wave < db["min_wave"]:
        score -= 20
        reasons.append(f"⚠️ [감점] 파도가 너무 잔잔합니다.")
    elif wave > db["max_wave"]:
        score -= 25
        reasons.append(f"⚠️ [감점] 파도가 높아 낚시가 힘듭니다.")

    if ocean_data["wind_speed"] > db["max_wind"]:
        score -= 15
        reasons.append(f"⚠️ [감점] 바람이 강해 캐스팅이 어렵습니다.")
        
    return max(0, min(100, score)), reasons

# 6. 메인 화면 로직
def main():
    put_markdown("# 🎣 전국 스마트 낚시 출조 도우미")
    
    location_list = list(LOCATION_MAP.keys())
    fish_list = list(FISH_DB.keys())
    
    data = input_group("출조 정보 선택", [
        p_input("1. 출조 날짜 (예: 20260428 - 당일이나 내일 날짜 입력)", name='date'),
        select("2. 출조 시간대", options=['오전', '오후', '저녁', '야간'], name='time_of_day'),
        select("3. 출조 지역", options=location_list, name='location'),
        select("4. 대상 어종", options=fish_list, name='fish')
    ])
    
    clear()
    put_markdown(f"## 📊 [{data['location']}] 출조 분석 결과")
    
    ocean = get_real_ocean_data(data['location'], data['date'])
    raw_tide = ocean['raw_tide']
    
    put_markdown("---")
    if ocean['is_real']:
         put_success("📡 기상청 & 해양조사원 실시간 데이터 연결 성공!")
    else:
         put_error("⚠️ 테스트 모드 (인증키 미등록, 또는 과거 날짜 입력 시 출력됨)")

    put_markdown("### 🌊 해양 및 기상 정보")
    put_markdown(f"- **상세 물때:** **{raw_tide}**\n- **기온:** {ocean['temperature']}°C\n- **풍속:** {ocean['wind_speed']}m/s\n- **수온:** {ocean['water_temp']}°C\n- **파고:** {ocean['wave_height']}m")
    
    score, reasons = analyze_fish_probability(data['fish'], ocean, data['time_of_day'])
    
    put_markdown("---")
    put_markdown(f"### 🤖 AI 조과 확률 분석 ({data['fish']})")
    
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
