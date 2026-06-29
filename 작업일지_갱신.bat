@echo off
chcp 65001 >nul
rem ===== 작업일지 데이터를 GitHub Pages(폰 화면)에 반영 =====
rem 더블클릭하면: 최신 데이터로 HTML 재생성 -> git add/commit/push
rem 1~2분 뒤 폰 아이콘으로 열면 최신 내용이 보입니다.

cd /d "%~dp0"
echo ============================================
echo   하이디라오 작업일지 - 폰 화면 갱신
echo ============================================
echo.

echo [1/3] HTML 재생성 중...
python build_worklogs_html.py
if errorlevel 1 (
  echo.
  echo [!] HTML 생성 실패. python 설치 여부를 확인하세요.
  goto end
)
echo.

echo [2/3] 변경사항 커밋 중...
git add -A
git diff --cached --quiet
if not errorlevel 1 (
  echo     변경된 내용이 없습니다. 푸시를 건너뜁니다.
  goto end
)
git commit -m "작업일지 갱신"
echo.

echo [3/3] GitHub 업로드(push) 중...
git push origin main
if errorlevel 1 (
  echo.
  echo [!] push 실패. 인터넷 연결 또는 GitHub 로그인을 확인하세요.
  goto end
)
echo.
echo ============================================
echo   완료! 1~2분 뒤 폰에서 최신 내용이 보입니다.
echo ============================================

:end
echo.
pause
