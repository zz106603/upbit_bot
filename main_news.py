import requests
from telegram import Bot
import os
from dotenv import load_dotenv
import hashlib
import json
import schedule
import time
from utils.telegram_helper import escape
from utils.upbit import get_all_krw_symbols, get_price_change_percent
from utils.translate import translate_to_korean

# 환경 변수 로드 및 봇 초기화
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRYPTO_PANIC_KEY = os.getenv("CRYPTO_PANIC_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
CACHE_FILE = "crypto_news_sent.json"

# 스케쥴링 시간(분)
NEWS_TIME = 30

# 최초 1회
ALL_SYMBOLS = get_all_krw_symbols()

# 전송된 뉴스 캐시 불러오기
def load_sent_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

# 전송된 뉴스 캐시 저장
def save_sent_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False, indent=2)

# 중요 뉴스 가져오기 (CryptoPanic 필터 적용)
def fetch_crypto_panic_news():
    url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTO_PANIC_KEY}&filter=important"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json().get("results", [])
    except Exception as e:
        print(f"❌ 뉴스 가져오기 실패: {e}")
        return []

# 뉴스 제목에서 관련 코인 심볼 자동 추출
def extract_symbols_from_title(title: str, all_symbols):
    return [symbol for symbol in all_symbols if symbol.lower() in title.lower()]

# 새 뉴스 감지 → 번역/분석 → 텔레그램으로 하나로 전송
def send_batched_news_alert():
    sent_cache = load_sent_cache()
    new_sent = False
    message_lines = ["\ud83d\udcf1 중요 뉴스 요약 (30분 주기)\n"]

    for idx, news in enumerate(fetch_crypto_panic_news()[:10], start=1):
        title = news['title']
        news_id = hashlib.md5(title.encode("utf-8")).hexdigest()
        if news_id in sent_cache:
            continue

        url = news['url']
        translated = translate_to_korean(title)
        safe_title = escape(title)
        safe_ko = escape(translated)
        safe_url = escape(url)

        entry = f"{idx}. *{safe_title}*\n\U0001F238 {safe_ko}"

        related_coins = extract_symbols_from_title(title, ALL_SYMBOLS)
        for coin in related_coins:
            change = get_price_change_percent(coin)
            if change is not None and change >= 2:
                change_msg = escape(f"{coin} +{change}%")
                entry += f"\n\U0001F4C8 {change_msg}"

        entry += f"\n\U0001F517 {safe_url}\n"
        message_lines.append(entry)
        sent_cache.add(news_id)
        new_sent = True
        time.sleep(0.2)

    if new_sent:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(message_lines), parse_mode="MarkdownV2")
        save_sent_cache(sent_cache)
        print("✅ 뉴스 요약 알림 전송됨")
    else:
        print("🔸 새 뉴스 없음")

# 실행 스케줄 등록
schedule.every(NEWS_TIME).minutes.do(send_batched_news_alert)

print(f"CryptoPanic 뉴스 감시 시작됨 ({NEWS_TIME}분)")

# 메인 루프
while True:
    schedule.run_pending()
    time.sleep(1)
