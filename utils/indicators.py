import numpy as np

# 주어진 가격 데이터로 RSI 계산
def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = [prices[i+1] - prices[i] for i in range(len(prices)-1)]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# 주어진 가격 데이터로 MACD 계산
def calculate_macd(prices):
    def ema(prices, period):
        ema_vals = [sum(prices[:period]) / period]
        k = 2 / (period + 1)
        for price in prices[period:]:
            ema_vals.append(price * k + ema_vals[-1] * (1 - k))
        return ema_vals

    if len(prices) < 35:
        return None, None
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    min_len = min(len(ema12), len(ema26))
    macd_line = [a - b for a, b in zip(ema12[-min_len:], ema26[-min_len:])]
    signal_line = ema(macd_line, 9)
    return macd_line[-1], signal_line[-1]

# 이동 평균 (MA) 계산 함수
def calculate_ma(closes, period=20):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period

# 이상 거래량 비율 계산 함수
def calculate_volatility_ratio(volumes):
    if len(volumes) < 2:
        return 1.0
    avg = np.mean(volumes[:-1])
    std = np.std(volumes[:-1])
    current = volumes[-1]
    return current / (avg + std) if (avg + std) > 0 else 1.0

# 최근 N일 고점 대비 낙폭 계산 함수
def calculate_drawdown(closes, window=7):
    if len(closes) < window:
        return 0.0
    max_price = max(closes[-window:])
    current_price = closes[-1]
    return round((current_price - max_price) / max_price * 100, 2)
