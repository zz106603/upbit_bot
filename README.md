# 📈 Upbit 급등 감지 & 예측 봇

업비트의 KRW 마켓 전체 코인을 대상으로 **실시간 급등 감지**와 **야간 예측 분석**을 수행하고, 그 결과를 **텔레그램으로 알림**해주는 Python 기반 봇

## 주요 기능

- **실시간 감지 (60초 주기 매일 07:00 ~ 22:50)**
  - 고정 코인 리스트 대상으로 가격/거래량 급등 감지
  - 조건: 가격 변동률 ≥ 4%, 거래량 증가 ≥ x2
- **야간 예측 분석 (매일 23:00)**
  - 업비트 KRW 마켓 전체 코인 스캔
  - RSI(35~55) + 최근 1시간 거래량이 이전 1시간 대비 1.5배 이상인 코인 후보 선정
- **아침 결과 검증 (매일 07:30)**
  - 전날 후보 코인이 5% 이상 상승한 경우 알림 발송

## 기술 스택

- Python 3.10+
- `requests` - Upbit API 요청
- `schedule` - 정기 스케줄 실행
- `python-telegram-bot` - 텔레그램 메시지 전송
- `python-dotenv` - 환경 변수 관리
- `logging` - 파일/콘솔 로그 기록

## 텔레그램 알림 예시
- 🚨 [리플] XRP 급등 감지!
- 가격: 735원 (+6.02%)0
- 거래량: x2.4 증가
- 👉 차트 보기: https://upbit.com/exchange?code=CRIX.UPBIT.KRW-XRP
---
- 🌙 [야간 후보 리스트]
- BTC | RSI: 52.34 | 거래량 x3.12
- ARB | RSI: 47.89 | 거래량 x2.05
- 🕐 내일 아침 급등 가능성 있는 후보입니다.

## 참고
- Upbit Open API: https://docs.upbit.com
- RSI 계산 참고: [Investopedia - RSI](https://www.investopedia.com/terms/r/rsi.asp)