import requests
from telegram import Bot
import os
from dotenv import load_dotenv
import hashlib
import json
import schedule
import time

# .env 로드
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRYPTO_PANIC_KEY = os.getenv("CRYPTO_PANIC_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
CACHE_FILE = "crypto_news_sent.json"

def load_sent_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False, indent=2)

def fetch_crypto_panic_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_KEY}&filter=important"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json().get("results", [])
    except Exception as e:
        print(f"❌ 뉴스 가져오기 실패: {e}")
        return []

def send_news_alert():
    sent_cache = load_sent_cache()
    new_sent = False

    for news in fetch_crypto_panic_news()[:10]:
        title = news["title"]
        url = news["url"]
        news_id = hashlib.md5(title.encode("utf-8")).hexdigest()

        if news_id in sent_cache:
            continue  # 이미 전송한 뉴스는 스킵

        message = f"📰 *{title}*\n🔗 {url}"
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        print(f"✅ 전송됨: {title}")

        sent_cache.add(news_id)
        new_sent = True

    if new_sent:
        save_sent_cache(sent_cache)
    else:
        print("🔸 새 뉴스 없음")

# 🔁 10분마다 실행 예약
schedule.every(30).minutes.do(send_news_alert)

print("📡 CryptoPanic 뉴스 감시 시작됨 (10분마다 실행)")

# 메인 루프
while True:
    schedule.run_pending()
    time.sleep(1)
