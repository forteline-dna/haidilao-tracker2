#!/usr/bin/env python3
"""
작업내용(중국어) → 한국어 변환 공용 모듈.

- work_translations.json (원문→한국어 사전)을 사용해 작업일지 데이터의
  trade_work_details[*].work / work_cn 및 work_contents 를 한국어로 변환한다.
- 원본 dict은 건드리지 않고 변환된 사본을 반환 (작업일지_데이터.json 은 중국어 원본 보존).
- 사전에 없는 새 문구는 제어문자만 정리한 원문을 그대로 둔다.
  → 새 문구가 나오면 work_translations.json 에 "원문": "한국어" 한 줄 추가하면 됨.
"""
import os
import json
import copy

_BASE = os.path.dirname(os.path.abspath(__file__))


def load_work_map(base_dir=None):
    p = os.path.join(base_dir or _BASE, 'work_translations.json')
    if os.path.exists(p):
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _norm(s):
    return (s or '').replace('\x00', '').strip()


def translate_data_for_html(data, base_dir=None):
    """data dict의 작업내용을 한국어로 변환한 새 dict를 반환 (원본 비변경)."""
    m = load_work_map(base_dir)
    d = copy.deepcopy(data)

    def tr(s):
        return m.get(_norm(s), _norm(s))

    for log in d.get('logs', []):
        twd = log.get('trade_work_details') or {}
        for v in twd.values():
            if isinstance(v, dict):
                if v.get('work'):
                    v['work'] = tr(v['work'])
                if v.get('work_cn'):
                    v['work_cn'] = tr(v['work_cn'])
        if isinstance(log.get('work_contents'), list):
            log['work_contents'] = [tr(x) for x in log['work_contents']]
    return d
