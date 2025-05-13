import requests
from telegram import Bot
import os
from dotenv import load_dotenv
import hashlib
import json
import schedule
import time
from telegram.utils.helpers import escape_markdown

# 환경 변수 로드 및 봇 초기화
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CRYPTO_PANIC_KEY = os.getenv("CRYPTO_PANIC_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
CACHE_FILE = "crypto_news_sent.json"

# 전체 KRW 마켓 코인 심볼 로드 (최초 1회)
def get_all_krw_symbols():
    url = "https://api.upbit.com/v1/market/all"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return [item['market'].split('-')[1] for item in res.json() if item['market'].startswith("KRW-")]
    except Exception as e:
        print(f"❌ 심볼 목록 로딩 실패: {e}")
        return []

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

# DeepL API를 사용하여 영어 → 한글 번역
def translate_to_korean(text):
    url = "https://api-free.deepl.com/v2/translate"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": text,
        "source_lang": "EN",
        "target_lang": "KO"
    }
    try:
        res = requests.post(url, headers=headers, data=data)
        res.raise_for_status()
        return res.json()['translations'][0]['text']
    except Exception as e:
        print(f"❌ 번역 실패: {e}")
        return "(번역 실패)"

# 새 뉴스 감지 → 번역/분석 → 텔레그램으로 하나로 전송
def send_batched_news_alert():
    sent_cache = load_sent_cache()
    new_sent = False
    message_lines = ["\ud83d\udcf1 중요 뉴스 요약 (3분 주기)\n"]

    for idx, news in enumerate(fetch_crypto_panic_news()[:10], start=1):
        title = news['title']
        news_id = hashlib.md5(title.encode("utf-8")).hexdigest()
        if news_id in sent_cache:
            continue

        url = news['url']
        translated = translate_to_korean(title)
        safe_title = escape_markdown(title, version=2)
        safe_ko = escape_markdown(translated, version=2)
        safe_url = escape_markdown(url, version=2)

        entry = f"{idx}. *{safe_title}*\n\U0001F238 {safe_ko}"

        related_coins = extract_symbols_from_title(title, ALL_SYMBOLS)
        for coin in related_coins:
            change = get_price_change_percent(coin)
            if change is not None and change >= 2:
                change_msg = escape_markdown(f"{coin} +{change}%", version=2)
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
schedule.every(5).minutes.do(send_batched_news_alert)

print("CryptoPanic 뉴스 감시 시작됨 (3분마다 실행)")

# 메인 루프
while True:
    schedule.run_pending()
    time.sleep(1)