#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
  하이디라오 영등포점 — 일일작업일보 PDF 파싱 & 대시보드 반영
═══════════════════════════════════════════════════════════
  일일작업일보/ 폴더의 PDF를 파싱하여:
    1. 공종별 인원수 (工种 + 人数)
    2. 총 투입인원 (今日施工人数总计)
    3. 오늘 시공내용 (今日施工内容 / 施工内容)
    4. 위치 정보 (餐厅/后厨 등)
  → 작업일지_데이터.json 및 하이디라오_작업일지.html 업데이트

  사용법:
    python3 parse_and_apply.py         # 전체 PDF 파싱
    python3 parse_and_apply.py --dry   # 파싱 결과만 출력 (파일 변경 없음)
"""

import json, re, os, sys
import fitz  # pymupdf
from datetime import datetime, timezone, timedelta

# ── 경로 ──
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
PDF_DIR   = os.path.join(BASE_DIR, '일일작업일보')
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')
HTML_FILE = os.path.join(BASE_DIR, '하이디라오_작업일지.html')
KST       = timezone(timedelta(hours=9))

# ── 공종 중국어 → 한국어 매핑 ──
TRADE_MAP = {
    # 중국어
    '管理人员':      '관리인원',
    '翻译':          '번역',
    '现场班长':      '현장반장',
    '木工':          '목공',
    '电工':          '전기공',
    '水泥工':        '미장공',
    '保养工':        '보양공',
    '拆除工':        '철거공',
    '防水':          '방수공',
    '防水工':        '방수공',
    '砌墙':          '조적공',
    '砌墙工':        '조적공',
    '金屬':          '금속',
    '金属':          '금속',
    '金属工':        '금속',
    '轻钢工':        '경량철골공',
    '暖通空调工':    '냉난방공조공',
    '暖通空调':      '냉난방공조공',
    '风管（新风，排风)': '풍관(신풍·배풍)',
    '风管(新风,排风)':   '풍관(신풍·배풍)',
    '风管':          '풍관(신풍·배풍)',
    '风管工':        '풍관(신풍·배풍)',
    '消防工':        '소방공',
    '脚手架工':      '비계공',
    '保温':          '단열공',
    '保温工':        '단열공',
    '水工':          '수도공',
    # 한글 지원 (한글화된 PDF 대응)
    '관리인원':      '관리인원',
    '번역':          '번역',
    '직영반장':      '현장반장',
    '현장반장':      '현장반장',
    '금속공':        '금속',
    '금속':          '금속',
    '목공':          '목공',
    '전기공':        '전기공',
    '보양공':        '보양공',
    '미장공':        '미장공',
    '덕트공(급기・배기)': '풍관(신풍·배풍)',
    '덕트공':        '풍관(신풍·배풍)',
    '풍관':          '풍관(신풍·배풍)',
    '풍관(신풍·배풍)': '풍관(신풍·배풍)',
    '조적':          '조적공',
    '조적공':        '조적공',
    '단열공':        '단열공',
    '방수공':        '방수공',
    '배관공(수도공)': '수도공',
    '수도공':        '수도공',
    '비계공':        '비계공',
    '경량철골공':    '경량철골공',
    '철거공':        '철거공',
    '냉난방공조공':  '냉난방공조공',
    '소방공':        '소방공',
}

# 시공내용 중국어 → 한국어
WORK_KR = {
    '现场清理':   '현장청소/폐기물처리',
    '建筑垃圾清运': '건축폐기물 반출',
    '弹线':       '먹매김',
    '墨线作业':   '먹매김 작업',
    '现场弹线':   '현장 먹매김',
    '拆除':       '철거/해체',
    '室内外冷暖空调管道施工': '실내외 냉난방 에어컨 배관 시공',
    '消防管道施工': '소방 배관 시공',
    '给水管道施工': '급수 배관 시공',
    '天花 / 墙体 / 地面配管作业': '천장 / 벽체 / 바닥 배관 작업',
    '厨房地沟制作 / 灯箱制作安装 / 轻钢龙骨修整': '주방 트렌치 제작 / 라이트박스 제작 설치 / 경량철골 천정틀 보수',
    '地面排风施工': '바닥 배기 시공',
    '现场勘查，图纸/甲供材料数量核算': '현장 실사, 도면 및 지급자재 수량 정산',
    '现场协调 / 翻译资料': '현장 조율 / 번역 자료',
    '瓷砖搬运': '타일 양중(반입)',
    '隔墙石膏板施工': '경량벽체 석고보드 시공',
    '金属作业': '금속 작업',
    '木工作业': '목공 작업',
    '防水作业': '방수 작업',
    '给排水设备作业': '급배수 설비 작업',
    '电气作业': '전기 작업',
    '风管作业': '덕트 작업',
    '暖通空调': '냉난방공조(HVAC)',
    '消防作业': '소방 작업',
}

def translate_trade(cn):
    return TRADE_MAP.get(cn, cn)

def translate_work(cn):
    if cn in WORK_KR:
        return WORK_KR[cn]
    result = cn
    # 긴 단어부터 순서대로 치환
    sorted_terms = sorted(WORK_KR.items(), key=lambda x: len(x[0]), reverse=True)
    for k, v in sorted_terms:
        result = result.replace(k, v)
    return result

def log(msg):
    print(msg)

def parse_pdf(pdf_path):
    """
    PDF 1페이지에서 구조화된 데이터 추출 (좌표 기반):
    - 날짜
    - 공종별 인원 (좌측 컬럼: x < 200)
    - 총 인원수
    - 시공내용 (우측 컬럼: x > 300, 공종표 행 범위)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        log(f'  ❌ PDF 열기 실패: {e}')
        return None

    try:
        page    = doc[0]
        full    = page.get_text()
        blocks  = page.get_text('blocks')

        # 모든 텍스트 블록 좌표 수집 (깨짐 방지를 위해 block 단위 수집)
        items = []
        for b in blocks:
            x0, y0, x1, y1, text, block_no, block_type = b
            # \xa0 공백 문자 정규화
            text = text.strip().replace('\xa0', ' ')
            if text:
                items.append({'x': x0, 'y': y0, 'text': text})
        items.sort(key=lambda v: (round(v['y'] / 4) * 4, v['x']))
        doc.close()
    except Exception as e:
        log(f'  ❌ 텍스트 추출 실패: {e}')
        try: doc.close()
        except: pass
        return None

    result = {
        'date': '',
        'total_workers': 0,
        'trades': {},
        'trades_cn': {},
        'trade_work_details': {},
        'work_contents': [],
        'work_contents_cn': [],
        'locations': [],
    }

    # ── 날짜 ──
    date_m = re.search(r'（(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日）', full)
    if not date_m:
        date_m = re.search(r'\((\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\)', full)
    if not date_m:
        date_m = re.search(r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日', full)
    if not date_m:
        date_m = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', full)
    if date_m:
        y, mo, d = date_m.group(1), date_m.group(2).zfill(2), date_m.group(3).zfill(2)
        result['date'] = f'{y}-{mo}-{d}'

    # ── 총 인원 ──
    total_m = re.search(r'(\d+)\s*人', full)
    if not total_m:
        total_m = re.search(r'(\d+)\s*명', full)
    if total_m:
        result['total_workers'] = int(total_m.group(1))

    # ── 공종표 Y 범위 파악 ──
    # "工种" / "人数" 라벨 위치 → 공종표 시작 Y
    table_start_y = None
    table_end_y   = None
    for it in items:
        if ('工种' in it['text'] or '공종' in it['text']) and it['x'] < 200:
            table_start_y = it['y']
        if any(lbl in it['text'] for lbl in ('今日施工人数总计', '施工人数总计', '금일 총 시공 인원')):
            table_end_y = it['y']
            break

    # ── 공종표 파싱 (Y 좌표 기반 행 매핑) ──
    if table_start_y is not None:
        left_items = [
            it for it in items
            if (table_start_y - 5) < it['y'] < (table_end_y or 9999)
            and it['text'] not in ('工종', '人数', '今日施工内容', '施工日志', '施工内容', '完成时间', '重要节点', '项目照片', '工种', '공종', '인원수', '오늘 시공 내용', '시공일지', '시공 내용', '완료 시간', '중요 일정', '프로젝트 사진')
        ]
        
        rows = []
        for it in left_items:
            # 합계 행만 제외 (공종명에 '人员'이 포함될 수 있어 '人' 단독 필터는 쓰지 않음)
            if any(kw in it['text'] for kw in ('总计', '總計', '합계', '人数总计', '총 시공')):
                continue
            matched = False
            for r in rows:
                if abs(r['y'] - it['y']) < 6:
                    r['items'].append(it)
                    matched = True
                    break
            if not matched:
                rows.append({'y': it['y'], 'items': [it]})

        trade_work_details = {}
        for r in sorted(rows, key=lambda x: x['y']):
            r['items'].sort(key=lambda x: x['x'])
            trade_cn = ""
            count = 0
            work_cn_list = []

            for it in r['items']:
                x = it['text'].strip()
                if not x:
                    continue
                if it['x'] < 130:
                    # 좌측 컬럼: 공종명. 신형 PDF는 같은 블록에 '공종명⏎인원수'가 합쳐져 있음
                    parts = [p.strip() for p in x.split('\n') if p.strip()]
                    if parts:
                        trade_cn = parts[0]
                        for p in parts[1:]:
                            if re.match(r'^\d+$', p):
                                count = int(p)
                    # 헤더 행 제외
                    if trade_cn in ('工种', '人数', '공종', '인원수'):
                        trade_cn = ""
                elif 130 <= it['x'] < 220:
                    # 구형(한글 번역본) PDF: 인원수가 별도 컬럼에 있음
                    if re.match(r'^\d+$', x):
                        count = int(x)
                else:
                    for p in x.split('\n'):
                        p = p.strip()
                        if p:
                            work_cn_list.append(p)
            
            if trade_cn:
                trade_ko_std = translate_trade(trade_cn)
                if trade_ko_std in TRADE_MAP.values() or trade_cn in TRADE_MAP:
                    work_cn = ", ".join(work_cn_list)
                    work_ko = translate_work(work_cn)
                    
                    result['trades_cn'][trade_cn] = count
                    result['trades'][trade_ko_std] = result['trades'].get(trade_ko_std, 0) + count
                    
                    if work_ko:
                        trade_work_details[trade_ko_std] = {
                            'count': count,
                            'work': work_ko,
                            'work_cn': work_cn
                        }
                    
                    if work_ko and work_ko not in result['work_contents']:
                        result['work_contents'].append(work_ko)
                    if work_cn and work_cn not in result['work_contents_cn']:
                        result['work_contents_cn'].append(work_cn)

        result['trade_work_details'] = trade_work_details
    else:
        # 폴백: "今日施工内容" 직전 텍스트
        NOISE_LABELS = {
            '施工内容', '今日施工内容', '施工日志', '阶段重要节点', '工种', '人数',
            '完成时间', '重要节点', '项目照片', '甲供品分类统计表',
        }
        contents_cn = []
        for i, it in enumerate(items):
            if '今日施工内容' in it['text'] or '오늘 시공 내용' in it['text']:
                for prev in items[max(0, i-4):i]:
                    cand = prev['text'].strip()
                    if (len(cand) > 3
                            and cand not in NOISE_LABELS
                            and not re.search(r'^\d{4}[年년]', cand)
                            and not re.match(r'^\d+$', cand)):
                        contents_cn.append(cand)
                break
        result['work_contents_cn'] = contents_cn
        result['work_contents']    = [translate_work(c) for c in contents_cn]

    # ── 위치 (2페이지) ──
    try:
        doc2 = fitz.open(pdf_path)
        if doc2.page_count > 1:
            p2 = doc2[1].get_text()
            locs = re.findall(r'(餐厅|后厨|包间|等待区|等候区|厨房|卫生间|用餐区|过道|入口|홀|주방|룸|대기\s*구역|화장실|객석\s*구역|복도|입구)', p2)
            # 위치명도 한국어로 통일
            loc_map = {
                '餐厅': '홀(객석)', '后厨': '주방', '包间': '룸', '等待区': '대기 구역', '等候区': '대기 구역',
                '厨房': '주방', '卫生间': '화장실', '用餐区': '객석 구역', '过道': '복도', '入口': '입구'
            }
            cleaned_locs = []
            for l in locs:
                cleaned_locs.append(loc_map.get(l, l))
            result['locations'] = list(dict.fromkeys(cleaned_locs))
        doc2.close()
    except:
        pass

    # 요약 텍스트
    result['raw_summary'] = ", ".join(result['work_contents_cn'])

    return result


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {'project': '하이디라오 영등포점', 'logs': [], 'total_logs': 0}


def update_html(data):
    """하이디라오_작업일지.html의 WORK_LOGS 객체 업데이트"""
    if not os.path.exists(HTML_FILE):
        log('  ⚠️ HTML 파일 없음')
        return False
    with open(HTML_FILE, encoding='utf-8') as f:
        html = f.read()

    # 작업내용 중국어 → 한국어 변환 (HTML용, 원본 data/JSON은 중국어 유지)
    from work_i18n import translate_data_for_html
    data_html = translate_data_for_html(data, BASE_DIR)
    js_data = json.dumps(data_html, ensure_ascii=False)
    # 줄바꿈/특수문자 이스케이프
    js_data = js_data.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')

    # re.sub에서 백슬래시가 축소되는 버그 방지
    escaped_js_data = js_data.replace('\\', '\\\\')
    new_html, n = re.subn(
        r'const WORK_LOGS = \{.*?\};',
        f'const WORK_LOGS = {escaped_js_data};',
        html, count=1, flags=re.DOTALL
    )
    if n == 0:
        log('  ⚠️ HTML에서 WORK_LOGS 패턴을 찾지 못함')
        return False

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)
    return True


def main():
    dry_run = '--dry' in sys.argv

    log('')
    log('═' * 60)
    log('  📄 일일작업일보 PDF 파싱 → 대시보드 반영')
    log('═' * 60)

    # PDF 목록 수집
    if not os.path.exists(PDF_DIR):
        log(f'❌ 폴더 없음: {PDF_DIR}')
        return

    pdf_files = sorted([
        f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')
    ])
    log(f'📂 PDF {len(pdf_files)}개 발견')

    # 기존 데이터 로드
    data = load_data()
    existing = {l['log_date']: i for i, l in enumerate(data['logs'])}

    updated = 0
    new_added = 0
    failed = 0

    for fname in pdf_files:
        # 날짜 추출 (파일명에서)
        date_m = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
        if not date_m:
            log(f'  ⚠️ 날짜 파싱 불가: {fname}')
            continue
        file_date = date_m.group(1)

        pdf_path = os.path.join(PDF_DIR, fname)
        log(f'\n  📄 [{file_date}] {fname[:55]}...' if len(fname) > 55 else f'\n  📄 [{file_date}] {fname}')

        parsed = parse_pdf(pdf_path)
        if not parsed:
            failed += 1
            continue

        # 파싱 결과 출력
        log(f'     총 인원: {parsed["total_workers"]}명')
        if parsed['trades']:
            trades_str = ', '.join(f'{k}:{v}명' for k, v in list(parsed['trades'].items())[:5])
            if len(parsed['trades']) > 5:
                trades_str += f' 외 {len(parsed["trades"])-5}개'
            log(f'     공종:   {trades_str}')
        if parsed['work_contents']:
            contents_str = ' | '.join(parsed['work_contents'][:3])
            if len(parsed['work_contents']) > 3:
                contents_str += f' 외 {len(parsed["work_contents"])-3}건'
            log(f'     내용:   {contents_str}')

        if dry_run:
            continue

        # 데이터 업데이트
        pdf_info = {
            'total_workers':    parsed['total_workers'],
            'trades':           parsed['trades'],
            'trades_cn':        parsed['trades_cn'],
            'trade_work_details': parsed['trade_work_details'],
            'work_contents':    parsed['work_contents'],
            'work_contents_cn': parsed['work_contents_cn'],
            'locations':        parsed['locations'],
            'pdf_parsed':       True,
            'pdf_file':         fname,
        }

        if file_date in existing:
            # 기존 로그에 PDF 데이터 병합
            idx = existing[file_date]
            data['logs'][idx].update(pdf_info)
            updated += 1
        else:
            # 새 항목 추가
            data['logs'].append({
                'log_date':    file_date,
                'upload_date': file_date,
                'upload_time': '09:00',
                'file_name':   fname,
                'file_key':    '',
                'message_id':  '',
                'sender_id':   '',
                'work_categories': list(parsed['trades'].keys()),
                'day_highlights':  parsed['work_contents'][:8],
                'total_messages':  0,
                **pdf_info,
            })
            new_added += 1

    if not dry_run and (updated + new_added) > 0:
        data['logs'].sort(key=lambda x: x['log_date'])
        data['total_logs'] = len(data['logs'])
        if data['logs']:
            data['period'] = f'{data["logs"][0]["log_date"]} ~ {data["logs"][-1]["log_date"]}'
        data['last_updated'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')

        # JSON 저장
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f'\n  💾 작업일지_데이터.json 저장 완료')

        # HTML 업데이트
        if update_html(data):
            log(f'  🌐 하이디라오_작업일지.html 업데이트 완료')

    # 최종 통계
    # 총 인원 통계
    total_worker_days = sum(
        l.get('total_workers', 0) for l in data['logs']
    )
    max_day = max(data['logs'], key=lambda x: x.get('total_workers', 0), default=None)

    log('')
    log('═' * 60)
    if dry_run:
        log('  ℹ️ DRY RUN — 파일 변경 없음')
    else:
        log(f'  ✅ 완료!')
        log(f'     기존 로그 업데이트: {updated}개')
        log(f'     새로 추가:          {new_added}개')
        log(f'     실패:               {failed}개')
    log(f'\n  📊 전체 통계:')
    log(f'     총 시공일수:     {len(data["logs"])}일')
    log(f'     누적 투입인원:   {total_worker_days:,}명')
    if max_day:
        log(f'     최다 투입일:     {max_day["log_date"]} ({max_day.get("total_workers", 0)}명)')
    log('═' * 60)


if __name__ == '__main__':
    main()
