@echo off
CALL conda activate C:\conda-envs\upbit-bot

start "" C:\conda-envs\upbit-bot\python.exe main_news.py
start "" C:\conda-envs\upbit-bot\python.exe main_swing.py
start "" C:\conda-envs\upbit-bot\python.exe main_alert.py

exit
