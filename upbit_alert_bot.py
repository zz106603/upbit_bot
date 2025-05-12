import requests
import time
import schedule
from telegram import Bot
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# 로그 설정
if not os.path.exists("upbit_logs"):
    os.makedirs("upbit_logs")

today = datetime.now().strftime('%Y-%m-%d')
log_file_path = f"upbit_logs/log_{today}.txt"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# .env 로드
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 관심 있는 코인 (실시간 감지용)
COINS_FIXED = ["MEW", "XRP", "DOGE", "MOVE", "PUNDIX", "LAYER", "VIRTUAL", "KAITO", "BTC", "ETH", "ONDO"]
PRICE_THRESHOLD_PERCENT = 4
VOLUME_THRESHOLD_MULTIPLIER = 2
CHECK_INTERVAL = 60

bot = Bot(token=TELEGRAM_TOKEN)
previous_data = {coin: {'price': None, 'volume': None} for coin in COINS_FIXED}
night_candidates = {}

COIN_NAMES = {
    "MEW": "캣인어독스월드", "XRP": "리플", "DOGE": "도지", "MOVE": "무브먼트",
    "PUNDIX": "펀디엑스", "LAYER": "솔레이어", "VIRTUAL": "버추얼프로토콜",
    "KAITO": "카이토", "BTC": "비트코인", "ETH": "이더리움", "ONDO": "온도파이낸스"
}

def check_market():
    now = datetime.now().time()
    # 예: 01:00 ~ 06:00 사이엔 실행 안 함
    if now >= datetime.strptime("01:00", "%H:%M").time() and now <= datetime.strptime("07:00", "%H:%M").time():
        return  # 새벽에는 감지 스킵
    
    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in COINS_FIXED])
    response = requests.get(url).json()

    for data in response:
        coin = data['market'].split('-')[1]
        current_price = data['trade_price']
        current_volume = data['acc_trade_volume_24h']

        prev_price = previous_data[coin]['price']
        prev_volume = previous_data[coin]['volume']

        if prev_price and prev_volume:
            price_change = ((current_price - prev_price) / prev_price) * 100
            volume_change = current_volume / prev_volume if prev_volume > 0 else 0

            timestamp = datetime.now().strftime('%H:%M:%S')
            color = "\033[91m" if price_change >= 0 else "\033[94m"
            reset = "\033[0m"
            print(f"{color}[{timestamp}] [{coin}] 변화율: {price_change:.2f}% / 거래량 x{volume_change:.2f}{reset}")

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
                logging.info(f"🚨 알림 전송됨: {coin} ({price_change:.2f}% 상승, x{volume_change:.1f} 거래량)")

        previous_data[coin]['price'] = current_price
        previous_data[coin]['volume'] = current_volume

def get_all_krw_coins():
    url = "https://api.upbit.com/v1/market/all"
    response = requests.get(url).json()
    return [item['market'].split('-')[1] for item in response if item['market'].startswith("KRW-")]

def get_candle_prices(coin, count=30):
    url = f"https://api.upbit.com/v1/candles/minutes/60?market=KRW-{coin}&count={count}"
    response = requests.get(url).json()
    if not response or 'error' in response:
        return []
    return [candle['trade_price'] for candle in reversed(response)]

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        gain = gains[i]
        loss = losses[i]
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def nightly_scan():
    logging.info("🌙 야간 예측 스캔 시작")
    COINS = get_all_krw_coins()
    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in COINS])
    response = requests.get(url).json()

    message_lines = ["🌙 [야간 후보 리스트]"]

    for data in response:
        coin = data['market'].split('-')[1]
        price = data['trade_price']
        volume = data['acc_trade_volume_24h']
        prev_volume = previous_data.get(coin, {}).get('volume')
        if not prev_volume:
            continue

        volume_change = volume / prev_volume
        prices = get_candle_prices(coin)
        rsi = calculate_rsi(prices)

        if rsi and 35 < rsi < 55 and volume_change > 1.5:
            night_candidates[coin] = {
                'price': price,
                'volume': volume,
                'rsi': rsi
            }
            line = f"- {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}"
            message_lines.append(line)
            logging.info(f"🕵️‍♂️ 후보 등록: {coin} | RSI: {rsi} | 거래량 x{volume_change:.2f}")

    if len(message_lines) > 1:
        message_lines.append("\n🕐 내일 아침 급등 가능성 있는 후보입니다.")
        bot.send_message(chat_id=CHAT_ID, text="\n".join(message_lines))
    else:
        bot.send_message(chat_id=CHAT_ID, text="🌙 오늘은 야간 예측 후보가 없습니다.")

def morning_check():
    logging.info("🌅 아침 후보 검증 시작")
    if not night_candidates:
        return
    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in night_candidates])
    response = requests.get(url).json()
    for data in response:
        coin = data['market'].split('-')[1]
        morning_price = data['trade_price']
        prev_info = night_candidates.get(coin)
        if not prev_info:
            continue
        rise = ((morning_price - prev_info['price']) / prev_info['price']) * 100
        if rise >= 5:
            name = COIN_NAMES.get(coin, coin)
            chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
            message = (
                f"☀️ [{name}] {coin} 새벽 급등!\n"
                f"밤 가격: {int(prev_info['price'])}원 → 아침 가격: {int(morning_price)}원\n"
                f"수익률: +{rise:.2f}%\n"
                f"[👉 차트 보기]({chart_url})"
            )
            bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
            logging.info(f"☀️ 아침 알림 전송됨: {coin} +{rise:.2f}%")

# 스케줄 등록
schedule.every(CHECK_INTERVAL).seconds.do(check_market)
schedule.every().day.at("23:00").do(nightly_scan)
schedule.every().day.at("07:30").do(morning_check)

print(f"🔔 실시간 감시 대상: {', '.join(COINS_FIXED)}")

while True:
    schedule.run_pending()
    time.sleep(1)
