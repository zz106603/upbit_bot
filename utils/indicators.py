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
    macd_line = [a - b for a, b in zip(ema12[-len(ema26):], ema26)]
    signal_line = ema(macd_line, 9)
    return macd_line[-1], signal_line[-1]
