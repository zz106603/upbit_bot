@echo off

REM Conda activate + 환경명으로 실행
CALL conda activate C:\conda-envs\upbit-bot

REM 현재 디렉토리 기준으로 실행 (상대 경로)
python upbit_alert_bot.py

pause
