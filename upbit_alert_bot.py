import requests
import time
import schedule
from telegram import Bot
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 설정 값 가져오기
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
COINS = os.getenv("COINS").split(",")
PRICE_THRESHOLD_PERCENT = float(os.getenv("PRICE_THRESHOLD_PERCENT"))
VOLUME_THRESHOLD_MULTIPLIER = float(os.getenv("VOLUME_THRESHOLD_MULTIPLIER"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"))

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
            price_change = ((current_price - prev_price) / prev_price) * 100
            volume_change = current_volume / prev_volume if prev_volume > 0 else 0

            if price_change >= PRICE_THRESHOLD_PERCENT and volume_change >= VOLUME_THRESHOLD_MULTIPLIER:
                chart_url = f"https://upbit.com/exchange?code=CRIX.UPBIT.KRW-{coin}"
                message = (
                    f"🚨 {coin} 급등 감지!\n"
                    f"가격: {current_price}원 ({price_change:.2f}%↑)\n"
                    f"거래량: {volume_change:.1f}배 증가\n"
                    f"[👉 차트 보기]({chart_url})"
                )
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

        previous_data[coin]['price'] = current_price
        previous_data[coin]['volume'] = current_volume

schedule.every(CHECK_INTERVAL).seconds.do(check_market)

print(f"🔔 알림봇 시작됨: 감시 대상 = {', '.join(COINS)}")

while True:
    schedule.run_pending()
    time.sleep(1)
