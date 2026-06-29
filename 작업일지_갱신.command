#!/bin/bash
# ===== 작업일지 데이터를 GitHub Pages(폰 화면)에 반영 =====
# 더블클릭하면: 최신 데이터로 HTML 재생성 -> git add/commit/push
# 1~2분 뒤 폰 아이콘으로 열면 최신 내용이 보입니다.
cd "$(dirname "$0")" || exit 1

echo "============================================"
echo "  하이디라오 작업일지 - 폰 화면 갱신"
echo "============================================"
echo

echo "[1/3] HTML 재생성 중..."
if ! python3 build_worklogs_html.py; then
  echo
  echo "[!] HTML 생성 실패. python3 설치 여부를 확인하세요."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."; exit 1
fi
echo

echo "[2/3] 변경사항 커밋 중..."
git add -A
if git diff --cached --quiet; then
  echo "    변경된 내용이 없습니다. 푸시를 건너뜁니다."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."; exit 0
fi
git commit -m "작업일지 갱신"
echo

echo "[3/3] GitHub 업로드(push) 중..."
if ! git push origin main; then
  echo
  echo "[!] push 실패. 인터넷 연결 또는 GitHub 로그인을 확인하세요."
  read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."; exit 1
fi
echo
echo "============================================"
echo "  완료! 1~2분 뒤 폰에서 최신 내용이 보입니다."
echo "============================================"
echo
read -n 1 -s -r -p "아무 키나 누르면 닫힙니다..."
