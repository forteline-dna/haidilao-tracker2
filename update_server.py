#!/usr/bin/env python3
"""
대시보드 로컬 서버

- 작업일지/이벤트 트래커 HTML을 http://localhost:8765 로 서빙
- 작업일지 화면의 [🔄 지금 업데이트] 버튼 → POST /api/update → daily_update.py 실행
  (라크 채팅 수집 → 시공일지·이벤트 트래커·회의록 갱신)

실행: 프로젝트 폴더의 "대시보드_시작.command" 더블클릭
     (또는 터미널에서  python3 update_server.py )
종료: 터미널 창에서 Control+C  또는 창 닫기
"""
import os
import re
import sys
import json
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8765
HOME_PAGE = '/하이디라오_작업일지.html'


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, *args):
        pass  # 접속 로그 숨김 (조용히)

    def end_headers(self):
        # 항상 최신 화면이 뜨도록 캐시 방지 헤더 주입
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        if self.path.rstrip('/') == '/api/update':
            self._run_update()
        else:
            self.send_error(404, 'Not Found')

    def _send_json(self, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _run_update(self):
        print('  ▶ 업데이트 실행: daily_update.py …')
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(BASE_DIR, 'daily_update.py')],
                cwd=BASE_DIR, capture_output=True, text=True, timeout=300,
            )
            out = (proc.stdout or '') + '\n' + (proc.stderr or '')

            def grab(pattern):
                found = re.findall(pattern, out)
                return int(found[-1]) if found else 0

            result = {
                'ok': proc.returncode == 0,
                'work_logs': grab(r'작업일지:\s*\+(\d+)개'),
                'events': grab(r'이벤트 트래커:\s*\+(\d+)개'),
                'meetings': grab(r'회의록:\s*\+(\d+)개'),
                'tail': '\n'.join(out.strip().splitlines()[-15:]),
            }
            if proc.returncode != 0 and 'error' not in result:
                result['error'] = '업데이트 스크립트 오류 (토큰 만료 가능 — 터미널에서 python3 daily_update.py --token)'
            print(f'  ✔ 완료: 시공일지 +{result["work_logs"]}, 이벤트 +{result["events"]}, 회의록 +{result["meetings"]}')
        except subprocess.TimeoutExpired:
            result = {'ok': False, 'error': '시간 초과 (5분)'}
            print('  ✖ 시간 초과')
        except Exception as e:  # noqa: BLE001
            result = {'ok': False, 'error': str(e)}
            print(f'  ✖ 오류: {e}')
        self._send_json(result)


def main():
    os.chdir(BASE_DIR)
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    url = f'http://localhost:{PORT}{HOME_PAGE}'
    print('═' * 55)
    print('  📊 하이디라오 대시보드 서버 시작')
    print(f'  주소: {url}')
    print('  [🔄 지금 업데이트] 버튼이 이 서버를 통해 동작합니다.')
    print('  종료하려면 이 창에서 Control+C (또는 창 닫기)')
    print('═' * 55)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n서버를 종료합니다.')
        httpd.shutdown()


if __name__ == '__main__':
    main()
