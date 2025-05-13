@echo off
CALL conda activate C:\conda-envs\upbit-bot

start "news" C:\conda-envs\upbit-bot\python.exe main_news.py
start "swing" C:\conda-envs\upbit-bot\python.exe main_swing.py
start "alert" C:\conda-envs\upbit-bot\python.exe main_alert.py

exit
