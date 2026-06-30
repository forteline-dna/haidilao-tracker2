#!/usr/bin/env python3
"""
작업일지 미번역(중국어 잔존) 문구 점검 스크립트

작업일지_데이터.json 의 모든 작업내용을 work_translations.json 사전으로 번역해보고,
번역 후에도 중국어(한자)가 남는 문구를 찾아서 보여준다.

사용법:
    python3 미번역_점검.py

출력의 맨 아래 "복사용" 블록을 work_translations.json 의 맨 끝
( 닫는 } 직전 )에 붙여넣고, 빈 따옴표 "" 안에 한국어 번역을 채우면 된다.
그 뒤  python3 build_worklogs_html.py  로 다시 빌드.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
from work_i18n import load_work_map, _norm  # noqa: E402

CJK = re.compile(r'[一-鿿]')   # 한자(중국어). 한글은 별도 영역이라 안 잡힘.


def main():
    data_path = os.path.join(BASE, '작업일지_데이터.json')
    with open(data_path, encoding='utf-8') as f:
        data = json.load(f)

    m = load_work_map(BASE)
    missing = {}   # 정규화 원문 -> set(날짜·직종)

    for log in data.get('logs', []):
        d = log.get('log_date', '?')
        twd = log.get('trade_work_details') or {}
        for trade, v in twd.items():
            if not isinstance(v, dict):
                continue
            for fld in ('work', 'work_cn'):
                s = v.get(fld)
                if not s:
                    continue
                key = _norm(s)
                out = m.get(key, key)
                if CJK.search(out):
                    missing.setdefault(key, set()).add(f'{d} {trade}')
        for s in (log.get('work_contents') or []):
            key = _norm(s)
            out = m.get(key, key)
            if CJK.search(out):
                missing.setdefault(key, set()).add(f'{d} (작업내용)')

    if not missing:
        print('✅ 미번역 중국어 문구가 없습니다. 모두 한국어로 표시됩니다.')
        return

    print(f'⚠️  미번역 문구 {len(missing)}개 발견:\n')
    for key in sorted(missing, key=lambda k: min(missing[k])):
        locs = sorted(missing[key])
        head = locs[0]
        more = f' 외 {len(locs)-1}건' if len(locs) > 1 else ''
        print(f'  • {key!r}')
        print(f'      ↳ {head}{more}')
    print()
    print('─' * 60)
    print('복사용 (work_translations.json 끝에 붙여넣고 "" 안에 번역 입력):')
    print('─' * 60)
    for key in sorted(missing, key=lambda k: min(missing[k])):
        line = json.dumps(key, ensure_ascii=False)
        print(f'  {line}: "",')


if __name__ == '__main__':
    main()
