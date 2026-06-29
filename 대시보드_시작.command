#!/bin/bash
# 더블클릭하면 대시보드 로컬 서버가 켜지고 브라우저가 자동으로 열립니다.
# [🔄 지금 업데이트] 버튼은 이 서버가 켜져 있어야 동작합니다.
cd "$(dirname "$0")" || exit 1
echo "하이디라오 대시보드 서버를 시작합니다…"
exec python3 update_server.py
