# 📈 Upbit 급등 감지 & 예측 + 뉴스 기반 분석 봇

업비트의 KRW 마켓 전체 코인을 대상으로 **실시간 급등 감지**, **야간 예측 분석**, **CryptoPanic 뉴스 기반 감시 및 번역 알림**을 수행하며, 그 결과를 **텔레그램으로 전송**하는 Python 기반 자동화 봇입니다.

---

## 주요 기능

### 실시간 급등 감지 (매일 07:00 ~ 22:50, 2분 간격)
- 고정된 관심 코인 리스트 대상으로 가격/거래량 급등 여부 모니터링
- 조건: **이전 1시간 기준 가격 변동률 ≥ 3%**, **거래량 증가 ≥ x2**
- 급등 감지 시 텔레그램으로 개별 알림 발송
- **민감 조건으로 테스트 진행중
  - **이전 3분 기준 가격 변동률 ≥ 3%, 거래량 증가 ≥ x1.5**

### 야간 예측 분석 (매일 23:00)
- 업비트 **KRW 마켓 전체 코인** 스캔
- **RSI (35~55)** 범위 & 최근 거래량이 이전 1시간 대비 **1.5배 이상 증가**한 코인 후보 저장
- 텔레그램으로 **후보 리스트 전송** + CSV 기록

### 아침 결과 검증 (매일 07:30)
- 전날 밤 저장된 후보 코인의 **수익률 분석**
- **+5% 이상 상승한 코인**이 있을 경우 **급등 성공 알림 발송**

### 뉴스 기반 분석 (30분 간격)
- [CryptoPanic](https://cryptopanic.com)에서 중요 뉴스(important)만 수집
- **DeepL API**를 통해 뉴스 제목 자동 번역 (영어 → 한글)
- 뉴스마다 연관된 코인 자동 추출 → **10분간 가격 급등 여부 분석 (가격 변동률 ≥ x2)**
- 모든 뉴스는 하나의 텔레그램 메시지로 묶어서 요약 전송

---

## 기술 스택

- Python 3.10+
- `requests` - Upbit/CryptoPanic API 호출
- `schedule` - 정기 스케줄러
- `python-telegram-bot` - 텔레그램 알림 발송
- `python-dotenv` - `.env` 환경 변수 관리
- `hashlib/json` - 뉴스 중복 방지 (캐싱)
- `deepl API` - 뉴스 자동 번역 (한글)
- `logging` - 콘솔 및 파일 로그 기록

---

## 텔레그램 알림 예시

### 🔔 실시간 급등 감지
```
🚨 [리플] XRP 급등 감지!
가격: 735원 (+6.02%)
거래량: x2.4 증가
👉 차트 보기: https://upbit.com/exchange?code=CRIX.UPBIT.KRW-XRP
```

### 🌙 야간 예측 후보
```
🌙 [야간 후보 리스트]
- BTC | RSI: 52.34 | 거래량 x3.12
- ARB | RSI: 47.89 | 거래량 x2.05
🕐 내일 아침 급등 가능성 있는 후보입니다.
```

### 📰 뉴스 요약 알림
```
📡 중요 뉴스 요약 (30분 주기)

1. *BlackRock resubmits ETF application*
🈯️ 블랙록, ETF 신청서 재제출
📈 BTC +2.8%
🔗 https://cryptopanic.com/news/abc123

2. *Ripple wins partial SEC ruling*
🈯️ 리플, SEC와의 소송 일부 승소
📈 XRP +3.1%
🔗 https://cryptopanic.com/news/xyz456
```

---

## 참고 자료
- [Upbit Open API](https://docs.upbit.com)
- [CryptoPanic API](https://cryptopanic.com/developers/api/)
- [DeepL API](https://www.deepl.com/docs-api)
- [Investopedia - RSI](https://www.investopedia.com/terms/r/rsi.asp)
