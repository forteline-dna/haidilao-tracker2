@echo off
chcp 65001 >nul
rem ===== 매일 오전 9시 작업 스케줄러가 실행하는 자동 갱신 (윈도우용) =====
rem Lark 메시지 수집 -> 작업일지/이벤트트래커 갱신 -> GitHub push
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
"C:\Users\j1375\AppData\Local\Programs\Python\Python312\python.exe" morning_update.py >> morning_task.log 2>&1
