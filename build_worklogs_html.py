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

data_json = json.dumps(data, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>하이디라오 영등포점 — 시공 작업일지</title>
<meta name="description" content="하이디라오 영등포점 공사 프로젝트 시공일지 대시보드. 공종별 인원 집계, 주별/월별 분석.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-primary: #06080f;
  --bg-secondary: #0e1320;
  --bg-card: rgba(17,24,48,0.65);
  --bg-card-hover: rgba(25,35,60,0.75);
  --bg-glass: rgba(255,255,255,0.03);
  --border: rgba(255,255,255,0.06);
  --border-active: rgba(255,255,255,0.18);
  --border-glow: rgba(99,102,241,0.35);
  --text-primary: #edf0f7;
  --text-secondary: #8b95a8;
  --text-muted: #4d5669;
  --accent: #818cf8;
  --accent-deep: #6366f1;
  --accent-glow: rgba(129,140,248,0.18);
  --green: #34d399;
  --yellow: #fbbf24;
  --red: #f87171;
  --blue: #60a5fa;
  --purple: #c084fc;
  --cyan: #22d3ee;
  --pink: #f472b6;
  --orange: #fb923c;
  --shadow-md: 0 8px 32px rgba(0,0,0,0.45);
  --shadow-glow: 0 0 40px rgba(99,102,241,0.08);
  --radius: 16px;
  --radius-sm: 10px;
}}
*{{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family:'Inter','Noto Sans KR',sans-serif;
  background:var(--bg-primary); color:var(--text-primary);
  min-height:100vh; line-height:1.6;
  background-image:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.10), transparent),
    radial-gradient(ellipse 60% 40% at 80% 100%, rgba(168,85,247,0.06), transparent);
  background-attachment:fixed;
}}
.container {{ max-width:1440px; margin:0 auto; padding:36px 28px; }}

/* ── ANIMATIONS ── */
@keyframes fadeInUp {{ from{{opacity:0;transform:translateY(18px)}} to{{opacity:1;transform:translateY(0)}} }}
@keyframes shimmer {{ 0%{{background-position:-200% 0}} 100%{{background-position:200% 0}} }}
@keyframes pulseGlow {{ 0%,100%{{opacity:0.5}} 50%{{opacity:1}} }}
.fade-in {{ animation:fadeInUp 0.45s ease both; }}

/* ── HEADER ── */
.header {{
  text-align:center; margin-bottom:44px; padding:36px 0 32px;
  border-bottom:1px solid var(--border);
  position:relative;
}}
.header::before {{
  content:''; position:absolute; bottom:-1px; left:20%; right:20%; height:1px;
  background:linear-gradient(90deg, transparent, var(--accent-deep), transparent);
}}
.header h1 {{
  font-size:2.2rem; font-weight:800; letter-spacing:-0.5px;
  background:linear-gradient(135deg,#818cf8 0%,#c084fc 40%,#f472b6 80%,#fb923c 100%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
  margin-bottom:10px; filter:drop-shadow(0 2px 8px rgba(99,102,241,0.25));
}}
.header p {{ color:var(--text-secondary); font-size:0.88rem; letter-spacing:0.3px; }}
.header .badge {{
  display:inline-flex; align-items:center; gap:6px;
  padding:5px 16px; margin-top:10px;
  background:var(--accent-glow); border:1px solid var(--border-glow);
  border-radius:24px; font-size:0.78rem; color:var(--accent);
  backdrop-filter:blur(8px);
}}
.action-bar {{ display:flex; gap:10px; justify-content:center; margin-top:18px; flex-wrap:wrap; }}
.action-btn {{
  padding:10px 22px; border-radius:10px; font-size:0.82rem; font-weight:600;
  border:none; cursor:pointer; transition:all 0.25s; display:flex; align-items:center; gap:7px;
  box-shadow:0 2px 12px rgba(0,0,0,0.25);
}}
.action-btn:hover {{ filter:brightness(1.15); transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,0,0,0.35); }}
.btn-save {{ background:linear-gradient(135deg,#34d399,#10b981); color:#064e3b; font-weight:700; }}
.btn-excel {{ background:linear-gradient(135deg,#10b981,#059669); color:white; }}
.btn-json {{ background:var(--bg-glass); color:var(--text-secondary); border:1px solid var(--border); backdrop-filter:blur(8px); }}

/* ── STATS ── */
.stats-row {{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(175px,1fr));
  gap:16px; margin-bottom:36px;
}}
.stat-card {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); padding:22px 20px; text-align:center;
  transition:all 0.3s ease; position:relative; overflow:hidden;
  backdrop-filter:blur(12px);
}}
.stat-card::before {{
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg, transparent 20%, var(--stat-accent, var(--accent)) 50%, transparent 80%);
  opacity:0; transition:opacity 0.3s;
}}
.stat-card:hover {{
  transform:translateY(-4px); border-color:var(--border-active);
  box-shadow:var(--shadow-glow);
}}
.stat-card:hover::before {{ opacity:1; }}
.stat-value {{ font-size:2.1rem; font-weight:800; margin-bottom:6px; letter-spacing:-0.5px; }}
.stat-label {{ font-size:0.72rem; color:var(--text-secondary); text-transform:uppercase; letter-spacing:0.8px; font-weight:500; }}

/* ── SECTION TITLE ── */
.section-title {{
  font-size:1.15rem; font-weight:700; margin-bottom:18px;
  display:flex; align-items:center; gap:10px;
  color:var(--text-primary);
}}
.section-title .icon {{ font-size:1.25rem; }}
.section-title::after {{
  content:''; flex:1; height:1px;
  background:linear-gradient(90deg, var(--border), transparent);
  margin-left:8px;
}}

/* ── TABS ── */
.tab-bar {{
  display:flex; gap:4px; margin-bottom:26px;
  background:var(--bg-secondary); border-radius:var(--radius);
  padding:5px; width:fit-content;
  border:1px solid var(--border);
}}
.tab-btn {{
  padding:9px 24px; border-radius:var(--radius-sm); border:none; cursor:pointer;
  font-size:0.82rem; font-weight:600; color:var(--text-muted);
  background:transparent; transition:all 0.25s;
}}
.tab-btn.active {{
  background:linear-gradient(135deg, var(--accent-deep), #7c3aed);
  color:white; box-shadow:0 4px 14px rgba(99,102,241,0.35);
}}
.tab-btn:hover:not(.active) {{ color:var(--text-primary); background:rgba(255,255,255,0.04); }}
.tab-panel {{ display:none; }}
.tab-panel.active {{ display:block; animation:fadeInUp 0.3s ease; }}

/* ── WORKER SUMMARY TABLE ── */
.worker-table-wrap {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden; margin-bottom:32px;
  backdrop-filter:blur(12px);
}}
.worker-table {{ width:100%; border-collapse:collapse; }}
.worker-table thead th {{
  padding:13px 14px; text-align:left; font-size:0.72rem; font-weight:600;
  color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;
  background:rgba(14,19,32,0.8); border-bottom:1px solid var(--border);
  white-space:nowrap;
}}
.worker-table thead th.num {{ text-align:center; }}
.worker-table tbody tr {{
  border-bottom:1px solid var(--border); transition:all 0.2s;
}}
.worker-table tbody tr:hover {{ background:var(--bg-card-hover); }}
.worker-table tbody tr:last-child {{ border-bottom:none; }}
.worker-table td {{ padding:11px 14px; font-size:0.82rem; vertical-align:middle; }}
.worker-table td.num {{ text-align:center; font-weight:600; }}
.worker-table td.total-cell {{
  text-align:center; font-weight:800; font-size:0.95rem;
  color:var(--accent);
}}
.worker-table tr.subtotal {{
  background:rgba(99,102,241,0.08); font-weight:700;
}}
.worker-table tr.subtotal td {{ color:var(--accent); }}
.trade-dot {{ width:9px; height:9px; border-radius:50%; display:inline-block; margin-right:7px; flex-shrink:0; box-shadow:0 0 6px currentColor; }}
.trade-name-cell {{ display:flex; align-items:center; gap:4px; }}

/* ── WORKER EDIT INLINE ── */
.worker-input {{
  width:52px; padding:4px 6px; background:var(--bg-secondary);
  border:1px solid var(--border); border-radius:6px;
  color:var(--text-primary); font-size:0.82rem; text-align:center;
  outline:none; transition:all 0.2s;
}}
.worker-input:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-glow); }}
.worker-input::-webkit-inner-spin-button {{ opacity:1; }}

/* ── LOG TABLE ── */
.log-table-wrap {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); overflow:hidden;
  backdrop-filter:blur(12px);
}}
.log-table {{ width:100%; border-collapse:collapse; }}
.log-table thead th {{
  padding:14px 16px; text-align:left; font-size:0.72rem; font-weight:600;
  color:var(--text-muted); text-transform:uppercase; letter-spacing:0.6px;
  background:rgba(14,19,32,0.8); border-bottom:1px solid var(--border);
  position:sticky; top:0; z-index:2;
}}
.log-table tbody tr {{
  border-bottom:1px solid var(--border); transition:all 0.2s; cursor:pointer;
}}
.log-table tbody tr:hover {{ background:var(--bg-card-hover); }}
.log-table tbody tr:last-child {{ border-bottom:none; }}
.log-table td {{ padding:11px 16px; font-size:0.82rem; vertical-align:middle; }}
.date-cell {{ font-weight:600; white-space:nowrap; }}
.weekday {{ font-size:0.7rem; color:var(--text-muted); margin-left:4px; }}
.cat-tags {{ display:flex; flex-wrap:wrap; gap:5px; }}
.cat-tag {{
  display:inline-block; padding:3px 10px; border-radius:12px;
  font-size:0.68rem; font-weight:500; white-space:nowrap;
  backdrop-filter:blur(4px);
}}
.worker-badge {{
  display:inline-flex; align-items:center; gap:4px;
  padding:4px 12px; border-radius:14px; font-size:0.75rem; font-weight:700;
  background:var(--accent-glow); border:1px solid var(--border-glow);
  color:var(--accent); cursor:pointer; transition:all 0.25s;
}}
.worker-badge:hover {{ background:rgba(129,140,248,0.3); transform:scale(1.05); }}
.worker-badge.empty {{ background:rgba(255,255,255,0.03); border-color:var(--border); color:var(--text-muted); }}
.worker-total-big {{ font-size:1.1rem; font-weight:800; color:var(--green); }}

/* ── FILTER BAR ── */
.filter-bar {{ display:flex; gap:12px; margin-bottom:24px; flex-wrap:wrap; align-items:center; }}
.filter-input {{
  flex:1; min-width:200px; padding:11px 18px; background:var(--bg-secondary);
  border:1px solid var(--border); border-radius:var(--radius-sm);
  color:var(--text-primary); font-size:0.85rem; outline:none; transition:all 0.25s;
}}
.filter-input:focus {{ border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-glow); }}
.filter-input::placeholder {{ color:var(--text-muted); }}
.filter-btn {{
  padding:10px 18px; background:var(--bg-secondary); border:1px solid var(--border);
  border-radius:var(--radius-sm); color:var(--text-secondary); font-size:0.82rem;
  cursor:pointer; transition:all 0.25s; white-space:nowrap;
}}
.filter-btn:hover {{ border-color:var(--accent); color:var(--accent); }}
.filter-btn.active {{ background:var(--accent-glow); border-color:var(--border-glow); color:var(--accent); }}

/* ── WEEK/MONTH GROUP ── */
.period-group {{ margin-bottom:28px; }}
.period-header {{
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 18px; background:var(--bg-secondary);
  border-radius:var(--radius-sm) var(--radius-sm) 0 0;
  border:1px solid var(--border); border-bottom:none;
  cursor:pointer; transition:background 0.2s;
}}
.period-header:hover {{ background:var(--bg-card-hover); }}
.period-label {{ font-size:0.9rem; font-weight:700; display:flex; align-items:center; gap:8px; }}
.period-total {{
  font-size:1.25rem; font-weight:800; color:var(--accent);
  display:flex; align-items:center; gap:6px;
}}
.period-total small {{ font-size:0.72rem; color:var(--text-muted); font-weight:400; }}

/* ── BAR CHART ── */
.bar-chart {{ padding:18px; background:var(--bg-card); border:1px solid var(--border); border-radius:0 0 var(--radius-sm) var(--radius-sm); backdrop-filter:blur(8px); }}
.bar-row {{ display:flex; align-items:center; gap:10px; margin-bottom:8px; }}
.bar-row:last-child {{ margin-bottom:0; }}
.bar-label {{ font-size:0.75rem; color:var(--text-secondary); width:130px; flex-shrink:0; text-align:right; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.bar-track {{ flex:1; height:20px; background:rgba(255,255,255,0.03); border-radius:6px; overflow:hidden; position:relative; }}
.bar-fill {{ height:100%; border-radius:6px; transition:width 0.6s ease; min-width:2px; position:relative; }}
.bar-fill::after {{ content:''; position:absolute; inset:0; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.15)); border-radius:inherit; }}
.bar-val {{ font-size:0.75rem; font-weight:700; color:var(--text-primary); width:32px; text-align:right; flex-shrink:0; }}

/* ── MODAL ── */
.modal-overlay {{
  display:none; position:fixed; top:0; left:0; right:0; bottom:0;
  background:rgba(0,0,0,0.65); z-index:100; align-items:center; justify-content:center;
  backdrop-filter:blur(8px); -webkit-backdrop-filter:blur(8px);
}}
.modal-overlay.active {{ display:flex; }}
.modal {{
  background:rgba(17,24,48,0.92); border:1px solid var(--border-active);
  border-radius:20px; max-width:700px; width:92%; max-height:85vh;
  overflow-y:auto; padding:36px; box-shadow:0 24px 80px rgba(0,0,0,0.6), 0 0 60px rgba(99,102,241,0.06);
  animation:modalIn 0.3s cubic-bezier(0.34,1.56,0.64,1);
  backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px);
}}
@keyframes modalIn {{ from{{opacity:0;transform:translateY(20px)}} to{{opacity:1;transform:translateY(0)}} }}
.modal-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; }}
.modal-title {{ font-size:1.2rem; font-weight:700; }}
.modal-close {{
  background:none; border:none; color:var(--text-muted); font-size:1.5rem;
  cursor:pointer; padding:4px 8px; transition:color 0.2s;
}}
.modal-close:hover {{ color:var(--text-primary); }}
.modal-meta {{ display:flex; gap:16px; margin-bottom:20px; flex-wrap:wrap; }}
.modal-meta-item {{ font-size:0.82rem; color:var(--text-secondary); display:flex; align-items:center; gap:4px; }}
.modal-section {{ margin-bottom:20px; }}
.modal-section-title {{ font-size:0.78rem; font-weight:600; color:var(--accent); margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px; }}

/* ── WORKER INPUT GRID ── */
.worker-input-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:10px; }}
.worker-input-row {{
  display:flex; align-items:center; justify-content:space-between;
  padding:8px 12px; background:var(--bg-secondary);
  border-radius:var(--radius-sm); gap:8px;
}}
.worker-input-label {{ font-size:0.78rem; color:var(--text-secondary); flex:1; }}
.wi-number {{
  width:60px; padding:4px 8px; background:var(--bg-card);
  border:1px solid var(--border); border-radius:4px;
  color:var(--text-primary); font-size:0.85rem; text-align:center;
  outline:none; transition:border-color 0.2s;
}}
.wi-number:focus {{ border-color:var(--accent); }}
.total-row {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 16px; background:rgba(99,102,241,0.1);
  border:1px solid rgba(99,102,241,0.2); border-radius:var(--radius-sm); margin-top:12px;
}}
.total-row .label {{ font-size:0.9rem; font-weight:700; }}
.total-row .value {{ font-size:1.4rem; font-weight:800; color:var(--accent); }}
.modal-highlight {{
  font-size:0.82rem; color:var(--text-secondary); padding:6px 0;
  border-bottom:1px solid rgba(255,255,255,0.03);
}}
.modal-btn {{
  padding:10px 20px; border-radius:8px; font-size:0.85rem; font-weight:600;
  border:none; cursor:pointer; transition:all 0.2s;
}}
.modal-btn-primary {{ background:var(--accent); color:white; }}
.modal-btn-primary:hover {{ background:#5254d4; }}
.modal-btn-cancel {{ background:var(--bg-secondary); color:var(--text-secondary); border:1px solid var(--border); }}
.modal-btn-cancel:hover {{ color:var(--text-primary); }}
.modal-footer {{ display:flex; gap:10px; justify-content:flex-end; margin-top:20px; }}

/* ── TOAST ── */
.toast-wl {{
  position:fixed; bottom:28px; right:28px; z-index:999;
  background:rgba(17,24,48,0.9); border:1px solid var(--green);
  border-radius:var(--radius); padding:14px 22px;
  color:var(--green); font-size:0.82rem; font-weight:600;
  box-shadow:0 12px 48px rgba(0,0,0,0.5); backdrop-filter:blur(12px);
  transform:translateY(100px); opacity:0; transition:all 0.4s cubic-bezier(0.34,1.56,0.64,1);
}}
.toast-wl.show {{ transform:translateY(0); opacity:1; }}

/* ── MISSING SECTION ── */
.missing-section {{
  margin-top:20px; padding:18px; background:rgba(248,113,113,0.06);
  border-radius:var(--radius); border:1px solid rgba(248,113,113,0.12);
  backdrop-filter:blur(8px);
}}
.missing-title {{ font-size:0.82rem; font-weight:600; color:var(--red); margin-bottom:10px; display:flex; align-items:center; gap:6px; }}
.missing-list {{ display:flex; gap:8px; flex-wrap:wrap; }}
.missing-day {{ font-size:0.78rem; color:var(--text-secondary); padding:5px 12px; background:rgba(248,113,113,0.08); border-radius:8px; border:1px solid rgba(248,113,113,0.1); transition:all 0.2s; }}
.missing-day:hover {{ background:rgba(248,113,113,0.15); }}

/* ── CALENDAR ── */
.calendar-section {{ margin-bottom:40px; }}
.month-group {{ margin-bottom:28px; }}
.month-label {{
  font-size:0.95rem; font-weight:700; margin-bottom:12px; color:var(--accent);
  display:flex; align-items:center; gap:8px;
}}
.day-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(40px,1fr)); gap:5px; }}
.day-cell {{
  aspect-ratio:1; border-radius:8px; display:flex; align-items:center; justify-content:center;
  font-size:0.72rem; font-weight:600; cursor:pointer; transition:all 0.2s;
  border:1px solid transparent; position:relative;
}}
.day-cell.has-log {{
  background:rgba(52,211,153,0.15); color:var(--green);
  border-color:rgba(52,211,153,0.25);
}}
.day-cell.has-log:hover {{
  background:rgba(52,211,153,0.3); transform:scale(1.15); z-index:2;
  box-shadow:0 0 16px rgba(52,211,153,0.25);
}}
.day-cell.missing {{ background:rgba(248,113,113,0.1); color:var(--red); border-color:rgba(248,113,113,0.18); }}
.day-cell.empty {{ background:rgba(255,255,255,0.015); color:var(--text-muted); }}

/* ── CAT GRID ── */
.cat-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:12px; margin-bottom:40px; }}
.cat-chip {{
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:var(--radius); padding:14px 16px;
  display:flex; align-items:center; gap:10px; transition:all 0.25s;
  backdrop-filter:blur(8px);
}}
.cat-chip:hover {{ border-color:var(--border-active); transform:translateY(-2px); box-shadow:var(--shadow-glow); }}
.cat-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; box-shadow:0 0 8px currentColor; }}
.cat-name {{ font-size:0.82rem; font-weight:500; flex:1; }}
.cat-count {{ font-size:0.95rem; font-weight:700; }}

/* ── PROGRESS BAR (D-Day) ── */
.progress-wrap {{ margin-top:6px; }}
.progress-bar {{ height:4px; border-radius:2px; background:rgba(255,255,255,0.06); overflow:hidden; }}
.progress-fill {{ height:100%; border-radius:2px; transition:width 1s ease; }}
.progress-label {{ font-size:0.65rem; color:var(--text-muted); margin-top:3px; text-align:center; }}

@media(max-width:768px) {{
  .stats-row {{ grid-template-columns:repeat(2,1fr); }}
  .cat-grid {{ grid-template-columns:repeat(2,1fr); }}
  .header h1 {{ font-size:1.6rem; }}
  .bar-label {{ width:90px; font-size:0.68rem; }}
  .container {{ padding:20px 16px; }}
}}
</style>
</head>
<body>
<div class="container">
  <div class="header fade-in">
    <h1>📋 하이디라오 영등포점 시공 작업일지</h1>
    <p>海底捞韩国永登浦店 施工日志 Dashboard — 공종별 인원 집계</p>
    <span class="badge">🤖 Lark 시공그룹 채팅 자동 수집</span>
    <div class="action-bar">
      <button class="action-btn btn-save" id="btnSave" onclick="saveChanges()">💾 저장</button>
      <button class="action-btn btn-excel" onclick="exportExcel()">📊 엑셀 보고서</button>
      <button class="action-btn btn-json" onclick="exportJSON()">📤 JSON</button>
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
            <th>공종별 작업 인원</th>
            <th class="num" style="min-width:80px">총인원</th>
            <th class="num">메시지</th>
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

<script>
// ===== DATA =====
const WORK_LOGS = {data_json};

// ===== TRADE COLOR MAP =====
const TRADE_COLORS = {{
  '철거공사': '#ef4444',
  '가설공사': '#94a3b8',
  '먹매김·측량': '#14b8a6',
  '조적공사': '#f97316',
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
}};

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
function getWorkers(logDate) {{
  const wd = getWorkerData();
  if (wd[logDate] && Object.keys(wd[logDate]).length > 0) return wd[logDate];
  // fallback: JSON 데이터의 trades 필드에서 공종별 인원 가져오기
  const log = WORK_LOGS.logs.find(l => l.log_date === logDate);
  if (log && log.trades && typeof log.trades === 'object' && !Array.isArray(log.trades)) {{
    return log.trades;
  }}
  return {{}};
}}
function setWorkers(logDate, tradeWorkers) {{
  const wd = getWorkerData();
  wd[logDate] = tradeWorkers;
  saveWorkerData(wd);
  hasChanges = true;
  document.getElementById('btnSave').classList.add('has-changes');
}}
function getTotalWorkers(logDate) {{
  const w = getWorkers(logDate);
  return Object.values(w).reduce((a,b) => a + (parseInt(b)||0), 0);
}}

// ===== INIT =====
function init() {{
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
  const allTrades = new Set(logs.flatMap(l => Object.keys(l.trade_details || {{}})));
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

// ===== CAT GRID =====
function renderCatGrid() {{
  const tradeCounts = {{}};
  WORK_LOGS.logs.forEach(l => {{
    Object.keys(l.trade_details || {{}}).forEach(t => {{
      tradeCounts[t] = (tradeCounts[t] || 0) + 1;
    }});
  }});
  const sorted = Object.entries(tradeCounts).sort((a,b) => b[1]-a[1]);
  document.getElementById('catGrid').innerHTML = sorted.map(([name, cnt]) => `
    <div class="cat-chip">
      <div class="cat-dot" style="background:${{TRADE_COLORS[name] || '#6366f1'}}"></div>
      <span class="cat-name">${{name}}</span>
      <span class="cat-count" style="color:${{TRADE_COLORS[name] || '#6366f1'}}">${{cnt}}일</span>
    </div>`).join('');
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
    const d = new Date(l.log_date);
    const wd = WEEKDAYS[d.getDay()];
    const workers = getWorkers(l.log_date);
    const total = getTotalWorkers(l.log_date);
    const trades = Object.keys(l.trade_details || {{}});

    const tradeTags = trades.map(t => {{
      const cnt = workers[t] || 0;
      return `<span class="cat-tag" style="background:${{TRADE_COLORS[t]||'#6366f1'}}22;color:${{TRADE_COLORS[t]||'#6366f1'}};border:1px solid ${{TRADE_COLORS[t]||'#6366f1'}}44">
        ${{t}}${{cnt > 0 ? ` <b>${{cnt}}명</b>` : ''}}
      </span>`;
    }}).join('');

    const workerBadge = total > 0
      ? `<span class="worker-total-big">${{total}}명</span>`
      : `<span style="color:var(--text-muted);font-size:0.78rem">-</span>`;

    return `<tr onclick="openWorkerModal('${{l.log_date}}')">
      <td class="date-cell">${{l.log_date}}<span class="weekday">(${{wd}})</span></td>
      <td><div class="cat-tags">${{tradeTags || '<span style="color:var(--text-muted);font-size:0.75rem">-</span>'}}</div></td>
      <td class="num">${{workerBadge}}</td>
      <td class="num" style="color:var(--text-muted)">${{l.total_messages || 0}}</td>
      <td><button class="worker-badge${{total === 0 ? ' empty' : ''}}" onclick="event.stopPropagation();openWorkerModal('${{l.log_date}}')">
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

function getAllTrades() {{
  const s = new Set();
  WORK_LOGS.logs.forEach(l => {{
    Object.keys(l.trade_details || {{}}).forEach(t => s.add(t));
    if (l.trades && typeof l.trades === 'object' && !Array.isArray(l.trades)) {{
      Object.keys(l.trades).forEach(t => s.add(t));
    }}
  }});
  return [...s].sort();
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
function openWorkerModal(logDate) {{
  const log = WORK_LOGS.logs.find(l => l.log_date === logDate);
  if (!log) return;
  const d = new Date(logDate);
  const wd = WEEKDAYS[d.getDay()];
  const workers = getWorkers(logDate);
  const trades = Object.keys(log.trade_details || {{}});
  const allTrades = getAllTrades();
  const shownTrades = [...new Set([...trades, ...Object.keys(workers).filter(t => workers[t] > 0)])];

  const inputRows = allTrades.map(t => {{
    const isActive = shownTrades.includes(t) || trades.includes(t);
    const color = TRADE_COLORS[t] || '#6366f1';
    return `<div class="worker-input-row" style="${{!isActive ? 'opacity:0.5' : ''}}">
      <span class="trade-dot" style="background:${{color}}"></span>
      <span class="worker-input-label">${{t}}</span>
      <input type="number" min="0" max="999" class="wi-number" id="wi_${{t.replace(/[^a-z가-힣]/gi,'_')}}"
        value="${{workers[t] || 0}}" oninput="updateModalTotal()"
        placeholder="0" ${{!isActive ? 'style="opacity:0.6"' : ''}}>
    </div>`;
  }});

  const total = Object.values(workers).reduce((a,b) => a + (parseInt(b)||0), 0);

  const highlights = (log.day_highlights_kr || log.day_highlights || []).slice(0,4);

  document.getElementById('modal').innerHTML = `
    <div class="modal-header">
      <div>
        <div class="modal-title">👷 작업 인원 입력</div>
        <div style="color:var(--text-secondary);font-size:0.85rem;margin-top:4px">
          ${{logDate}} (${{wd}}) — ${{log.file_name || ''}}</div>
      </div>
      <button class="modal-close" onclick="closeModal()">✕</button>
    </div>

    <div class="modal-section">
      <div class="modal-section-title">공종별 투입 인원 (명)</div>
      <div class="worker-input-grid">${{inputRows.join('')}}</div>
      <div class="total-row">
        <span class="label">📊 당일 총 투입 인원</span>
        <span class="value" id="modalTotal">${{total}}명</span>
      </div>
    </div>

    ${{highlights.length > 0 ? `<div class="modal-section">
      <div class="modal-section-title">📝 당일 주요 대화</div>
      ${{highlights.map(h => `<div class="modal-highlight">${{h.slice(0,120)}}</div>`).join('')}}
    </div>` : ''}}

    <div class="modal-footer">
      <button class="modal-btn modal-btn-cancel" onclick="closeModal()">취소</button>
      <button class="modal-btn modal-btn-primary" onclick="saveWorkerModal('${{logDate}}')">💾 저장</button>
    </div>`;

  document.getElementById('modalOverlay').classList.add('active');
}}

function updateModalTotal() {{
  const inputs = document.querySelectorAll('.wi-number');
  let total = 0;
  inputs.forEach(inp => total += parseInt(inp.value) || 0);
  document.getElementById('modalTotal').textContent = total + '명';
}}

function saveWorkerModal(logDate) {{
  const allTrades = getAllTrades();
  const workers = {{}};
  allTrades.forEach(t => {{
    const id = 'wi_' + t.replace(/[^a-z가-힣]/gi,'_');
    const el = document.getElementById(id);
    if (el) {{
      const v = parseInt(el.value) || 0;
      if (v > 0) workers[t] = v;
    }}
  }});
  setWorkers(logDate, workers);
  closeModal();
  renderDailyTable();
  renderStats();
  showToast('✅ 인원 저장 완료!');
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
      const dow = new Date(yr, mm-1, d).getDay();
      const workers = inLog ? getTotalWorkers(ds) : 0;
      const cls = inLog ? 'has-log' : '';
      const tooltip = inLog ? `${{ds}}${{workers > 0 ? ` (${{workers}}명)` : ''}}` : ds;
      cells.push(`<div class="day-cell ${{cls}}" title="${{tooltip}}" onclick="${{inLog ? `openWorkerModal('${{ds}}')` : ''}}">
        ${{d}}${{workers > 0 ? `<sup style="font-size:0.5rem;color:var(--green)">●</sup>` : ''}}
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
    if (dow !== 0 && dow !== 6 && !logDates.has(ds)) missing.push(ds);
    d.setDate(d.getDate()+1);
  }}
  if (missing.length === 0) {{ document.getElementById('missingSection').innerHTML = ''; return; }}
  document.getElementById('missingSection').innerHTML = `
    <div class="missing-title">⚠️ 미제출 평일 (${{missing.length}}일)</div>
    <div class="missing-list">${{missing.slice(0,30).map(d => `<span class="missing-day">${{d}}</span>`).join('')}}${{missing.length > 30 ? `<span class="missing-day">+${{missing.length-30}}일</span>` : ''}}</div>`;
}}

// ===== SAVE / EXPORT =====
function saveChanges() {{
  // Worker data is auto-saved to localStorage
  // Optionally also export as JSON for backup
  showToast('✅ 인원 데이터 저장됨 (브라우저 로컬 저장소)');
  hasChanges = false;
  document.getElementById('btnSave').classList.remove('has-changes');
}}

function exportExcel() {{
  const allTrades = getAllTrades();
  let csv = 'BOM,\\uFF2C\\uFF2F\\uFF27 날짜,총 인원,' + allTrades.join(',') + '\\n';
  WORK_LOGS.logs.forEach(l => {{
    const workers = getWorkers(l.log_date);
    const total = getTotalWorkers(l.log_date);
    const tradeCols = allTrades.map(t => workers[t] || 0);
    csv += `"${{l.file_name}}",${{l.log_date}},${{total}},${{tradeCols.join(',')}}\\n`;
  }});
  // Add weekly summary
  csv += '\\n[주별 집계]\\n주 시작일,주 종료일,총 인원,' + allTrades.join(',') + '\\n';
  const weeks = {{}};
  WORK_LOGS.logs.forEach(l => {{
    const d = new Date(l.log_date);
    const mon = new Date(d); mon.setDate(d.getDate() - ((d.getDay()+6)%7));
    const wk = mon.toISOString().slice(0,10);
    if (!weeks[wk]) weeks[wk] = [];
    weeks[wk].push(l);
  }});
  Object.keys(weeks).sort().forEach(wk => {{
    const wkEnd = new Date(wk); wkEnd.setDate(wkEnd.getDate()+6);
    const tradeTotals = {{}};
    let gt = 0;
    weeks[wk].forEach(l => {{
      const w = getWorkers(l.log_date);
      allTrades.forEach(t => {{
        tradeTotals[t] = (tradeTotals[t]||0) + (parseInt(w[t])||0);
        gt += (parseInt(w[t])||0);
      }});
    }});
    csv += `${{wk}},${{wkEnd.toISOString().slice(0,10)}},${{gt}},${{allTrades.map(t=>tradeTotals[t]||0).join(',')}}\\n`;
  }});

  const blob = new Blob(['\\uFEFF'+csv], {{type:'text/csv;charset=utf-8;'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '하이디라오_인원집계_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
  showToast('📊 CSV 다운로드 시작!');
}}

function exportJSON() {{
  const wd = getWorkerData();
  const exportData = {{...WORK_LOGS, workerData: wd, exportedAt: new Date().toISOString()}};
  const blob = new Blob([JSON.stringify(exportData, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '하이디라오_작업일지_' + new Date().toISOString().slice(0,10) + '.json';
  a.click();
  showToast('📤 JSON 다운로드!');
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
