#!/usr/bin/env python3
"""
하이디라오_작업일지.html 재생성 스크립트
인원수 관리 기능 포함 (일별/주별/월별 집계)
"""
import json, re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')
HTML_FILE = os.path.join(BASE_DIR, '하이디라오_작업일지.html')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# ── 작업내용 중국어 → 한국어 변환 (빌드 시점, 원본 JSON은 보존) ──
from work_i18n import translate_data_for_html
data = translate_data_for_html(data, BASE_DIR)

data_json = json.dumps(data, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>하이디라오 영등포점 — 시공 작업일지</title>
<meta name="description" content="하이디라오 영등포점 공사 프로젝트 시공일지 대시보드. 공종별 인원 집계, 주별/월별 분석.">
<!-- 홈 화면 추가(PWA): 갤럭시/아이폰에서 아이콘으로 실행 -->
<link rel="manifest" href="./manifest.webmanifest">
<meta name="theme-color" content="#c0652b">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="작업일지">
<link rel="apple-touch-icon" href="./icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="./icons/icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-primary: #f8f8f8;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-card-hover: #fafafa;
  --bg-glass: #f2f2f2;
  --border: #e5e5e5;
  --border-active: #d0d0d0;
  --border-glow: #1a1a1a;
  --text-primary: #1a1a1a;
  --text-secondary: #6b6b6b;
  --text-muted: #a0a0a0;
  --accent: #1a1a1a;
  --accent-deep: #000000;
  --accent-glow: rgba(0,0,0,0.04);
  --green: #2d8a56;
  --yellow: #b8860b;
  --red: #c0392b;
  --blue: #2c5aa0;
  --purple: #6b3fa0;
  --cyan: #1a7a7a;
  --pink: #a0365e;
  --orange: #c0652b;
  --shadow-md: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-glow: 0 4px 16px rgba(0,0,0,0.06);
  --radius: 4px;
  --radius-sm: 3px;
}}
*{{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family:'Inter','Noto Sans KR',system-ui,sans-serif;
  background:var(--bg-primary); color:var(--text-primary);
  min-height:100vh; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}}
.container {{ max-width:1200px; margin:0 auto; padding:48px 32px; }}

/* ── ANIMATIONS ── */
@keyframes fadeInUp {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}
@keyframes shimmer {{ 0%{{background-position:-200% 0}} 100%{{background-position:200% 0}} }}
@keyframes pulseGlow {{ 0%,100%{{opacity:0.5}} 50%{{opacity:1}} }}
.fade-in {{ animation:fadeInUp 0.4s ease both; }}

/* ── HEADER ── */
.header {{
  margin-bottom:56px; padding:0 0 40px;
  border-bottom:2px solid #1a1a1a;
  position:relative;
}}
.header::before {{ display:none; }}
.header h1 {{
  font-size:1.75rem; font-weight:700; letter-spacing:-0.8px;
  background:none; -webkit-text-fill-color:var(--text-primary);
  margin-bottom:6px; filter:none;
  text-align:left;
}}
.header p {{ color:var(--text-secondary); font-size:0.82rem; letter-spacing:0.2px; text-align:left; }}
.header .badge {{
  display:inline-flex; align-items:center; gap:5px;
  padding:4px 12px; margin-top:12px;
  background:transparent; border:1px solid var(--border);
  border-radius:2px; font-size:0.72rem; color:var(--text-secondary);
  backdrop-filter:none; text-transform:uppercase; letter-spacing:0.8px;
}}
.action-bar {{ display:flex; gap:8px; justify-content:flex-start; margin-top:20px; flex-wrap:wrap; }}
.action-btn {{
  padding:9px 20px; border-radius:2px; font-size:0.78rem; font-weight:600;
  border:1px solid var(--border); cursor:pointer; transition:all 0.2s;
  display:flex; align-items:center; gap:6px;
  box-shadow:none; text-transform:uppercase; letter-spacing:0.5px;
}}
.action-btn:hover {{ border-color:var(--accent); color:var(--accent); transform:none; box-shadow:none; }}
.btn-excel {{ background:var(--bg-secondary); color:var(--text-primary); }}
.update-date {{ display:inline-flex; align-items:center; font-size:0.74rem; color:var(--text-secondary); margin:0 4px; white-space:nowrap; }}
.btn-update {{ background:#1A7A4A; color:white; border-color:#1A7A4A; }}
.btn-update:hover {{ background:#15633c; border-color:#15633c; color:white; }}
.btn-update.loading {{ opacity:0.75; cursor:progress; pointer-events:none; }}
.btn-update.loading::before {{
  content:""; width:12px; height:12px; border:2px solid rgba(255,255,255,0.4);
  border-top-color:#fff; border-radius:50%; display:inline-block;
  animation:spin 0.7s linear infinite;
}}
@keyframes spin {{ to {{ transform:rotate(360deg); }} }}

/* ── STATS ── */
.stats-row {{
  display:grid; grid-template-columns:repeat(6,1fr);
  gap:0; margin-bottom:48px;
  border:1px solid var(--border);
}}
.stat-card {{
  background:var(--bg-card); border:none;
  border-right:1px solid var(--border);
  border-radius:0; padding:28px 20px; text-align:center;
  transition:background 0.2s; position:relative; overflow:hidden;
  backdrop-filter:none;
}}
.stat-card:last-child {{ border-right:none; }}
.stat-card::before {{ display:none; }}
.stat-card:hover {{
  background:var(--bg-card-hover);
  transform:none; border-color:transparent;
  box-shadow:none;
}}
.stat-card:hover::before {{ display:none; }}
.stat-value {{ font-size:1.8rem; font-weight:300; margin-bottom:8px; letter-spacing:-1px; color:var(--text-primary); }}
.stat-label {{ font-size:0.65rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px; font-weight:500; }}

/* ── SECTION TITLE ── */
.section-title {{
  font-size:0.72rem; font-weight:600; margin-bottom:20px;
  display:flex; align-items:center; gap:8px;
  color:var(--text-muted); text-transform:uppercase; letter-spacing:1.5px;
}}
.section-title .icon {{ font-size:0.85rem; }}
.section-title::after {{
  content:''; flex:1; height:1px;
  background:var(--border); margin-left:12px;
}}

/* ── TABS ── */
.tab-bar {{
  display:flex; gap:0; margin-bottom:28px;
  background:transparent; border-radius:0;
  padding:0; width:fit-content;
  border:none; border-bottom:1px solid var(--border);
}}
.tab-btn {{
  padding:10px 24px; border-radius:0; border:none; cursor:pointer;
  font-size:0.78rem; font-weight:600; color:var(--text-muted);
  background:transparent; transition:all 0.2s;
  text-transform:uppercase; letter-spacing:0.8px;
  border-bottom:2px solid transparent; margin-bottom:-1px;
}}
.tab-btn.active {{
  background:transparent; color:var(--text-primary);
  border-bottom:2px solid var(--accent);
  box-shadow:none;
}}
.tab-btn:hover:not(.active) {{ color:var(--text-secondary); background:transparent; }}
.tab-panel {{ display:none; }}
.tab-panel.active {{ display:block; animation:fadeInUp 0.3s ease; }}

/* ── WORKER SUMMARY TABLE ── */
.worker-table-wrap {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden; margin-bottom:40px;
  backdrop-filter:none;
}}
.worker-table {{ width:100%; border-collapse:collapse; }}
.worker-table thead th {{
  padding:12px 16px; text-align:left; font-size:0.68rem; font-weight:600;
  color:var(--text-muted); text-transform:uppercase; letter-spacing:1px;
  background:var(--bg-glass); border-bottom:1px solid var(--border);
  white-space:nowrap;
}}
.worker-table thead th.num {{ text-align:center; }}
.worker-table tbody tr {{
  border-bottom:1px solid #f0f0f0; transition:background 0.15s;
}}
.worker-table tbody tr:hover {{ background:var(--bg-card-hover); }}
.worker-table tbody tr:last-child {{ border-bottom:none; }}
.worker-table td {{ padding:11px 16px; font-size:0.82rem; vertical-align:middle; }}
.worker-table td.num {{ text-align:center; font-weight:600; }}
.worker-table td.total-cell {{
  text-align:center; font-weight:700; font-size:0.95rem;
  color:var(--text-primary);
}}
.worker-table tr.subtotal {{
  background:#f5f5f5; font-weight:700;
}}
.worker-table tr.subtotal td {{ color:var(--text-primary); }}
.trade-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:8px; flex-shrink:0; box-shadow:none; }}
.trade-name-cell {{ display:flex; align-items:center; gap:4px; }}

/* ── WORKER EDIT INLINE ── */
.worker-input {{
  width:52px; padding:4px 6px; background:var(--bg-primary);
  border:1px solid var(--border); border-radius:2px;
  color:var(--text-primary); font-size:0.82rem; text-align:center;
  outline:none; transition:all 0.2s;
}}
.worker-input:focus {{ border-color:var(--accent); box-shadow:none; }}
.worker-input::-webkit-inner-spin-button {{ opacity:1; }}

/* ── LOG TABLE ── */
.log-table-wrap {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden;
  backdrop-filter:none;
}}
.log-table {{ width:100%; border-collapse:collapse; }}
.log-table thead th {{
  padding:12px 16px; text-align:left; font-size:0.68rem; font-weight:600;
  color:var(--text-muted); text-transform:uppercase; letter-spacing:1px;
  background:var(--bg-glass); border-bottom:1px solid var(--border);
  position:sticky; top:0; z-index:2;
}}
.log-table tbody tr {{
  border-bottom:1px solid #f0f0f0; transition:background 0.15s; cursor:pointer;
}}
.log-table tbody tr:hover {{ background:var(--bg-card-hover); }}
.log-table tbody tr:last-child {{ border-bottom:none; }}
.log-table td {{ padding:11px 16px; font-size:0.82rem; vertical-align:middle; }}
.date-cell {{ font-weight:600; white-space:nowrap; font-variant-numeric:tabular-nums; }}
.date-cell.sat {{ color:#2563eb; }}
.date-cell.sun {{ color:#dc2626; }}
.date-cell.sat .weekday {{ color:#2563eb; }}
.date-cell.sun .weekday {{ color:#dc2626; }}
.weekday {{ font-size:0.7rem; color:var(--text-muted); margin-left:4px; }}
.manager-num {{ font-size:0.92rem; font-weight:700; color:var(--text-muted); }}
.cat-tags {{ display:flex; flex-wrap:wrap; gap:4px; }}
.cat-tag {{
  display:inline-block; padding:2px 8px; border-radius:2px;
  font-size:0.68rem; font-weight:500; white-space:nowrap;
  backdrop-filter:none;
}}
.worker-badge {{
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 10px; border-radius:2px; font-size:0.75rem; font-weight:700;
  background:var(--accent-glow); border:1px solid var(--border);
  color:var(--text-primary); cursor:pointer; transition:all 0.2s;
}}
.worker-badge:hover {{ background:#e8e8e8; transform:none; }}
.worker-badge.empty {{ background:transparent; border-color:var(--border); color:var(--text-muted); }}
.worker-total-big {{ font-size:1.1rem; font-weight:700; color:var(--green); }}

/* ── FILTER BAR ── */
.filter-bar {{ display:flex; gap:8px; margin-bottom:24px; flex-wrap:wrap; align-items:center; }}
.filter-input {{
  flex:1; min-width:200px; padding:10px 16px; background:var(--bg-secondary);
  border:1px solid var(--border); border-radius:2px;
  color:var(--text-primary); font-size:0.85rem; outline:none; transition:all 0.2s;
}}
.filter-input:focus {{ border-color:var(--accent); box-shadow:none; }}
.filter-input::placeholder {{ color:var(--text-muted); }}
.filter-btn {{
  padding:9px 16px; background:var(--bg-secondary); border:1px solid var(--border);
  border-radius:2px; color:var(--text-secondary); font-size:0.78rem;
  cursor:pointer; transition:all 0.2s; white-space:nowrap;
  text-transform:uppercase; letter-spacing:0.5px; font-weight:600;
}}
.filter-btn:hover {{ border-color:var(--accent); color:var(--accent); }}
.filter-btn.active {{ background:var(--accent); border-color:var(--accent); color:white; }}

/* ── WEEK/MONTH GROUP ── */
.period-group {{ margin-bottom:32px; }}
.period-header {{
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 18px; background:var(--bg-glass);
  border-radius:0; border:1px solid var(--border); border-bottom:none;
  cursor:pointer; transition:background 0.15s;
}}
.period-header:hover {{ background:#eee; }}
.period-label {{ font-size:0.85rem; font-weight:600; display:flex; align-items:center; gap:8px; }}
.period-total {{
  font-size:1.1rem; font-weight:700; color:var(--text-primary);
  display:flex; align-items:center; gap:6px;
}}
.period-total small {{ font-size:0.72rem; color:var(--text-muted); font-weight:400; }}

/* ── BAR CHART ── */
.bar-chart {{ padding:18px; background:var(--bg-card); border:1px solid var(--border); border-radius:0; backdrop-filter:none; }}
.bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:6px; }}
.bar-row:last-child {{ margin-bottom:0; }}
.bar-label {{ font-size:0.75rem; color:var(--text-secondary); width:130px; flex-shrink:0; text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar-track {{ flex:1; height:16px; background:#f0f0f0; border-radius:1px; overflow:hidden; position:relative; }}
.bar-fill {{ height:100%; border-radius:1px; transition:width 0.6s ease; min-width:2px; position:relative; opacity:0.85; }}
.bar-fill::after {{ display:none; }}
.bar-val {{ font-size:0.75rem; font-weight:600; color:var(--text-primary); width:32px; text-align:right; flex-shrink:0; }}

/* ── 공종별 날짜 투입 그래프 모달 ── */
.td-chart {{ max-height:60vh; overflow-y:auto; }}
.td-row {{ padding:8px 4px; border-bottom:1px solid #f3f3f3; cursor:pointer; transition:background 0.12s; }}
.td-row:last-child {{ border-bottom:none; }}
.td-row:hover {{ background:var(--bg-secondary); }}
.td-bar-line {{ display:flex; align-items:center; gap:10px; }}
.td-date {{ font-size:0.78rem; color:var(--text-secondary); width:92px; flex-shrink:0; font-variant-numeric:tabular-nums; }}
.td-date small {{ color:var(--text-muted); }}
.td-cnt {{ font-size:0.82rem; font-weight:700; width:42px; text-align:right; flex-shrink:0; font-variant-numeric:tabular-nums; }}
.td-works {{ margin:5px 0 0 102px; display:flex; flex-wrap:wrap; gap:5px; }}
.td-work {{ font-size:0.74rem; color:var(--text-secondary); background:var(--bg-secondary); border:1px solid var(--border); border-radius:3px; padding:2px 7px; line-height:1.45; }}
@media(max-width:768px) {{
  .td-works {{ margin-left:0; }}
  .td-date {{ width:78px; }}
}}

/* ── WEEKLY WORK SUMMARY ── */
.week-summary {{ margin-top:16px; padding-top:14px; border-top:1px dashed var(--border); }}
.week-summary-title {{ font-size:0.74rem; font-weight:700; color:var(--text-secondary); margin-bottom:10px; letter-spacing:0.3px; }}
.ws-row {{ display:flex; align-items:flex-start; gap:8px; padding:5px 0; border-bottom:1px solid #f3f3f3; font-size:0.8rem; }}
.ws-row:last-of-type {{ border-bottom:none; }}
.ws-dot {{ width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-top:5px; }}
.ws-trade {{ width:120px; flex-shrink:0; font-weight:600; color:var(--text-primary); }}
.ws-work {{ flex:1; color:var(--text-secondary); line-height:1.5; }}
.ws-loc {{ margin-top:10px; font-size:0.76rem; color:var(--text-muted); }}
@media(max-width:768px) {{
  .ws-row {{ flex-wrap:wrap; }}
  .ws-trade {{ width:auto; }}
}}

/* ── MODAL ── */
.modal-overlay {{
  display:none; position:fixed; top:0; left:0; right:0; bottom:0;
  background:rgba(0,0,0,0.2); z-index:100; align-items:center; justify-content:center;
  backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
}}
.modal-overlay.active {{ display:flex; }}
.modal {{
  background:var(--bg-secondary); border:1px solid var(--border);
  border-radius:4px; max-width:700px; width:92%; max-height:85vh;
  overflow-y:auto; padding:36px; box-shadow:0 20px 60px rgba(0,0,0,0.1);
  animation:modalIn 0.25s ease;
  backdrop-filter:none;
}}
@keyframes modalIn {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}
.modal-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; }}
.modal-title {{ font-size:1.1rem; font-weight:600; letter-spacing:-0.3px; }}
.modal-close {{
  background:none; border:none; color:var(--text-muted); font-size:1.5rem;
  cursor:pointer; padding:4px 8px; transition:color 0.2s;
}}
.modal-close:hover {{ color:var(--text-primary); }}
.modal-meta {{ display:flex; gap:16px; margin-bottom:20px; flex-wrap:wrap; }}
.modal-meta-item {{ font-size:0.82rem; color:var(--text-secondary); display:flex; align-items:center; gap:4px; }}
.modal-section {{ margin-bottom:20px; }}
.modal-section-title {{ font-size:0.72rem; font-weight:600; color:var(--text-muted); margin-bottom:10px; text-transform:uppercase; letter-spacing:1px; }}

/* ── WORKER INPUT GRID ── */
.worker-input-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:8px; }}
.worker-input-row {{
  display:flex; align-items:center; justify-content:space-between;
  padding:8px 12px; background:var(--bg-primary);
  border-radius:2px; gap:8px; border:1px solid #f0f0f0;
}}
.worker-input-label {{ font-size:0.78rem; color:var(--text-secondary); flex:1; }}
.wi-number {{
  width:60px; padding:4px 8px; background:var(--bg-secondary);
  border:1px solid var(--border); border-radius:2px;
  color:var(--text-primary); font-size:0.85rem; text-align:center;
  outline:none; transition:border-color 0.2s;
}}
.wi-number:focus {{ border-color:var(--accent); }}
.total-row {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 16px; background:var(--bg-primary);
  border:1px solid var(--border); border-radius:2px; margin-top:12px;
}}
.total-row .label {{ font-size:0.85rem; font-weight:600; }}
.total-row .value {{ font-size:1.3rem; font-weight:700; color:var(--text-primary); }}
.modal-highlight {{
  font-size:0.82rem; color:var(--text-secondary); padding:6px 0;
  border-bottom:1px solid #f0f0f0;
}}
/* 작업자/관리자 분리 배지 */
.split-row {{ display:flex; gap:8px; margin-top:8px; }}
.split-badge {{
  flex:1; text-align:center; padding:8px 10px; border-radius:2px;
  font-size:0.8rem; font-weight:600;
}}
.split-badge b {{ font-size:1.05rem; }}
.split-badge.labor {{ background:#e8f5ee; color:var(--green); border:1px solid #c8e6d4; }}
.split-badge.mgr {{ background:#f1f1f3; color:var(--text-secondary); border:1px solid var(--border); }}
/* 관리·지원 구분 라벨 */
.wi-group-label {{
  grid-column:1/-1; margin-top:10px; padding-top:8px; border-top:1px dashed var(--border);
  font-size:0.7rem; font-weight:600; color:var(--text-muted);
  text-transform:uppercase; letter-spacing:1px;
}}
/* 당일 작업 사항 */
.work-item {{
  font-size:0.82rem; color:var(--text-secondary); padding:6px 0;
  border-bottom:1px solid #f0f0f0; display:flex; align-items:center; gap:6px;
}}
.work-item b {{ color:var(--text-primary); font-weight:600; }}
.loc-row {{ margin-top:10px; font-size:0.78rem; color:var(--text-secondary); }}
.loc-chip {{
  display:inline-block; padding:2px 9px; margin:2px; border-radius:11px;
  background:var(--bg-primary); border:1px solid var(--border); font-size:0.72rem;
}}
/* PDF 미리보기 */
.pdf-link {{ cursor:pointer; color:var(--accent); text-decoration:underline; text-decoration-style:dotted; }}
.pdf-link:hover {{ color:#000; }}
.pdf-preview {{ margin:0 0 20px; border:1px solid var(--border); border-radius:4px; overflow:hidden; background:#f7f7f7; }}
.pdf-frame {{ width:100%; height:560px; border:none; display:block; }}
.pdf-bar {{ padding:8px 12px; text-align:right; border-top:1px solid var(--border); }}
.pdf-bar a {{ font-size:0.75rem; color:var(--accent); text-decoration:none; }}
.pdf-bar a:hover {{ text-decoration:underline; }}
.modal-btn {{
  padding:9px 20px; border-radius:2px; font-size:0.82rem; font-weight:600;
  border:1px solid var(--border); cursor:pointer; transition:all 0.2s;
  text-transform:uppercase; letter-spacing:0.5px;
}}
.modal-btn-primary {{ background:var(--accent); color:white; border-color:var(--accent); }}
.modal-btn-primary:hover {{ background:#333; }}
.modal-btn-cancel {{ background:var(--bg-secondary); color:var(--text-secondary); }}
.modal-btn-cancel:hover {{ color:var(--text-primary); border-color:var(--accent); }}
.modal-footer {{ display:flex; gap:8px; justify-content:flex-end; margin-top:24px; }}

/* ── TOAST ── */
.toast-wl {{
  position:fixed; bottom:28px; right:28px; z-index:999;
  background:var(--bg-secondary); border:1px solid var(--green);
  border-radius:2px; padding:12px 20px;
  color:var(--green); font-size:0.82rem; font-weight:600;
  box-shadow:0 8px 32px rgba(0,0,0,0.08);
  transform:translateY(100px); opacity:0; transition:all 0.3s ease;
}}
.toast-wl.show {{ transform:translateY(0); opacity:1; }}

/* ── MISSING SECTION ── */
.missing-section {{
  margin-top:24px; padding:18px; background:#fef5f5;
  border-radius:2px; border:1px solid #f0d0d0;
}}
.missing-title {{ font-size:0.78rem; font-weight:600; color:var(--red); margin-bottom:10px; display:flex; align-items:center; gap:6px; text-transform:uppercase; letter-spacing:0.5px; }}
.missing-list {{ display:flex; gap:6px; flex-wrap:wrap; }}
.missing-day {{ font-size:0.78rem; color:var(--red); padding:4px 10px; background:white; border-radius:2px; border:1px solid #f0d0d0; transition:all 0.15s; }}
.missing-day:hover {{ background:#fee; }}

/* ── CALENDAR ── */
.calendar-section {{ margin-bottom:48px; }}
.month-group {{ margin-bottom:28px; }}
.month-label {{
  font-size:0.82rem; font-weight:600; margin-bottom:12px; color:var(--text-primary);
  display:flex; align-items:center; gap:8px;
}}
.day-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(38px,1fr)); gap:3px; }}
.day-cell {{
  aspect-ratio:1; border-radius:2px; display:flex; align-items:center; justify-content:center;
  font-size:0.72rem; font-weight:500; cursor:pointer; transition:all 0.15s;
  border:1px solid transparent; position:relative;
}}
.day-cell.has-log {{
  background:#e8f5e9; color:var(--green);
  border-color:#c8e6c9;
}}
.day-cell.has-log:hover {{
  background:#c8e6c9; transform:none; z-index:2;
  box-shadow:none;
}}
.day-cell.missing {{ background:#ffebee; color:var(--red); border-color:#ffcdd2; }}
.day-cell.empty {{ background:#fafafa; color:var(--text-muted); }}
.day-cell.note {{ background:#fff7e6; color:var(--orange); border-color:#ffe0b2; cursor:help; }}

/* ── CAT GRID ── */
.cat-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:0; margin-bottom:48px; border:1px solid var(--border); }}
.cat-chip {{
  background:var(--bg-card); border:none;
  border-right:1px solid var(--border); border-bottom:1px solid var(--border);
  border-radius:0; padding:14px 16px;
  display:flex; align-items:center; gap:10px; transition:background 0.15s;
  backdrop-filter:none; cursor:pointer;
}}
.cat-chip:hover {{ background:var(--bg-card-hover); transform:none; box-shadow:none; }}
.cat-chip .cat-go {{ font-size:0.7rem; color:var(--text-muted); opacity:0; transition:opacity 0.15s; flex-shrink:0; }}
.cat-chip:hover .cat-go {{ opacity:1; }}
.cat-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; box-shadow:none; }}
.cat-name {{ font-size:0.82rem; font-weight:400; flex:1; color:var(--text-secondary); }}
.cat-count {{ font-size:0.85rem; font-weight:700; font-variant-numeric:tabular-nums; text-align:right; display:flex; flex-direction:column; align-items:flex-end; line-height:1.3; }}
.cat-head {{ font-size:0.66rem; font-weight:500; color:var(--text-muted); }}

/* ── PROGRESS BAR (D-Day) ── */
.progress-wrap {{ margin-top:8px; }}
.progress-bar {{ height:2px; border-radius:0; background:#e5e5e5; overflow:hidden; }}
.progress-fill {{ height:100%; border-radius:0; transition:width 1s ease; }}
.progress-label {{ font-size:0.6rem; color:var(--text-muted); margin-top:4px; text-align:center; letter-spacing:0.5px; }}

@media(max-width:768px) {{
  .stats-row {{ grid-template-columns:repeat(2,1fr); }}
  .cat-grid {{ grid-template-columns:repeat(2,1fr); }}
  .header h1 {{ font-size:1.4rem; }}
  .bar-label {{ width:90px; font-size:0.68rem; }}
  .container {{ padding:24px 16px; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header fade-in">
    <h1>📋 하이디라오 영등포점 시공 작업일지</h1>
    <p>海底捞韩国永登浦店 施工日志 Dashboard — 공종별 인원 집계</p>
    <div class="action-bar">
      <button class="action-btn btn-update" id="btnUpdate" onclick="runUpdate()">🔄 Lark 채팅 수집 · 지금 업데이트</button>
      <span class="update-date" id="updateDate"></span>
      <button class="action-btn btn-excel" onclick="exportExcel()">📊 엑셀 보고서</button>
    </div>
  </div>

  <div class="stats-row" id="statsRow"></div>

  <div class="section-title"><span class="icon">🏗️</span> 공종별 시공 현황</div>
  <div class="cat-grid" id="catGrid"></div>

  <!-- ── 인원 집계 탭 ── -->
  <div class="section-title"><span class="icon">👷</span> 인원 집계</div>
  <div class="tab-bar">
    <button class="tab-btn active" id="tab-daily" onclick="switchTab('daily')">일별</button>
    <button class="tab-btn" id="tab-weekly" onclick="switchTab('weekly')">주별</button>
    <button class="tab-btn" id="tab-monthly" onclick="switchTab('monthly')">월별</button>
  </div>

  <div class="tab-panel active" id="panel-daily">
    <div class="filter-bar">
      <input class="filter-input" id="searchDaily" placeholder="🔍 날짜, 공종 검색..." oninput="renderDailyTable()">
      <button class="filter-btn active" data-f="all" onclick="setDailyFilter('all',this)">전체</button>
      <button class="filter-btn" data-f="has-workers" onclick="setDailyFilter('has-workers',this)">인원 입력됨</button>
      <button class="filter-btn" data-f="no-workers" onclick="setDailyFilter('no-workers',this)">미입력</button>
    </div>
    <div class="worker-table-wrap">
      <table class="worker-table">
        <thead>
          <tr>
            <th>날짜</th>
            <th>공종별 인원</th>
            <th class="num" style="min-width:80px">총인원</th>
            <th class="num" style="min-width:60px">관리</th>
            <th style="min-width:70px">작업</th>
          </tr>
        </thead>
        <tbody id="dailyTableBody"></tbody>
      </table>
    </div>
  </div>

  <div class="tab-panel" id="panel-weekly">
    <div id="weeklyContent"></div>
  </div>

  <div class="tab-panel" id="panel-monthly">
    <div id="monthlyContent"></div>
  </div>

  <!-- ── 달력 ── -->
  <div class="section-title" style="margin-top:32px"><span class="icon">📅</span> 월별 달력</div>
  <div class="calendar-section" id="calendarSection"></div>

  <div class="missing-section" id="missingSection"></div>
</div>

<!-- 인원 입력 모달 -->
<div class="modal-overlay" id="modalOverlay">
  <div class="modal" id="modal"></div>
</div>
<div class="toast-wl" id="toastWL"></div>

<script src="https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js"></script>
<script>
// ===== DATA =====
const WORK_LOGS = {data_json};

// ===== 작업일지 없는 날 (사유 표기) =====
const NO_LOG_DAYS = {{
  '2026-06-24': '바닥 콘크리트 타설 (작업일지 없음)',
}};

// ===== TRADE COLOR MAP =====
const TRADE_COLORS = {{
  '철거공사': '#ef4444',
  '가설공사': '#94a3b8',
  '먹매김·측량': '#14b8a6',
  '조적공사': '#f97316',
  '금속공사': '#78716c',
  '소방·방화공사': '#dc2626',
  '급배수·위생공사': '#0ea5e9',
  'HVAC·기계설비공사': '#22c55e',
  '전기공사': '#eab308',
  '미장/타일공사': '#06b6d4',
  '목공사/천장공사': '#8b5cf6',
  '방수공사': '#3b82f6',
  '가스설비공사': '#f59e0b',
  '도면·설계변경': '#6366f1',
  '자재·발주': '#a855f7',
  '가구·FF&E': '#ec4899',
  '현장반장': '#0d9488',
  '관리인원': '#1e293b',
  '번역': '#64748b',
}};

// 작업자 직종(인원) → 공종 매핑. 모든 화면을 공종 기준으로 통일한다.
const ROLE_TO_TRADE = {{
  '비계공': '가설공사', '보양공': '가설공사',
  '철거공': '철거공사',
  '조적공': '조적공사',
  '방수공': '방수공사', '단열공': '방수공사',
  '미장공': '미장/타일공사',
  '목공': '목공사/천장공사', '경량철골공': '목공사/천장공사',
  '금속': '금속공사',
  '수도공': '급배수·위생공사',
  '소방공': '소방·방화공사',
  '전기공': '전기공사',
  '냉난방공조공': 'HVAC·기계설비공사', '풍관(신풍·배풍)': 'HVAC·기계설비공사',
  // 관리·지원 인력 (공종 아님)
  '관리인원': '관리인원', '번역': '번역', '현장반장': '현장반장',
}};

// 공종 표시 순서 (공종 → 관리·지원 순). 새 공종이 나오면 뒤에 자동 추가됨.
const TRADE_ORDER = [
  '가설공사','철거공사','먹매김·측량','조적공사','금속공사','목공사/천장공사',
  '방수공사','미장/타일공사','급배수·위생공사','전기공사','HVAC·기계설비공사',
  '소방·방화공사','가스설비공사','자재·발주','도면·설계변경','가구·FF&E',
  '현장반장','관리인원','번역',
];
// 관리·지원 인력 (공종별 시공 현황·태그에서 제외)
const SUPPORT_TRADES = ['현장반장','관리인원','번역'];
// 관리자(그레이) = 관리인원 + 번역. 나머지(현장반장 포함)는 작업자(녹색).
const MANAGER_TRADES = ['관리인원','번역'];

function tradeOf(k) {{ return ROLE_TO_TRADE[k] || k; }}

const WEEKDAYS = ['일','월','화','수','목','금','토'];
let currentFilter = 'all';
let hasChanges = false;

// ===== WORKER STORAGE =====
function getWorkerData() {{
  try {{
    const raw = localStorage.getItem('workerData_haidilao');
    return raw ? JSON.parse(raw) : {{}};
  }} catch(e) {{ return {{}}; }}
}}
function saveWorkerData(data) {{
  localStorage.setItem('workerData_haidilao', JSON.stringify(data));
}}
// 직종/공종 혼재 딕셔너리를 공종 기준으로 합산 정규화
function normalizeWorkers(dict) {{
  const out = {{}};
  if (!dict || typeof dict !== 'object') return out;
  Object.entries(dict).forEach(([k, v]) => {{
    const t = tradeOf(k);
    out[t] = (out[t] || 0) + (parseInt(v) || 0);
  }});
  return out;
}}
function getWorkers(logDate) {{
  const wd = getWorkerData();
  if (wd[logDate] && Object.keys(wd[logDate]).length > 0) return normalizeWorkers(wd[logDate]);
  // fallback: JSON 데이터의 trades 필드(직종)를 공종으로 정규화
  const log = WORK_LOGS.logs.find(l => l.log_date === logDate);
  if (log && log.trades && typeof log.trades === 'object' && !Array.isArray(log.trades)) {{
    return normalizeWorkers(log.trades);
  }}
  return {{}};
}}
function setWorkers(logDate, tradeWorkers) {{
  const wd = getWorkerData();
  wd[logDate] = tradeWorkers;
  saveWorkerData(wd);
  hasChanges = true;
}}
function getTotalWorkers(logDate) {{
  const w = getWorkers(logDate);
  return Object.values(w).reduce((a,b) => a + (parseInt(b)||0), 0);
}}
// 관리자(관리인원+번역) 합계
function getManagerTotal(logDate) {{
  const w = getWorkers(logDate);
  return MANAGER_TRADES.reduce((a,t) => a + (parseInt(w[t])||0), 0);
}}
// 작업자 합계 (총원 - 관리자, 현장반장은 작업자에 포함)
function getLaborTotal(logDate) {{
  return getTotalWorkers(logDate) - getManagerTotal(logDate);
}}

// ===== INIT =====
function renderUpdateDate() {{
  const el = document.getElementById('updateDate');
  if (!el) return;
  const raw = (WORK_LOGS.last_updated || '').replace(/:\\d\\d\\s*KST$/, '').trim();
  el.textContent = raw ? '🕒 최근 업데이트: ' + raw : '';
}}
// 로컬 서버(맥)에서 열렸는지 여부 — 아니면 온라인(GitHub Pages) 보기
const IS_LOCAL = ['localhost', '127.0.0.1'].includes(location.hostname)
  || /^192\.168\./.test(location.hostname) || /^10\./.test(location.hostname)
  || location.protocol === 'file:';

function init() {{
  // 온라인 보기에서는 로컬 전용 '지금 업데이트' 버튼 숨김 (서버 없으면 동작 불가)
  if (!IS_LOCAL) {{
    const btn = document.getElementById('btnUpdate');
    if (btn) btn.style.display = 'none';
  }}
  renderUpdateDate();
  renderStats();
  renderCatGrid();
  renderDailyTable();
  renderWeekly();
  renderMonthly();
  renderCalendar();
  renderMissing();
}}

// ===== STATS =====
function renderStats() {{
  const logs = WORK_LOGS.logs;
  const totalWorkers = logs.reduce((s, l) => s + getTotalWorkers(l.log_date), 0);
  const workedDays = logs.filter(l => getTotalWorkers(l.log_date) > 0).length;
  const allTrades = new Set(getPdfTrades().filter(t =>
    WORK_LOGS.logs.some(l => (parseInt(getWorkers(l.log_date)[t]) || 0) > 0)));
  const avgWorkers = workedDays > 0 ? Math.round(totalWorkers / workedDays) : 0;

  const endDate = new Date('2026-08-16');
  const today = new Date(); today.setHours(0,0,0,0);
  const daysLeft = Math.ceil((endDate - today) / (1000*60*60*24));
  const dDayText = daysLeft > 0 ? `D-${{daysLeft}}` : daysLeft === 0 ? 'D-Day' : `D+${{Math.abs(daysLeft)}}`;
  const dDayColor = daysLeft > 30 ? '#3b82f6' : daysLeft > 14 ? '#f59e0b' : '#ef4444';

  const stats = [
    {{ val: logs.length, label:'총 시공일지', color:'#6366f1' }},
    {{ val: totalWorkers + '명', label:'총 투입인원', color:'#10b981' }},
    {{ val: workedDays + '일', label:'인원 입력일', color:'#f59e0b' }},
    {{ val: avgWorkers + '명', label:'일 평균 인원', color:'#a855f7' }},
    {{ val: allTrades.size, label:'공종 수', color:'#06b6d4' }},
    {{ val: dDayText, label:'준공까지 (8/16)', color: dDayColor }},
  ];
  document.getElementById('statsRow').innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="stat-value" style="color:${{s.color}}">${{s.val}}</div>
      <div class="stat-label">${{s.label}}</div>
    </div>`).join('');
}}

// PDF 시공일지 工种(직종)에서 나온 공종만. 새 직종이 PDF에 추가되면 자동 포함.
function getPdfTrades() {{
  const s = new Set();
  WORK_LOGS.logs.forEach(l => {{
    if (l.trades && typeof l.trades === 'object' && !Array.isArray(l.trades)) {{
      Object.keys(l.trades).forEach(r => {{
        const t = tradeOf(r);
        if (!SUPPORT_TRADES.includes(t)) s.add(t);
      }});
    }}
  }});
  const ordered = TRADE_ORDER.filter(t => s.has(t));
  [...s].forEach(t => {{ if (!ordered.includes(t)) ordered.push(t); }});
  return ordered;
}}

// ===== CAT GRID (공종별 시공 현황: PDF 工种 기준, 공종별 날짜 / 누적 인원) =====
function renderCatGrid() {{
  const trades = getPdfTrades();
  const days = {{}}, heads = {{}};
  WORK_LOGS.logs.forEach(l => {{
    const w = getWorkers(l.log_date);
    trades.forEach(t => {{
      const cnt = parseInt(w[t]) || 0;
      if (cnt > 0) days[t] = (days[t] || 0) + 1;
      heads[t] = (heads[t] || 0) + cnt;
    }});
  }});
  const shown = trades
    .filter(t => (heads[t] || 0) > 0)
    .sort((a,b) => (days[b]||0) - (days[a]||0) || (heads[b]||0) - (heads[a]||0));
  document.getElementById('catGrid').innerHTML = shown.map(name => {{
    const c = TRADE_COLORS[name] || '#6366f1';
    return `<div class="cat-chip" onclick="openTradeModal('${{htmlEscape(name)}}')" title="${{htmlEscape(name)}} 날짜별 투입인원·작업내용 보기">
      <div class="cat-dot" style="background:${{c}}"></div>
      <span class="cat-name">${{name}}</span>
      <span class="cat-count" style="color:${{c}}">${{days[name]||0}}일<span class="cat-head">누적 ${{heads[name]||0}}명</span></span>
      <span class="cat-go">›</span>
    </div>`;
  }}).join('');
}}

// ===== DAILY TABLE =====
function renderDailyTable() {{
  const q = (document.getElementById('searchDaily')?.value || '').toLowerCase();
  let logs = WORK_LOGS.logs;
  if (currentFilter === 'has-workers') logs = logs.filter(l => getTotalWorkers(l.log_date) > 0);
  if (currentFilter === 'no-workers') logs = logs.filter(l => getTotalWorkers(l.log_date) === 0);
  if (q) logs = logs.filter(l =>
    l.log_date.includes(q) ||
    Object.keys(l.trade_details || {{}}).some(t => t.toLowerCase().includes(q))
  );

  document.getElementById('dailyTableBody').innerHTML = logs.map(l => {{
    const d = new Date(l.log_date + 'T00:00:00');
    const dow = d.getDay();
    const wd = WEEKDAYS[dow];
    const dayClass = dow === 0 ? ' sun' : dow === 6 ? ' sat' : '';
    const workers = getWorkers(l.log_date);
    const labor = getLaborTotal(l.log_date);
    const manager = getManagerTotal(l.log_date);

    // 공종별 인원만 표시 (관리·지원 제외, 인원 0 제외)
    const tradeTags = getConstructionTrades()
      .filter(t => (parseInt(workers[t]) || 0) > 0)
      .map(t => {{
        const c = TRADE_COLORS[t] || '#6366f1';
        return `<span class="cat-tag" style="background:${{c}}22;color:${{c}};border:1px solid ${{c}}44">${{t}} <b>${{workers[t]}}명</b></span>`;
      }}).join('');

    const laborBadge = (labor + manager) > 0
      ? `<span class="worker-total-big">${{labor + manager}}명</span>`
      : `<span style="color:var(--text-muted);font-size:0.78rem">-</span>`;
    const mgrBadge = manager > 0
      ? `<span class="manager-num">${{manager}}명</span>`
      : `<span style="color:var(--text-muted);font-size:0.78rem">-</span>`;

    return `<tr onclick="openWorkerModal('${{l.log_date}}')">
      <td class="date-cell${{dayClass}}">${{l.log_date}}<span class="weekday">(${{wd}})</span></td>
      <td><div class="cat-tags">${{tradeTags || '<span style="color:var(--text-muted);font-size:0.75rem">-</span>'}}</div></td>
      <td class="num">${{laborBadge}}</td>
      <td class="num">${{mgrBadge}}</td>
      <td><button class="worker-badge${{(labor+manager) === 0 ? ' empty' : ''}}" onclick="event.stopPropagation();openWorkerModal('${{l.log_date}}')">
        ✏️ 입력
      </button></td>
    </tr>`;
  }}).join('');
}}

function setDailyFilter(f, btn) {{
  currentFilter = f;
  document.querySelectorAll('[data-f]').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderDailyTable();
}}

// 작업내용 문자열 정리 (제어문자·널바이트 제거, 공백 정리)
function cleanWork(s) {{
  return String(s == null ? '' : s).replace(/[\\u0000-\\u001f]/g, ' ').replace(/\\s+/g, ' ').trim();
}}
// 기간 내 로그들의 작업내용을 공종별로 묶어 중복 제거
function buildWorkSummary(logs) {{
  const byTrade = {{}}; const locs = new Set();
  logs.forEach(l => {{
    (l.locations || []).forEach(x => {{ const c = cleanWork(x); if (c) locs.add(c); }});
    const twd = l.trade_work_details || {{}};
    Object.entries(twd).forEach(([role, v]) => {{
      if (!v) return;
      const w = cleanWork(v.work || v.work_cn);
      if (!w) return;
      const t = tradeOf(role);
      (byTrade[t] = byTrade[t] || new Set()).add(w);
    }});
  }});
  return {{ byTrade, locs: [...locs] }};
}}

// ===== WEEKLY =====
function renderWeekly() {{
  const weeks = {{}};
  WORK_LOGS.logs.forEach(l => {{
    const d = new Date(l.log_date);
    const mon = new Date(d); mon.setDate(d.getDate() - ((d.getDay()+6)%7));
    const wk = mon.toISOString().slice(0,10);
    if (!weeks[wk]) weeks[wk] = [];
    weeks[wk].push(l);
  }});

  let html = '';
  Object.keys(weeks).sort().forEach(wkStart => {{
    const wkEnd = new Date(wkStart); wkEnd.setDate(wkEnd.getDate()+6);
    const wkEndStr = wkEnd.toISOString().slice(0,10);
    const logs = weeks[wkStart];
    const tradeTotals = {{}};
    let grandTotal = 0;

    logs.forEach(l => {{
      const workers = getWorkers(l.log_date);
      Object.entries(workers).forEach(([t, cnt]) => {{
        tradeTotals[t] = (tradeTotals[t] || 0) + (parseInt(cnt) || 0);
        grandTotal += (parseInt(cnt) || 0);
      }});
    }});

    const activeTrades = Object.keys(tradeTotals).filter(t => tradeTotals[t] > 0).sort((a,b) => tradeTotals[b] - tradeTotals[a]);
    const maxVal = Math.max(...Object.values(tradeTotals), 1);

    const sum = buildWorkSummary(logs);
    const sumTrades = getAllTrades().filter(t => sum.byTrade[t]);
    const summaryHtml = sumTrades.length ? `
      <div class="week-summary">
        <div class="week-summary-title">📋 주간 작업 내용 요약</div>
        ${{sumTrades.map(t => `<div class="ws-row">
          <span class="ws-dot" style="background:${{TRADE_COLORS[t]||'#6366f1'}}"></span>
          <span class="ws-trade">${{t}}</span>
          <span class="ws-work">${{[...sum.byTrade[t]].map(htmlEscape).join(' · ')}}</span>
        </div>`).join('')}}
        ${{sum.locs.length ? `<div class="ws-loc">📍 작업 위치 ${{sum.locs.map(x => `<span class="loc-chip">${{htmlEscape(x)}}</span>`).join('')}}</div>` : ''}}
      </div>` : '';

    html += `<div class="period-group">
      <div class="period-header">
        <div class="period-label">
          <span style="color:var(--accent)">📅</span>
          ${{wkStart}} ~ ${{wkEndStr}}
          <span style="color:var(--text-muted);font-size:0.75rem;font-weight:400">(${{logs.length}}일)</span>
        </div>
        <div class="period-total">
          ${{grandTotal}}<span style="font-size:0.9rem">명</span>
          <small>주 총인원</small>
        </div>
      </div>
      <div class="bar-chart">
        ${{activeTrades.length === 0 ? '<p style="color:var(--text-muted);font-size:0.82rem;text-align:center;padding:12px">인원 데이터 없음 — 일별 탭에서 입력하세요</p>' :
          activeTrades.map(t => `
          <div class="bar-row">
            <div class="bar-label" title="${{t}}">${{t}}</div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${{(tradeTotals[t]/maxVal*100).toFixed(1)}}%;background:${{TRADE_COLORS[t]||'#6366f1'}}"></div>
            </div>
            <div class="bar-val">${{tradeTotals[t]}}</div>
          </div>`).join('')
        }}
        ${{grandTotal > 0 ? `<div style="margin-top:12px;padding-top:10px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
          <span style="font-size:0.78rem;color:var(--text-muted)">주 합계</span>
          <span style="font-size:1.1rem;font-weight:800;color:var(--accent)">${{grandTotal}}명</span>
        </div>` : ''}}
        ${{summaryHtml}}
      </div>
    </div>`;
  }});
  document.getElementById('weeklyContent').innerHTML = html || '<p style="color:var(--text-muted);padding:20px">데이터가 없습니다.</p>';
}}

// ===== MONTHLY =====
function renderMonthly() {{
  const months = {{}};
  WORK_LOGS.logs.forEach(l => {{
    const mo = l.log_date.slice(0,7);
    if (!months[mo]) months[mo] = [];
    months[mo].push(l);
  }});

  let html = '';
  Object.keys(months).sort().forEach(mo => {{
    const logs = months[mo];
    const tradeTotals = {{}};
    let grandTotal = 0;

    logs.forEach(l => {{
      const workers = getWorkers(l.log_date);
      Object.entries(workers).forEach(([t, cnt]) => {{
        tradeTotals[t] = (tradeTotals[t] || 0) + (parseInt(cnt) || 0);
        grandTotal += (parseInt(cnt) || 0);
      }});
    }});

    const activeTrades = Object.keys(tradeTotals).filter(t => tradeTotals[t] > 0).sort((a,b) => tradeTotals[b] - tradeTotals[a]);
    const maxVal = Math.max(...Object.values(tradeTotals), 1);
    const [yr, mm] = mo.split('-');
    const moLabel = `${{yr}}년 ${{parseInt(mm)}}월`;

    // Build full table for monthly
    const tableRows = activeTrades.map(t => {{
      const dayBreakdown = logs.map(l => {{
        const w = getWorkers(l.log_date);
        return {{ date: l.log_date, cnt: parseInt(w[t]) || 0 }};
      }}).filter(x => x.cnt > 0);
      if (dayBreakdown.length === 0 && (tradeTotals[t] || 0) === 0) return '';
      return `<tr>
        <td><div class="trade-name-cell">
          <span class="trade-dot" style="background:${{TRADE_COLORS[t]||'#6366f1'}}"></span>${{t}}
        </div></td>
        <td class="num" style="color:${{TRADE_COLORS[t]||'#6366f1'}};font-weight:800">${{tradeTotals[t] || 0}}</td>
        <td style="font-size:0.75rem;color:var(--text-muted)">
          ${{dayBreakdown.map(x => `${{x.date.slice(5)}}(${{x.cnt}})`).join(', ') || '-'}}
        </td>
      </tr>`;
    }}).join('');

    html += `<div class="period-group">
      <div class="period-header">
        <div class="period-label">
          <span style="color:var(--accent)">🗓️</span> ${{moLabel}}
          <span style="color:var(--text-muted);font-size:0.75rem;font-weight:400">(${{logs.length}}일치)</span>
        </div>
        <div class="period-total">
          ${{grandTotal}}<span style="font-size:0.9rem">명</span>
          <small>월 총인원</small>
        </div>
      </div>
      <div class="bar-chart">
        ${{activeTrades.length === 0 ? '<p style="color:var(--text-muted);font-size:0.82rem;text-align:center;padding:12px">인원 데이터 없음 — 일별 탭에서 입력하세요</p>' : `
          <div class="worker-table-wrap" style="margin-bottom:16px">
            <table class="worker-table">
              <thead><tr>
                <th>공종</th>
                <th class="num">월 합계</th>
                <th>일별 투입 내역</th>
              </tr></thead>
              <tbody>${{tableRows}}</tbody>
              <tfoot><tr class="subtotal">
                <td><b>합 계</b></td>
                <td class="total-cell">${{grandTotal}}</td>
                <td style="font-size:0.75rem;color:var(--text-muted)">${{logs.filter(l => getTotalWorkers(l.log_date) > 0).length}}일 투입</td>
              </tr></tfoot>
            </table>
          </div>
          ${{activeTrades.map(t => `
          <div class="bar-row">
            <div class="bar-label" title="${{t}}">${{t}}</div>
            <div class="bar-track">
              <div class="bar-fill" style="width:${{(tradeTotals[t]/maxVal*100).toFixed(1)}}%;background:${{TRADE_COLORS[t]||'#6366f1'}}"></div>
            </div>
            <div class="bar-val">${{tradeTotals[t]}}</div>
          </div>`).join('')}}`
        }}
      </div>
    </div>`;
  }});
  document.getElementById('monthlyContent').innerHTML = html || '<p style="color:var(--text-muted);padding:20px">데이터가 없습니다.</p>';
}}

// 데이터에 등장하는 모든 공종을 정해진 순서대로 반환 (새 공종은 뒤에 자동 추가)
function getAllTrades() {{
  const s = new Set(TRADE_ORDER);
  WORK_LOGS.logs.forEach(l => {{
    Object.keys(l.trade_details || {{}}).forEach(t => s.add(tradeOf(t)));
    if (l.trades && typeof l.trades === 'object' && !Array.isArray(l.trades)) {{
      Object.keys(l.trades).forEach(t => s.add(tradeOf(t)));
    }}
  }});
  const ordered = TRADE_ORDER.filter(t => s.has(t));
  [...s].forEach(t => {{ if (!ordered.includes(t)) ordered.push(t); }});
  return ordered;
}}
// 공종만 (관리·지원 인력 제외)
function getConstructionTrades() {{
  return getAllTrades().filter(t => !SUPPORT_TRADES.includes(t));
}}

// ===== TAB SWITCH =====
function switchTab(tab) {{
  ['daily','weekly','monthly'].forEach(t => {{
    document.getElementById(`tab-${{t}}`).classList.toggle('active', t === tab);
    document.getElementById(`panel-${{t}}`).classList.toggle('active', t === tab);
  }});
  if (tab === 'weekly') renderWeekly();
  if (tab === 'monthly') renderMonthly();
}}

// ===== WORKER INPUT MODAL =====
function htmlEscape(s) {{
  return String(s == null ? '' : s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}}

function openWorkerModal(logDate) {{
  const log = WORK_LOGS.logs.find(l => l.log_date === logDate);
  if (!log) return;
  const d = new Date(logDate + 'T00:00:00');
  const wd = WEEKDAYS[d.getDay()];
  const workers = getWorkers(logDate);
  const allTrades = getAllTrades();
  const chatCats = new Set(Object.keys(log.trade_details || {{}}).map(tradeOf));

  // 공종 입력칸 (공종 → 관리·지원 순, 사이에 구분 라벨)
  let supportStarted = false;
  const inputRows = allTrades.map((t, i) => {{
    let pre = '';
    if (!supportStarted && SUPPORT_TRADES.includes(t)) {{
      supportStarted = true;
      pre = `<div class="wi-group-label">관리·지원 인력</div>`;
    }}
    const isActive = (parseInt(workers[t]) || 0) > 0 || chatCats.has(t);
    const color = TRADE_COLORS[t] || '#6366f1';
    return `${{pre}}<div class="worker-input-row" style="${{!isActive ? 'opacity:0.45' : ''}}">
      <span class="trade-dot" style="background:${{color}}"></span>
      <span class="worker-input-label">${{t}}</span>
      <input type="number" min="0" max="999" class="wi-number" id="wi_${{i}}" data-trade="${{htmlEscape(t)}}"
        value="${{parseInt(workers[t]) || 0}}" oninput="updateModalTotal()" placeholder="0">
    </div>`;
  }});

  const total = getTotalWorkers(logDate);
  const labor = getLaborTotal(logDate);
  const manager = getManagerTotal(logDate);

  // 그날 작업 사항 (직종별 작업내용 → 없으면 work_contents)
  const twd = log.trade_work_details || {{}};
  let workRows = Object.entries(twd)
    .filter(([k,v]) => v && (v.work || v.work_cn))
    .map(([k,v]) => {{
      const t = tradeOf(k);
      const color = TRADE_COLORS[t] || '#6366f1';
      return `<div class="work-item"><span class="trade-dot" style="background:${{color}}"></span><b>${{htmlEscape(t)}}</b> ${{htmlEscape(v.work || v.work_cn)}}</div>`;
    }}).join('');
  if (!workRows) {{
    workRows = (log.work_contents || []).filter(Boolean)
      .map(w => `<div class="work-item">• ${{htmlEscape(w)}}</div>`).join('');
  }}
  const locs = (log.locations || []).filter(Boolean);
  const locHtml = locs.length ? `<div class="loc-row">📍 ${{locs.map(x => `<span class="loc-chip">${{htmlEscape(x)}}</span>`).join('')}}</div>` : '';

  // 이슈 / 주요 대화
  const issues = (log.day_highlights_kr || log.day_highlights || []).slice(0,5);

  document.getElementById('modal').innerHTML = `
    <div class="modal-header">
      <div>
        <div class="modal-title">👷 작업 인원 입력</div>
        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:4px">
          ${{logDate}} (${{wd}})
          ${{log.pdf_file ? ` · <span class="pdf-link" onclick="togglePdf('${{encodeURIComponent(log.pdf_file)}}')">📄 ${{htmlEscape(log.file_name || log.pdf_file)}} (미리보기)</span>` : (log.file_name ? ` — ${{htmlEscape(log.file_name)}}` : '')}}
        </div>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>

    <div class="pdf-preview" id="pdfPreview" style="display:none"></div>

    <div class="modal-section">
      <div class="modal-section-title">공종별 투입 인원 (명)</div>
      <div class="worker-input-grid">${{inputRows.join('')}}</div>
      <div class="total-row">
        <span class="label">📊 당일 총 투입 인원</span>
        <span class="value" id="modalTotal">${{total}}명</span>
      </div>
      <div class="split-row">
        <span class="split-badge labor">작업자 <b id="modalLabor">${{labor}}</b>명</span>
        <span class="split-badge mgr">관리자 <b id="modalManager">${{manager}}</b>명</span>
      </div>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">📋 당일 작업 사항</div>
      ${{workRows || '<div class="work-item" style="color:var(--text-muted)">기록 없음</div>'}}
      ${{locHtml}}
    </div>

    ${{issues.length > 0 ? `<div class="modal-section">
      <div class="modal-section-title">⚠️ 이슈 / 주요 대화</div>
      ${{issues.map(h => `<div class="modal-highlight">${{htmlEscape(h).slice(0,160)}}</div>`).join('')}}
    </div>` : ''}}

    <div class="modal-footer">
      <button class="modal-btn modal-btn-cancel" onclick="closeModal()">취소</button>
      <button class="modal-btn modal-btn-primary" onclick="saveWorkerModal('${{logDate}}')">💾 저장</button>
    </div>`;

  document.getElementById('modalOverlay').classList.add('active');
}}

function togglePdf(pdfEnc) {{
  const box = document.getElementById('pdfPreview');
  if (!box) return;
  if (box.style.display === 'none' || !box.innerHTML) {{
    if (!IS_LOCAL) {{
      // 온라인(GitHub Pages)에는 PDF 원본을 올리지 않음
      box.innerHTML = `<div style="padding:18px;font-size:0.85rem;color:var(--text-secondary)">📄 PDF 원본 미리보기는 맥(로컬 대시보드)에서만 제공됩니다. 작업 내용은 위 표에서 확인하세요.</div>`;
      box.style.display = 'block';
      return;
    }}
    const url = '일일작업일보/' + pdfEnc;  // pdf_file은 encodeURIComponent 처리됨
    box.innerHTML = `<iframe src="${{url}}" class="pdf-frame"></iframe>
      <div class="pdf-bar"><a href="${{url}}" target="_blank" rel="noopener">↗ 새 탭에서 열기</a></div>`;
    box.style.display = 'block';
  }} else {{
    box.style.display = 'none';
    box.innerHTML = '';
  }}
}}

function updateModalTotal() {{
  let total = 0, manager = 0;
  document.querySelectorAll('.wi-number').forEach(inp => {{
    const v = parseInt(inp.value) || 0;
    total += v;
    if (MANAGER_TRADES.includes(inp.dataset.trade)) manager += v;
  }});
  document.getElementById('modalTotal').textContent = total + '명';
  const lb = document.getElementById('modalLabor'); if (lb) lb.textContent = (total - manager);
  const mg = document.getElementById('modalManager'); if (mg) mg.textContent = manager;
}}

function saveWorkerModal(logDate) {{
  const workers = {{}};
  document.querySelectorAll('.wi-number').forEach(inp => {{
    const v = parseInt(inp.value) || 0;
    if (v > 0) workers[inp.dataset.trade] = v;
  }});
  setWorkers(logDate, workers);
  closeModal();
  renderDailyTable();
  renderStats();
  renderCatGrid();
  showToast('✅ 인원 저장 완료!');
}}

// ===== 공종별 날짜 투입인원 + 작업내용 그래프 모달 =====
function openTradeModal(trade) {{
  const color = TRADE_COLORS[trade] || '#6366f1';
  // 해당 공종 인원이 있는 날짜만 수집 (날짜순)
  const rows = [];
  WORK_LOGS.logs.forEach(l => {{
    const cnt = parseInt(getWorkers(l.log_date)[trade]) || 0;
    if (cnt <= 0) return;
    // 그 날짜 해당 공종 작업내용
    const works = new Set();
    Object.entries(l.trade_work_details || {{}}).forEach(([role, v]) => {{
      if (v && tradeOf(role) === trade) {{
        const w = cleanWork(v.work || v.work_cn);
        if (w) works.add(w);
      }}
    }});
    rows.push({{ date: l.log_date, cnt, works: [...works] }});
  }});
  rows.sort((a,b) => a.date.localeCompare(b.date));

  const totalHead = rows.reduce((s,r) => s + r.cnt, 0);
  const maxVal = 40;  // 인원수 기준 고정 최대값 (막대 길이 = 인원 / 40)
  const avg = rows.length ? (totalHead / rows.length) : 0;

  const chartRows = rows.map(r => {{
    const d = new Date(r.date + 'T00:00:00');
    const wd = WEEKDAYS[d.getDay()];
    const pct = Math.round(r.cnt / maxVal * 100);
    const worksHtml = r.works.length
      ? `<div class="td-works">${{r.works.map(w => `<span class="td-work">${{htmlEscape(w)}}</span>`).join('')}}</div>`
      : '';
    return `<div class="td-row" onclick="closeModal();openWorkerModal('${{r.date}}')" title="${{r.date}} 상세 보기">
      <div class="td-bar-line">
        <span class="td-date">${{r.date.slice(5)}} <small>(${{wd}})</small></span>
        <div class="bar-track"><div class="bar-fill" style="width:${{pct}}%;background:${{color}}"></div></div>
        <span class="td-cnt" style="color:${{color}}">${{r.cnt}}명</span>
      </div>
      ${{worksHtml}}
    </div>`;
  }}).join('');

  document.getElementById('modal').innerHTML = `
    <div class="modal-header">
      <div>
        <div class="modal-title"><span class="cat-dot" style="display:inline-block;background:${{color}}"></span> ${{htmlEscape(trade)}} · 날짜별 투입 현황</div>
        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:4px">
          투입 ${{rows.length}}일 · 누적 ${{totalHead}}명 · 일 평균 ${{avg.toFixed(1)}}명
        </div>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-section">
      ${{rows.length ? `<div class="bar-chart td-chart">${{chartRows}}</div>`
        : '<div class="work-item" style="color:var(--text-muted)">투입 기록이 없습니다.</div>'}}
    </div>
    <div class="modal-footer">
      <button class="modal-btn modal-btn-cancel" onclick="closeModal()">닫기</button>
    </div>`;
  document.getElementById('modalOverlay').classList.add('active');
}}

function closeModal() {{
  document.getElementById('modalOverlay').classList.remove('active');
}}

document.getElementById('modalOverlay').addEventListener('click', function(e) {{
  if (e.target === this) closeModal();
}});

// ===== CALENDAR =====
function renderCalendar() {{
  const logDates = new Set(WORK_LOGS.logs.map(l => l.log_date));
  const months = {{}};
  WORK_LOGS.logs.forEach(l => {{
    const mo = l.log_date.slice(0,7);
    if (!months[mo]) months[mo] = [];
    months[mo].push(l.log_date);
  }});

  let html = '';
  Object.keys(months).sort().forEach(mo => {{
    const [yr, mm] = mo.split('-').map(Number);
    const daysInMonth = new Date(yr, mm, 0).getDate();
    const firstDay = new Date(yr, mm-1, 1).getDay();
    const moLabel = `${{yr}}년 ${{mm}}월`;

    let cells = Array(firstDay).fill('<div class="day-cell empty"></div>');
    for (let d = 1; d <= daysInMonth; d++) {{
      const ds = `${{yr}}-${{String(mm).padStart(2,'0')}}-${{String(d).padStart(2,'0')}}`;
      const inLog = logDates.has(ds);
      const note = NO_LOG_DAYS[ds];
      const dow = new Date(yr, mm-1, d).getDay();
      const workers = inLog ? getTotalWorkers(ds) : 0;
      const cls = inLog ? 'has-log' : (note ? 'note' : '');
      const tooltip = inLog ? `${{ds}}${{workers > 0 ? ` (${{workers}}명)` : ''}}` : (note ? `${{ds}} · ${{note}}` : ds);
      cells.push(`<div class="day-cell ${{cls}}" title="${{tooltip}}" onclick="${{inLog ? `openWorkerModal('${{ds}}')` : ''}}">
        ${{d}}${{workers > 0 ? `<sup style="font-size:0.5rem;color:var(--green)">●</sup>` : (note ? `<sup style="font-size:0.5rem;color:var(--orange)">◆</sup>` : '')}}
      </div>`);
    }}
    html += `<div class="month-group">
      <div class="month-label">📅 ${{moLabel}} <span style="font-size:0.75rem;color:var(--text-muted)">(${{months[mo].length}}일)</span></div>
      <div class="day-grid">${{cells.join('')}}</div>
    </div>`;
  }});
  document.getElementById('calendarSection').innerHTML = html;
}}

// ===== MISSING =====
function renderMissing() {{
  const logDates = new Set(WORK_LOGS.logs.map(l => l.log_date));
  if (WORK_LOGS.logs.length < 2) {{ document.getElementById('missingSection').innerHTML = ''; return; }}
  const first = WORK_LOGS.logs[0].log_date;
  const last = WORK_LOGS.logs[WORK_LOGS.logs.length-1].log_date;
  const missing = [];
  const d = new Date(first);
  const end = new Date(last);
  while (d <= end) {{
    const ds = d.toISOString().slice(0,10);
    const dow = d.getDay();
    if (dow !== 0 && dow !== 6 && !logDates.has(ds) && !NO_LOG_DAYS[ds]) missing.push(ds);
    d.setDate(d.getDate()+1);
  }}
  if (missing.length === 0) {{ document.getElementById('missingSection').innerHTML = ''; return; }}
  document.getElementById('missingSection').innerHTML = `
    <div class="missing-title">⚠️ 미제출 평일 (${{missing.length}}일)</div>
    <div class="missing-list">${{missing.slice(0,30).map(d => `<span class="missing-day">${{d}}</span>`).join('')}}${{missing.length > 30 ? `<span class="missing-day">+${{missing.length-30}}일</span>` : ''}}</div>`;
}}

// ===== SAVE / EXPORT =====

// ===== 수동 업데이트 (로컬 서버 필요) =====
async function runUpdate() {{
  const btn = document.getElementById('btnUpdate');
  if (btn.classList.contains('loading')) return;
  const orig = btn.innerHTML;
  btn.classList.add('loading');
  btn.innerHTML = '업데이트 중… (최대 1~2분)';
  try {{
    const res = await fetch('/api/update', {{ method:'POST' }});
    if (!res.ok) throw new Error('server');
    const data = await res.json();
    if (data.ok) {{
      const parts = [];
      if (data.work_logs) parts.push(`시공일지 +${{data.work_logs}}`);
      if (data.events) parts.push(`이벤트 +${{data.events}}`);
      showToast('✅ 업데이트 완료! ' + (parts.length ? parts.join(', ') : '새 항목 없음') + ' · 새로고침합니다');
      setTimeout(() => location.reload(), 1600);
    }} else {{
      showToast('⚠️ 업데이트 실패: ' + (data.error || '알 수 없음'));
      btn.classList.remove('loading'); btn.innerHTML = orig;
    }}
  }} catch (e) {{
    alert('수동 업데이트 버튼은 로컬 서버에서만 동작합니다.\\n\\n프로젝트 폴더의 "대시보드_시작.command" 파일을 더블클릭해 실행한 뒤,\\n자동으로 열리는 페이지에서 다시 눌러주세요.\\n\\n(또는 터미널에서:  python3 daily_update.py )');
    btn.classList.remove('loading'); btn.innerHTML = orig;
  }}
}}

// ===== 스타일 적용 엑셀(.xlsx) 내보내기 =====
function exportExcel() {{
  if (typeof XLSX === 'undefined') {{ showToast('⏳ 엑셀 라이브러리 로딩 중… 잠시 후 다시 시도하세요'); return; }}
  const today = new Date().toISOString().slice(0,10);
  const FONT = '맑은 고딕';
  const WD = ['일','월','화','수','목','금','토'];
  const trades = getAllTrades();
  const logs = [...WORK_LOGS.logs].sort((a,b) => a.log_date.localeCompare(b.log_date));

  // 공통: 제목/메타/헤더/데이터 행에 스타일 입힌 시트 생성
  function styleSheet(title, meta, headers, rows, opts) {{
    opts = opts || {{}};
    const blank = Array(headers.length-1).fill('');
    const aoa = [ [title, ...blank], [meta, ...blank], headers, ...rows ];
    const ws = XLSX.utils.aoa_to_sheet(aoa);
    const HROW = 2;
    ws['!merges'] = [
      {{s:{{r:0,c:0}}, e:{{r:0,c:headers.length-1}}}},
      {{s:{{r:1,c:0}}, e:{{r:1,c:headers.length-1}}}},
    ];
    ws['!rows'] = [{{hpt:30}},{{hpt:20}},{{hpt:24}}];
    const bd = {{ style:'thin', color:{{rgb:'D9D9D9'}} }};
    const BORDER = {{ top:bd, bottom:bd, left:bd, right:bd }};
    const range = XLSX.utils.decode_range(ws['!ref']);
    for (let R=range.s.r; R<=range.e.r; R++) {{
      for (let C=range.s.c; C<=range.e.c; C++) {{
        const addr = XLSX.utils.encode_cell({{r:R,c:C}});
        const cell = ws[addr] || (ws[addr] = {{t:'s', v:''}});
        if (R === 0) {{
          cell.s = {{ font:{{name:FONT, sz:16, bold:true, color:{{rgb:'FFFFFF'}}}},
                     fill:{{patternType:'solid', fgColor:{{rgb:'1A1A1A'}}}},
                     alignment:{{horizontal:'left', vertical:'center'}} }};
        }} else if (R === 1) {{
          cell.s = {{ font:{{name:FONT, sz:10, color:{{rgb:'888888'}}}},
                     fill:{{patternType:'solid', fgColor:{{rgb:'F2F2F2'}}}},
                     alignment:{{horizontal:'left', vertical:'center'}} }};
        }} else if (R === HROW) {{
          cell.s = {{ font:{{name:FONT, sz:11, bold:true, color:{{rgb:'FFFFFF'}}}},
                     fill:{{patternType:'solid', fgColor:{{rgb:'333333'}}}},
                     alignment:{{horizontal:'center', vertical:'center', wrapText:true}},
                     border:BORDER }};
        }} else {{
          const isTotal = opts.totalRow && R === range.e.r;
          const zebra = ((R-HROW) % 2 === 0) ? 'FFFFFF' : 'F7F7F7';
          cell.s = {{ font:{{name:FONT, sz:10, bold:(C===2 || isTotal), color:{{rgb: isTotal?'FFFFFF':'222222'}}}},
                     fill:{{patternType:'solid', fgColor:{{rgb: isTotal?'555555':zebra}}}},
                     alignment:{{horizontal:'center', vertical:'center'}},
                     border:BORDER }};
        }}
      }}
    }}
    ws['!autofilter'] = {{ ref: XLSX.utils.encode_range({{s:{{r:HROW,c:0}}, e:{{r:range.e.r,c:headers.length-1}}}}) }};
    return ws;
  }}

  // ── 일별 시트 ──
  const H = ['날짜','요일','총 인원', ...trades];
  const dailyRows = logs.map(l => {{
    const w = getWorkers(l.log_date);
    return [ l.log_date, WD[new Date(l.log_date+'T00:00:00').getDay()], getTotalWorkers(l.log_date),
             ...trades.map(t => parseInt(w[t])||0) ];
  }});
  const totalRow = ['합계','', dailyRows.reduce((a,r)=>a+r[2],0),
                    ...trades.map((t,i)=> dailyRows.reduce((a,r)=>a+r[3+i],0))];
  const wsDaily = styleSheet('하이디라오 영등포점 · 일별 인원집계',
    `내보낸 날짜 ${{today}}   ·   총 ${{logs.length}}일   ·   기간 ${{WORK_LOGS.period||''}}`,
    H, [...dailyRows, totalRow], {{totalRow:true}});
  wsDaily['!cols'] = H.map((h,i)=> i===0?{{wch:13}} : i===1?{{wch:6}} : i===2?{{wch:9}} : {{wch:11}});

  // ── 주별 시트 ──
  const weeks = {{}};
  logs.forEach(l => {{
    const d = new Date(l.log_date+'T00:00:00');
    const mon = new Date(d); mon.setDate(d.getDate() - ((d.getDay()+6)%7));
    const wk = mon.toISOString().slice(0,10);
    (weeks[wk] = weeks[wk] || []).push(l);
  }});
  const WH = ['주간','일수','총 인원', ...trades];
  const weekRows = Object.keys(weeks).sort().map(wk => {{
    const wkEnd = new Date(wk+'T00:00:00'); wkEnd.setDate(wkEnd.getDate()+6);
    const tt = {{}}; let gt = 0;
    weeks[wk].forEach(l => {{ const w = getWorkers(l.log_date);
      trades.forEach(t => {{ const v = parseInt(w[t])||0; tt[t]=(tt[t]||0)+v; gt+=v; }}); }});
    return [ `${{wk}} ~ ${{wkEnd.toISOString().slice(0,10)}}`, weeks[wk].length, gt, ...trades.map(t=>tt[t]||0) ];
  }});
  const wsWeek = styleSheet('하이디라오 영등포점 · 주별 인원집계',
    `내보낸 날짜 ${{today}}   ·   총 ${{weekRows.length}}주`, WH, weekRows, {{}});
  wsWeek['!cols'] = WH.map((h,i)=> i===0?{{wch:26}} : i===1?{{wch:7}} : i===2?{{wch:9}} : {{wch:11}});

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, wsDaily, '일별');
  XLSX.utils.book_append_sheet(wb, wsWeek, '주별');
  XLSX.writeFile(wb, `하이디라오_인원집계_${{today}}.xlsx`);
  showToast('📊 엑셀 보고서가 다운로드됩니다');
}}

function showToast(msg) {{
  const t = document.getElementById('toastWL');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}}

// ===== START =====
init();
</script>
</body>
</html>"""

with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"✅ 완료! {len(HTML):,} bytes → {HTML_FILE}")
