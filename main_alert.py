import requests
import time
import schedule
from telegram import Bot
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import csv
from utils.upbit import (
    get_all_krw_symbols,
    get_candle_prices,
    get_minute_candles,
    get_hourly_volumes,
    get_volume_trend
)
from utils.indicators import calculate_rsi

# 로그 설정
log_dir = os.path.join(os.getcwd(), "upbit_logs")
os.makedirs(log_dir, exist_ok=True)

today = datetime.now().strftime('%Y-%m-%d')
log_file_path = os.path.join(log_dir, f"log_{today}.txt")

import sys

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 환경변수 로드
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 관심 있는 코인 (실시간 감지용)
COINS_FIXED = ["MEW", "XRP", "DOGE", "MOVE", "PUNDIX", "LAYER", "VIRTUAL", "KAITO", "BTC", "ETH", "ONDO"]
COIN_NAMES = {
    "MEW": "캣인어독스월드", "XRP": "리플", "DOGE": "도지", "MOVE": "무브먼트",
    "PUNDIX": "펀디엑스", "LAYER": "솔레이어", "VIRTUAL": "버추얼프로토콜",
    "KAITO": "카이토", "BTC": "비트코인", "ETH": "이더리움", "ONDO": "온도파이낸스"
}

# 실시간 감지 조건
PRICE_THRESHOLD_PERCENT = 3 # 가격 3%
VOLUME_THRESHOLD_MULTIPLIER = 2 # 거래량 2배
CHECK_INTERVAL = 120 # 2분

# 실시간 감지 시간
STOP_START_TIME = "22:55"
STOP_END_TIME = "07:00"

# 예측 시간
NIGHT_TIME = "23:00"
MORNING_TIME = "07:30"

bot = Bot(token=TELEGRAM_TOKEN)
previous_data = {coin: {'price': None, 'volume': None} for coin in COINS_FIXED}
night_candidates = {}

# 실시간 시장 감시: 가격 및 거래량 변동 감지 후 텔레그램 알림 (3%, 2배, 2분)
def check_market():
    now = datetime.now().time()
    # 22:55 ~ 07:00 사이엔 실행 안 함
    if now >= datetime.strptime(STOP_START_TIME, "%H:%M").time() or now <= datetime.strptime(STOP_END_TIME, "%H:%M").time():
        return

    try:
        # 모든 티커 정보를 한 번에 가져오기
        url = f"https://api.upbit.com/v1/ticker?markets=" + ",".join([f"KRW-{c}" for c in COINS_FIXED])
        res = requests.get(url)
        res.raise_for_status()
        ticker_data = {item['market'].split('-')[1]: item for item in res.json()}

    except Exception as e:
        logging.error(f"❌ 티커 전체 조회 실패: {e}")
        print(f"❌ 티커 전체 조회 실패: {e}")
        return

    for coin in COINS_FIXED:
        try:
            data = ticker_data.get(coin)
            if not data:
                continue

            current_price = data['trade_price']

            # 🟡 캔들 거래량 가져오기 (API 1회)
            prev_volume, current_volume = get_hourly_volumes(coin)
            if not prev_volume or not current_volume:
                logging.debug(f"🔸 {coin} 캔들 거래량 부족 → 스킵")
                print(f"🔸 {coin} 캔들 거래량 부족 → 스킵")
                continue

            volume_change = current_volume / prev_volume if prev_volume > 0 else 0

            prev_price = previous_data[coin]['price']
            if not prev_price:
                previous_data[coin]['price'] = current_price
                previous_data[coin]['volume'] = current_volume
                continue

            price_change = ((current_price - prev_price) / prev_price) * 100

            timestamp = datetime.now().strftime('%H:%M:%S')
            color = "\033[91m" if price_change >= 0 else "\033[94m"
            reset = "\033[0m"
            logging.info(f"[{timestamp}] [{coin}] 변화율: {price_change:.2f}% / 거래량 x{volume_change:.2f}")
            print(f"[{timestamp}] [{coin}] 변화율: {price_change:.2f}% / 거래량 x{volume_change:.2f}")

            if price_change >= PRICE_THRESHOLD_PERCENT and volume_change >= VOLUME_THRESHOLD_MULTIPLIER:
                chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                name = COIN_NAMES.get(coin, coin)
                message = (
                    f"🚨 [{name}] {coin} 급등 감지!\n"
                    f"가격: {current_price}원 ({price_change:.2f}%↑)\n"
                    f"거래량: {volume_change:.1f}배 증가\n"
                    f"[👉 차트 보기]({chart_url})"
                )
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                print(f"🚨 알림 전송됨: {coin} ({price_change:.2f}% 상승, x{volume_change:.1f} 거래량)")

            # 상태 갱신
            previous_data[coin]['price'] = current_price
            previous_data[coin]['volume'] = current_volume

        except Exception as e:
            logging.error(f"❌ {coin} 실시간 감시 중 오류: {e}")
            print(f"❌ {coin} 실시간 감시 중 오류: {e}")

        time.sleep(0.2)  # 너무 빠르게 거래량 요청하지 않도록 약간 유지

# 실시간 시장 감시 (민감 버전): 최근 3분 내 저점 대비 3% 이상 상승 + 거래량 1.5배 이상
def check_market_sensitive():
    now = datetime.now().time()
    if now >= datetime.strptime(STOP_START_TIME, "%H:%M").time() or now <= datetime.strptime(STOP_END_TIME, "%H:%M").time():
        return

    try:
        url = f"https://api.upbit.com/v1/ticker?markets=" + ",".join([f"KRW-{c}" for c in COINS_FIXED])
        res = requests.get(url)
        res.raise_for_status()
        ticker_data = {item['market'].split('-')[1]: item for item in res.json()}
    except Exception as e:
        logging.error(f"❌ 티커 전체 조회 실패 (민감 버전): {e}")
        print(f"❌ 티커 전체 조회 실패 (민감 버전): {e}")
        return

    for coin in COINS_FIXED:
        try:
            data = ticker_data.get(coin)
            if not data:
                continue

            current_price = data['trade_price']

            # 🔍 1분봉 3개 → 저점 기준 가격 변동률 계산
            candles = get_minute_candles(coin, count=3)
            if not candles:
                continue

            recent_lows = [candle['low_price'] for candle in candles]
            min_price = min(recent_lows)
            price_change = ((current_price - min_price) / min_price) * 100

            # 🔍 거래량 변화율 확인 (1시간 기준)
            prev_volume, current_volume = get_hourly_volumes(coin)
            if not prev_volume or not current_volume:
                logging.debug(f"🔸 {coin} 거래량 부족 → 스킵")
                print(f"🔸 {coin} 거래량 부족 → 스킵")
                continue

            volume_change = current_volume / prev_volume if prev_volume > 0 else 0

            timestamp = datetime.now().strftime('%H:%M:%S')
            logging.info(f"[민감 {timestamp}] [{coin}] 저점대비 변화율: {price_change:.2f}% / 거래량 x{volume_change:.2f}")
            print(f"[민감 {timestamp}] [{coin}] 저점대비 변화율: {price_change:.2f}% / 거래량 x{volume_change:.2f}")
            
            if price_change >= 3.0 and volume_change >= 1.5:
                chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                name = COIN_NAMES.get(coin, coin)
                message = (
                    f"🚨 [민감] [{name}] {coin} 급등 감지!\n"
                    f"가격: {current_price}원 ({price_change:.2f}%↑)\n"
                    f"거래량: {volume_change:.1f}배 증가\n"
                    f"[👉 차트 보기]({chart_url})"
                )
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                logging.info(f"🚨 민감 알림 전송됨: {coin} (+{price_change:.2f}%, x{volume_change:.1f})")
                print(f"🚨 민감 알림 전송됨: {coin} (+{price_change:.2f}%, x{volume_change:.1f})")

        except Exception as e:
            logging.error(f"❌ {coin} 민감 감시 오류: {e}")
            print(f"❌ {coin} 민감 감시 오류: {e}")
        time.sleep(0.2)


# 야간 예측 스캔: RSI 및 거래량 변화를 바탕으로 후보 선정
def nightly_scan():
    logging.info("🌙 야간 예측 스캔 시작")
    print("🌙 야간 예측 스캔 시작")
    COINS = get_all_krw_symbols()
    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in COINS])
    response = requests.get(url).json()

    message_lines = ["🌙 [야간 후보 리스트]"]

    for data in response:
        coin = data['market'].split('-')[1]
        price = data['trade_price']

        avg_volume, current_volume = get_volume_trend(coin, hours=6)
        if not avg_volume or not current_volume:
            logging.info(f"🔸 {coin} 거래량 데이터 부족 → 스킵")
            print(f"🔸 {coin} 거래량 데이터 부족 → 스킵")
            continue

        volume_change = current_volume / avg_volume if avg_volume > 0 else 0

        prices = get_candle_prices(coin)
        if not prices:
            logging.info(f"🔸 {coin} 캔들 가격 없음 → 스킵")
            print(f"🔸 {coin} 캔들 가격 없음 → 스킵")
            continue

        time.sleep(0.15)
        rsi = calculate_rsi(prices)

        if rsi is not None:
            logging.info(f"🔍 {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}")
            print(f"🔍 {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}")
        else:
            logging.info(f"🔸 {coin} RSI 계산 실패 → 스킵")
            print(f"🔸 {coin} RSI 계산 실패 → 스킵")

        if 35 < rsi < 55 and volume_change > 1.5:
            night_candidates[coin] = {
                'price': price,
                'volume': current_volume,
                'rsi': rsi
            }
            line = f"- {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}"
            message_lines.append(line)
            save_night_candidate_to_csv(coin, rsi, volume_change, price)
            logging.info(f"🕵️‍♂️ 후보 등록: {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}")
            print(f"🕵️‍♂️ 후보 등록: {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}")

    if len(message_lines) > 1:
        message_lines.append("\n🕐 내일 아침 급등 가능성 있는 후보입니다.")
        bot.send_message(chat_id=CHAT_ID, text="\n".join(message_lines))
    else:
        bot.send_message(chat_id=CHAT_ID, text="🌙 오늘은 야간 예측 후보가 없습니다.")

# 아침 후보 검증: 전날 선정된 후보의 아침 결과를 확인 및 알림
def morning_check():
    logging.info("🌅 아침 후보 검증 시작")
    print("🌅 아침 후보 검증 시작")

    if not night_candidates:
        bot.send_message(chat_id=CHAT_ID, text="🌅 아침 후보가 없습니다.")
        return

    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in night_candidates])
    response = requests.get(url).json()

    message_lines = ["🌅 [전날 후보 아침 결과]"]
    found_risers = False

    for data in response:
        coin = data['market'].split('-')[1]
        morning_price = data['trade_price']
        prev_info = night_candidates.get(coin)
        if not prev_info:
            continue
        rise = ((morning_price - prev_info['price']) / prev_info['price']) * 100
        name = COIN_NAMES.get(coin, coin)
        chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
        line = (
            f"- [{name}] {coin} | 밤: {int(prev_info['price'])} → 아침: {int(morning_price)}원 | "
            f"수익률: {rise:.2f}%"
        )
        message_lines.append(line)

        # csv 파일에 저장
        save_morning_result_to_csv(coin, prev_info['price'], morning_price, rise)
        # 수익률 5% 이상인 경우 별도 알림
        if rise >= 5:
            alert = (
                f"☀️ [{name}] {coin} 새벽 급등!\n"
                f"밤 가격: {int(prev_info['price'])}원 → 아침 가격: {int(morning_price)}원\n"
                f"수익률: +{rise:.2f}%\n"
                f"[👉 차트 보기]({chart_url})"
            )
            bot.send_message(chat_id=CHAT_ID, text=alert, parse_mode='Markdown')
            
            logging.info(f"☀️ 아침 알림 전송됨: {coin} +{rise:.2f}%")
            print(f"☀️ 아침 알림 전송됨: {coin} +{rise:.2f}%")
            found_risers = True

    # 요약 결과 전송
    if len(message_lines) > 1:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(message_lines))
    elif not found_risers:
        bot.send_message(chat_id=CHAT_ID, text="🌅 아침 후보는 있었지만 변화가 없었습니다.")

# 야간 후보 데이터를 CSV 파일에 저장
def save_night_candidate_to_csv(coin, rsi, volume_change, price):
    today = datetime.now().strftime('%Y-%m-%d')
    log_dir = "upbit_logs"
    filename = f"{log_dir}/night_candidates_{today}.csv"

    # 디렉토리 없으면 생성
    os.makedirs(log_dir, exist_ok=True)

    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "coin", "rsi", "volume_change", "price"])
        writer.writerow([datetime.now().strftime('%Y-%m-%d'), coin, rsi, volume_change, price])

# 아침 결과 데이터를 CSV 파일에 저장
def save_morning_result_to_csv(coin, prev_price, morning_price, rise):
    today = datetime.now().strftime('%Y-%m-%d')
    log_dir = "upbit_logs"
    filename = f"{log_dir}/morning_results_{today}.csv"

    # 디렉토리 없으면 생성
    os.makedirs(log_dir, exist_ok=True)

    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "coin", "night_price", "morning_price", "rise_percent"])
        writer.writerow([datetime.now().strftime('%Y-%m-%d'), coin, prev_price, morning_price, f"{rise:.2f}"])

# 스케줄 등록
schedule.every(CHECK_INTERVAL).seconds.do(check_market)
schedule.every(CHECK_INTERVAL).seconds.do(check_market_sensitive)
schedule.every().day.at(NIGHT_TIME).do(nightly_scan)
schedule.every().day.at(MORNING_TIME).do(morning_check)

print(f"🔔 실시간 감시 대상: {', '.join(COINS_FIXED)}")

while True:
    schedule.run_pending()
    time.sleep(1)
