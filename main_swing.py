import requests
import time
import csv
import os
import schedule
from datetime import datetime, timedelta
from telegram import Bot
from dotenv import load_dotenv
from utils.upbit import get_all_krw_symbols, get_daily_candles
from utils.indicators import calculate_rsi, calculate_macd

# 환경변수 로드
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)
SWING_LOG = "upbit_logs/swing_candidates.csv"
POSITION_LOG = "upbit_logs/swing_positions.csv"

# 스윙 시간
SWING_SCAN_TIME = "22:30"
SWING_POSITION_TIME = "09:00"
ANALYZE_POSITION_TIME = "09:10"

# 스윙 후보 저장
def save_swing_candidate(coin, rsi, macd, signal, vol_ratio, price):
    if not os.path.exists("upbit_logs"):
        os.makedirs("upbit_logs")
    file_exists = os.path.isfile(SWING_LOG)
    with open(SWING_LOG, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "coin", "rsi", "macd", "signal", "vol_ratio", "price"])
        writer.writerow([datetime.now().strftime('%Y-%m-%d'), coin, rsi, macd, signal, vol_ratio, price])

# 스윙 포지션 저장
def save_swing_position(coin, entry_price):
    file_exists = os.path.isfile(POSITION_LOG)
    with open(POSITION_LOG, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "coin", "entry_price"] + [f"D+{i}" for i in range(1, 8)])
        writer.writerow([datetime.now().strftime('%Y-%m-%d'), coin, entry_price] + ["" for _ in range(7)])

# 이전 후보 불러오기
def load_previous_candidates():
    if not os.path.exists(SWING_LOG):
        return set()
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    candidates = set()
    with open(SWING_LOG, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['date'] == yesterday:
                candidates.add(row['coin'])
    return candidates

# 스윙 포지션 업데이트
def update_swing_positions():
    if not os.path.exists(POSITION_LOG):
        return
    updated_rows = []
    with open(POSITION_LOG, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    for row in rows:
        entry_date = datetime.strptime(row[0], "%Y-%m-%d")
        coin = row[1]
        entry_price = float(row[2])
        days_elapsed = (datetime.now() - entry_date).days
        if 1 <= days_elapsed <= 7 and row[2 + days_elapsed] == "":
            try:
                url = f"https://api.upbit.com/v1/ticker?markets=KRW-{coin}"
                res = requests.get(url)
                res.raise_for_status()
                current_price = res.json()[0]['trade_price']
                row[2 + days_elapsed] = str(current_price)
            except:
                continue
        updated_rows.append(row)
    with open(POSITION_LOG, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(updated_rows)

# 완료된 포지션 분석
def analyze_completed_positions():
    if not os.path.exists(POSITION_LOG):
        return
    rows_to_keep = []
    with open(POSITION_LOG, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row in reader:
            if all(row[3:10]):  # D+1 to D+7 모두 채워졌는지 확인
                coin = row[1]
                entry_price = float(row[2])
                prices = list(map(float, row[3:10]))
                max_price = max(prices)
                min_price = min(prices)
                end_price = prices[-1]
                max_rise = (max_price - entry_price) / entry_price * 100
                max_fall = (min_price - entry_price) / entry_price * 100
                final_rise = (end_price - entry_price) / entry_price * 100
                message = (
                    f"📊 [{coin} 스윙 결과 요약]\n"
                    f"진입가: {entry_price:.2f}원\n"
                    f"7일간 고점: {max_price:.2f}원 ({max_rise:.2f}%)\n"
                    f"7일간 저점: {min_price:.2f}원 ({max_fall:.2f}%)\n"
                    f"종료가: {end_price:.2f}원 ({final_rise:.2f}%)"
                )
                bot.send_message(chat_id=CHAT_ID, text=message)
            else:
                rows_to_keep.append(row)
    with open(POSITION_LOG, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows_to_keep)

# 스윙 스캔 실행
def swing_scan():
    print("\n📈 스윙 스캔 시작")
    symbols = get_all_krw_symbols()
    message_lines = ["📈 [스윙 후보 리스트]"]
    strong_lines = ["🔥 [이틀 연속 스윙 조건 만족]"]
    found = False
    strong_found = False

    prev_day_set = load_previous_candidates()

    for coin in symbols:
        candles = get_daily_candles(coin)
        if len(candles) < 30:
            continue

        closes = [c['trade_price'] for c in reversed(candles)]
        volumes = [c['candle_acc_trade_volume'] for c in reversed(candles)]
        current_price = closes[-1]

        rsi = calculate_rsi(closes)
        macd, signal = calculate_macd(closes)
        vol_ratio = volumes[-1] / (sum(volumes[:-1]) / len(volumes[:-1])) if len(volumes) > 1 else 1

        if rsi and macd and signal and rsi < 45 and macd > signal and vol_ratio > 1.5:
            found = True
            save_swing_candidate(coin, rsi, macd, signal, vol_ratio, current_price)
            save_swing_position(coin, current_price)
            line = f"- {coin} | RSI: {rsi} | MACD: {macd:.4f} > SIG: {signal:.4f} | 거래량 x{vol_ratio:.2f}"
            message_lines.append(line)
            print(f"✅ 후보: {line}")

            if coin in prev_day_set:
                strong_found = True
                strong_lines.append(f"✅ {coin} → 이틀 연속 조건 만족")

        time.sleep(0.2)

    if found:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(message_lines))
    else:
        bot.send_message(chat_id=CHAT_ID, text="📉 오늘 스윙 조건을 만족하는 종목이 없습니다.")

    if strong_found:
        bot.send_message(chat_id=CHAT_ID, text="\n".join(strong_lines))

# 매일 밤 22:30 스윙 스캔, 매일 오전 09:00 수익률 추적 및 분석
schedule.every().day.at(SWING_SCAN_TIME).do(swing_scan)
schedule.every().day.at(SWING_POSITION_TIME).do(update_swing_positions)
schedule.every().day.at(ANALYZE_POSITION_TIME).do(analyze_completed_positions)

print("🟢 스윙 봇 실행됨 (스캔: 22:30 / 추적: 09:00 / 분석: 09:10)")
while True:
    schedule.run_pending()
    time.sleep(1)

