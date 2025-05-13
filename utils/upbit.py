import requests

# 전체 KRW 마켓 코인 심볼 로드
def get_all_krw_symbols():
    url = "https://api.upbit.com/v1/market/all"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return [item['market'].split('-')[1] for item in res.json() if item['market'].startswith("KRW-")]
    except Exception as e:
        print(f"❌ 심볼 목록 오류: {e}")
        return []

# 해당 코인의 최근 2개의 1시간봉 캔들 거래량 반환    
def get_hourly_volumes(coin):
    url = f"https://api.upbit.com/v1/candles/minutes/60?market=KRW-{coin}&count=2"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if len(data) < 2:
            return None, None
        return data[1]['candle_acc_trade_volume'], data[0]['candle_acc_trade_volume']
    except Exception as e:
        print(f"❌ {coin} 거래량 조회 실패: {e}")
        return None, None

# 최근 'hours' 시간 동안의 평균 거래량과 현재 캔들 거래량을 비교
def get_volume_trend(coin, hours=6):
    url = f"https://api.upbit.com/v1/candles/minutes/60?market=KRW-{coin}&count={hours + 1}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if len(data) < hours + 1:
            return None, None
        current_volume = data[0]['candle_acc_trade_volume']
        avg_volume = sum(d['candle_acc_trade_volume'] for d in data[1:]) / hours
        return avg_volume, current_volume
    except Exception as e:
        print(f"❌ {coin} 거래량 추이 조회 실패: {e}")
        return None, None

# 지정 코인의 최근 10분간 가격 변화율 계산
def get_price_change_percent(symbol: str, minutes: int = 10):
    url = f"https://api.upbit.com/v1/candles/minutes/1?market=KRW-{symbol.upper()}&count={minutes + 1}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if len(data) < minutes + 1:
            return None
        current_price = data[0]['trade_price']
        past_price = data[-1]['trade_price']
        return round(((current_price - past_price) / past_price) * 100, 2)
    except Exception as e:
        print(f"❌ {symbol} 가격 변화율 조회 실패: {e}")
        return None

# 지정 코인의 최근 n개의 종가를 가져옴 (1시간봉 기준)
def get_candle_prices(coin, count=30):
    
    url = f"https://api.upbit.com/v1/candles/minutes/60?market=KRW-{coin}&count={count}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # response가 리스트가 아니면 잘못된 응답
        if not isinstance(data, list):
            print(f"⚠️ {coin} 캔들 요청 실패: 예상과 다른 응답형식 → {data}")
            return []

        return [candle['trade_price'] for candle in reversed(data)]  # 최신 → 과거
    except Exception as e:
        print(f"❌ {coin} 캔들 조회 실패: {e}")
        return []
    
# 일봉 캔들 데이터 가져오기
def get_daily_candles(coin, count=30):
    url = f"https://api.upbit.com/v1/candles/days?market=KRW-{coin}&count={count}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ {coin} 일봉 데이터 오류: {e}")
        return []
    
# currently unused    
def get_current_price(coin):
    url = f"https://api.upbit.com/v1/ticker?markets=KRW-{coin}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()[0]['trade_price']
    except Exception as e:
        print(f"❌ 가격 조회 실패: {e}")
        return None