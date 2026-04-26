from pywebio.input import input_group, input as p_input, select
from pywebio.output import put_markdown, put_success, put_warning, put_error, put_info, clear
from pywebio import start_server # 서버 실행을 위한 도구 추가
import os # 시스템 환경 설정을 읽어오기 위한 도구 추가

# 1. 수온과 조류 속도 데이터가 추가된 FISH_DB
FISH_DB = {
    "농어": {
        "min_wave": 0.5, "max_wave": 1.5, "max_wind": 6.0, "best_time": ["오전", "저녁", "야간"],
        "min_temp": 14, "max_temp": 22, "best_current": ["보통", "빠름"]
    },
    "광어": {
        "min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"],
        "min_temp": 14, "max_temp": 21, "best_current": ["느림", "보통"]
    },
    "우럭": {
        "min_wave": 0.0, "max_wave": 1.0, "max_wind": 7.0, "best_time": ["저녁", "야간"],
        "min_temp": 12, "max_temp": 20, "best_current": ["느림", "보통"]
    },
    "놀래미": {
        "min_wave": 0.0, "max_wave": 1.0, "max_wind": 6.0, "best_time": ["오전", "오후"],
        "min_temp": 11, "max_temp": 19, "best_current": ["느림", "보통"]
    },
    "삼치": {
        "min_wave": 0.0, "max_wave": 1.2, "max_wind": 7.0, "best_time": ["오전", "오후"],
        "min_temp": 17, "max_temp": 24, "best_current": ["보통", "빠름"]
    }
}

# 2. 가상 데이터 수집 함수
def get_ocean_data(location, target_date):
    return {
        "condition": "맑음", "temperature": 18, 
        "wind_speed": 3.5, "wind_direction": "북서풍", 
        "wave_height": 0.6, "water_temp": 16.5, 
        "is_real": False
    }

# 3. 조과 확률 분석 알고리즘
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
            reasons.append(f"✨ [가점] {fish}가 활발히 먹이 활동을 하는 아주 좋은 시간대입니다!")

        w_temp = ocean_data["water_temp"]
        if db["min_temp"] <= w_temp <= db["max_temp"]:
            score += 10
            reasons.append(f"✨ [가점] 현재 수온({w_temp}°C)이 {fish}가 활동하기 딱 좋은 적정 수온입니다.")
        elif w_temp < db["min_temp"]:
            score -= 25
            reasons.append(f"⚠️ [감점] 수온({w_temp}°C)이 너무 찹니다. {fish}의 활성도가 크게 떨어질 수 있습니다.")
        elif w_temp > db["max_temp"]:
            score -= 20
            reasons.append(f"⚠️ [감점] 수온({w_temp}°C)이 너무 높습니다.")

        if current_speed in db["best_current"]:
            score += 10
            reasons.append(f"✨ [가점] 현재 물때(조류: {current_speed})가 {fish} 낚시에 아주 적합합니다.")
        else:
            score -= 20
            reasons.append(f"⚠️ [감점] 조류 속도가 '{current_speed}'인 상황은 {fish} 낚시에 조금 불리합니다.")

        wave = ocean_data["wave_height"]
        if wave < db["min_wave"]:
            score -= 20
            reasons.append(f"⚠️ [감점] 파도가 너무 잔잔합니다. 최소 {db['min_wave']}m 이상은 되어야 좋습니다.")
        elif wave > db["max_wave"]:
            score -= 25
            reasons.append(f"⚠️ [감점] 파도가 {db['max_wave']}m를 넘어가면 낚시가 힘들어집니다.")

        if ocean_data["wind_speed"] > db["max_wind"]:
            score -= 15
            reasons.append(f"⚠️ [감점] 바람이 강해 낚시하기 불편할 수 있습니다.")
    else:
        reasons.append("ℹ️ DB에 없는 어종입니다. 일반적인 안전 기준으로만 평가합니다.")
        if ocean_data["wave_height"] > 1.5:
            score -= 30

    score = max(0, min(100, score))
    return score, reasons

def get_recommendation(fish):
    return {"date": "20260430", "location": "포항", "time_of_day": "오전", "current": "보통"}

# 4. 메인 화면 로직
def main():
    put_markdown("# 🎣 스마트 낚시 출조 도우미 (수온+조류 분석)")
    
    data = input_group("출조 정보 입력", [
        p_input("1. 출조 날짜 (예: 20260426)", name='date'),
        select("2. 출조 시간대", options=['오전', '오후', '저녁', '야간'], name='time_of_day'),
        select("3. 물때(조류 속도)", options=['느림 (조금~무시)', '보통 (1~4물, 11~14물)', '빠름 (사리 부근)'], name='current_speed'),
        p_input("4. 출조 지역 (예: 속초)", name='location'),
        p_input("5. 대상 어종 (예: 농어, 광어, 우럭, 놀래미, 삼치)", name='fish')
    ])
    
    current_speed = data['current_speed'].split(' ')[0] 
    
    clear()
    put_markdown(f"## 📊 [{data['location']}] 출조 분석 결과")
    
    ocean = get_ocean_data(data['location'], data['date'])
    
    put_markdown("---")
    put_markdown("### 📡 해양 및 기상 정보")
    put_markdown(f"- **날씨/기온:** {ocean['condition']}, {ocean['temperature']}°C\n- **풍속/파고:** {ocean['wind_speed']}m/s, {ocean['wave_height']}m\n- **수온/조류:** {ocean['water_temp']}°C, {current_speed}")
    
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
        
    if score < 50:
        rec = get_recommendation(data['fish'])
        put_info(f"💡 **추천 출조일:** {rec['date']} {rec['time_of_day']}(조류 {rec['current']})에 {rec['location']}로 떠나보세요!")

# 5. 서버용 앱 실행 방식 (핵심 변경 사항)
if __name__ == '__main__':
    # 클라우드 서버(Render)가 지정해주는 포트를 사용하도록 설정합니다.
    port = int(os.environ.get("PORT", 8080))
    start_server(main, port=port, debug=True)
