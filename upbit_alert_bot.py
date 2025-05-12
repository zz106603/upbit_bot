import requests
import time
import schedule
from telegram import Bot
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

# 로그 설정
# logs 디렉토리 없으면 생성
if not os.path.exists("upbit_logs"):
    os.makedirs("upbit_logs")

# 오늘 날짜 기반 파일 이름
today = datetime.now().strftime('%Y-%m-%d')
log_file_path = f"upbit_logs/log_{today}.txt"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# .env 파일 로드
load_dotenv()

# 설정 값 가져오기
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

COIN_NAMES = {
    "MEW": "캣인어독스월드",
    "XRP": "리플",
    "DOGE": "도지",
    "MOVE": "무브먼트",
    "PUNDIX": "펀디엑스",
    "LAYER": "솔레이어",
    "VIRTUAL": "버추얼프로토콜",
    "KAITO": "카이토",
    "BTC": "비트코인",
    "ETH": "이더리움",
    "ONDO": "온도파이낸스"
}
COINS=["MEW","XRP","DOGE","MOVE","PUNDIX","LAYER","VIRTUAL","KAITO","BTC","ETH","ONDO"]
PRICE_THRESHOLD_PERCENT=4
VOLUME_THRESHOLD_MULTIPLIER=2
CHECK_INTERVAL=60

bot = Bot(token=TELEGRAM_TOKEN)
previous_data = {coin: {'price': None, 'volume': None} for coin in COINS}

def check_market():
    url = f"https://api.upbit.com/v1/ticker?markets=" + ','.join([f'KRW-{coin}' for coin in COINS])
    response = requests.get(url).json()

    for data in response:
        market = data['market']
        coin = market.split('-')[1]
        current_price = data['trade_price']
        current_volume = data['acc_trade_volume_24h']

        prev_price = previous_data[coin]['price']
        prev_volume = previous_data[coin]['volume']

        if prev_price and prev_volume:

            # # 테스트 모드 시작 (강제 조건 충족)
            # # ↓ 실제 조건은 아래 두 줄로 대체됨
            # fake_prev_price = current_price * 0.85  # 15% 급등한 것처럼
            # fake_prev_volume = current_volume / 10  # 거래량 10배 증가한 것처럼

            # price_change = ((current_price - fake_prev_price) / fake_prev_price) * 100
            # volume_change = current_volume / fake_prev_volume

            # # 테스트용 메시지 전송
            # if price_change >= PRICE_THRESHOLD_PERCENT and volume_change >= VOLUME_THRESHOLD_MULTIPLIER:
            #     chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
            #     message = (
            #         f"🚨 [테스트] {coin} 급등 감지!\n"
            #         f"가격: {current_price}원 ({price_change:.2f}%↑)\n"
            #         f"거래량: {volume_change:.1f}배 증가\n"
            #         f"[👉 차트 보기]({chart_url})"
            #     )
            #     bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
            #     logging.info(f"🚨 알림 전송됨: {coin} ({price_change:.2f}% 상승, x{volume_change:.1f} 거래량)")

            price_change = ((current_price - prev_price) / prev_price) * 100
            volume_change = current_volume / prev_volume if prev_volume > 0 else 0

            logging.info(f"[{coin}] 가격: {current_price}원 / 변화율: {price_change:.2f}% / 거래량 x{volume_change:.1f}")

            if price_change >= PRICE_THRESHOLD_PERCENT and volume_change >= VOLUME_THRESHOLD_MULTIPLIER:
                chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"

                korean_name = COIN_NAMES.get(coin, coin)  # 매핑 없으면 영어 그대로
                message = (
                    f"🚨 [{korean_name}] {coin} 급등 감지!\n"
                    f"가격: {current_price}원 ({price_change:.2f}%↑)\n"
                    f"거래량: {volume_change:.1f}배 증가\n"
                    f"[👉 차트 보기]({chart_url})"
                )
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
                logging.info(f"🚨 알림 전송됨: {coin} ({price_change:.2f}% 상승, x{volume_change:.1f} 거래량)")


        previous_data[coin]['price'] = current_price
        previous_data[coin]['volume'] = current_volume

schedule.every(CHECK_INTERVAL).seconds.do(check_market)

print(f"🔔 알림봇 시작됨: 감시 대상 = {', '.join(COINS)}")

while True:
    schedule.run_pending()
    time.sleep(1)
