@echo off
chcp 65001 >nul
rem 더블클릭하면 대시보드 로컬 서버가 켜지고 브라우저가 자동으로 열립니다.
rem [🔄 지금 업데이트] 버튼은 이 서버가 켜져 있어야 동작합니다.
rem 서버 종료: 이 창을 닫거나 Ctrl+C

cd /d "%~dp0"
set PYTHONUTF8=1
echo 하이디라오 대시보드 서버를 시작합니다…
python update_server.py
if errorlevel 1 (
  echo.
  echo [!] 서버 실행 실패. python 설치 여부를 확인하세요.
  pause
)
