# Upbit 급등 감지 및 뉴스 분석 봇

업비트(Upbit) KRW 마켓의 코인을 대상으로 실시간 급등을 감지하고, 야간 예측 분석을 수행하며, CryptoPanic 뉴스를 기반으로 시장 동향을 분석하여 텔레그램으로 알림을 전송하는 Python 자동화 봇입니다.

## 주요 기능

### 1. 실시간 급등 감지
- **운영 시간**: 매일 07:00 ~ 22:50 (2분 간격)
- **감지 대상**: 관심 코인 리스트
- **감지 조건**:
  - 이전 1시간 대비 가격 변동률 3% 이상 상승
  - 거래량 2배 이상 증가
- **알림**: 조건 충족 시 즉시 텔레그램 알림 전송

### 2. 야간 예측 분석
- **실행 시간**: 매일 23:00
- **분석 대상**: 업비트 KRW 마켓 전체 코인
- **선정 기준**:
  - RSI 지표 35 ~ 55 구간
  - 최근 거래량이 이전 1시간 대비 1.5배 이상 증가
- **결과**: 유망 코인 후보 리스트를 텔레그램으로 전송 및 CSV 파일로 저장

### 3. 아침 결과 검증
- **실행 시간**: 매일 07:30
- **검증 내용**: 전날 밤 선정된 후보 코인의 수익률 분석
- **알림**: 5% 이상 상승한 코인이 있을 경우 성공 알림 발송

### 4. 뉴스 기반 분석
- **실행 주기**: 30분 간격
- **출처**: CryptoPanic (중요 뉴스 필터링)
- **기능**:
  - DeepL API를 활용한 뉴스 제목 한글 번역
  - 뉴스 관련 코인 자동 추출 및 가격 급등 여부 분석 (10분 내 변동률 2배 이상)
  - 뉴스 요약 및 분석 결과를 텔레그램으로 전송

## 시작하기

이 프로젝트를 로컬 환경에서 실행하기 위한 방법입니다.

### 사전 요구 사항
- Python 3.10 이상
- Telegram Bot Token 및 Chat ID
- Upbit API Key (Access/Secret Key)
- CryptoPanic API Key
- DeepL API Key

### 설치

1. 저장소를 클론합니다.
   ```bash
   git clone https://github.com/yourusername/upbit_bot.git
   cd upbit_bot
   ```

2. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

### 환경 설정

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 정보를 입력하세요.

```env
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
CRYPTOPANIC_API_KEY=your_cryptopanic_api_key
DEEPL_AUTH_KEY=your_deepl_auth_key
```

## 사용 방법

각 기능별로 별도의 스크립트를 실행하거나, 배치 파일을 통해 실행할 수 있습니다.

- **전체 기능 실행**: `run_all.bat`
- **뉴스 분석 실행**: `python main_news.py`
- **급등 감지 실행**: `python main_alert.py`
- **스윙/예측 분석 실행**: `python main_swing.py`

## 기술 스택

- **Language**: Python 3.10+
- **API Integration**: `requests` (Upbit, CryptoPanic, DeepL)
- **Scheduling**: `schedule`
- **Notification**: `python-telegram-bot`
- **Environment Management**: `python-dotenv`
- **Data Processing**: `hashlib`, `json`

## 알림 예시

### 실시간 급등 감지
```
[리플] XRP 급등 감지!
가격: 735원 (+6.02%)
거래량: x2.4 증가
차트 보기: https://upbit.com/exchange?code=CRIX.UPBIT.KRW-XRP
```

### 야간 예측 후보
```
[야간 후보 리스트]
- BTC | RSI: 52.34 | 거래량 x3.12
- ARB | RSI: 47.89 | 거래량 x2.05
내일 아침 급등 가능성 있는 후보입니다.
```

### 뉴스 요약 알림
```
중요 뉴스 요약 (30분 주기)

1. BlackRock resubmits ETF application
블랙록, ETF 신청서 재제출
BTC +2.8%
https://cryptopanic.com/news/abc123
```

## 참고 자료
- [Upbit Open API](https://docs.upbit.com)
- [CryptoPanic API](https://cryptopanic.com/developers/api/)
- [DeepL API](https://www.deepl.com/docs-api)
