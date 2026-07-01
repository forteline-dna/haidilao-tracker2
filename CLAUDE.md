# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a construction-progress tracking system for the **Haidilao Yeongdeungpo branch (하이디라오 영등포점)** interior-fit-out project in Korea. It pulls data from a **Lark (Feishu) construction group chat**, parses Chinese-language daily construction logs (施工日志 PDFs), translates/normalizes the content into Korean, and renders two self-contained HTML dashboards. The codebase is almost entirely standalone Python scripts plus generated HTML/JSON data files. Most code, comments, and data are in Korean and Chinese.

The two deliverables are:
- **하이디라오_작업일지.html** — work-log dashboard (per-trade worker counts, daily/weekly/monthly aggregation). Built from `작업일지_데이터.json`.
- **하이디라오_이벤트트래커.html** — event tracker (meetings, design changes, issues). Built from `이벤트_데이터.js`. `index.html` redirects here.

## Commands

There is no build system, package manager, or test framework. Scripts run directly with `python3` from the repo root (each resolves paths via `BASE_DIR = os.path.dirname(os.path.abspath(__file__))`, so cwd does not matter, but the data files live in the repo root).

**Primary orchestrator** (collects Lark messages → updates both dashboards):
```bash
python3 daily_update.py            # incremental: last 26 hours
python3 daily_update.py --token    # re-authenticate (issue new user token) then run
python3 daily_update.py --full     # re-collect the entire history
```

**Work-log-only morning job** (also downloads new PDFs; designed to run via launchd at 09:00 KST):
```bash
python3 morning_update.py
```

**Regenerate a dashboard from existing data** (no network):
```bash
python3 build_worklogs_html.py     # 작업일지_데이터.json → 하이디라오_작업일지.html
```

**One-off pipeline stages** (rarely needed; `daily_update.py`/`morning_update.py` wrap these):
```bash
python3 download_work_logs.py [--all|--token]   # pull 施工日志 PDFs into 일일작업일보/
python3 parse_and_apply.py [--dry]              # parse PDFs (worker counts, trades) → JSON + HTML
python3 translate_existing_pdfs.py             # CN→KR translation of PDF text (uses translation_cache.json)
```

Verification helpers (`verify_json.py`, `verify_rows.py`, `verify_fitz_options.py`, `inspect_trades.py`) are ad-hoc inspection scripts, not a test suite — read them before running.

## Dependencies

- **Python 3** standard library for all networking (`urllib.request`, not `requests`) and Lark API calls.
- **PyMuPDF** (`import fitz`) — required only by the PDF-parsing scripts (`parse_and_apply.py`, `translate_existing_pdfs.py`, `inspect_trades.py`, `verify_*`). Install with `pip3 install pymupdf` if missing.
- `translate_existing_pdfs.py` references a macOS system font path (`/System/Library/Fonts/AppleSDGothicNeo.ttc`); the PDF-translation rendering path assumes macOS.

## Architecture / data flow

```
Lark group chat  ──fetch──►  lark_raw_messages.json  (raw message cache, gitignored)
       │                            │
       │ PDF attachments            │ text messages
       ▼                            ▼
 일일작업일보/*.pdf            event extraction (≥20 msgs/day ⇒ an event)
       │                            │
   parse (fitz)                     ▼
       ▼                     이벤트_데이터.js  ──►  하이디라오_이벤트트래커.html
 작업일지_데이터.json  ──►  하이디라오_작업일지.html
```

Key points to understand before editing:

- **`작업일지_데이터.json` is the single source of truth for the work-log dashboard.** Top-level keys: `project`, `data_source`, `total_logs`, `period`, `logs` (array), `trade_system`, `last_updated`. Each `logs` entry carries both raw Chinese and translated Korean fields (e.g. `trades`/`trades_cn`, `work_contents`/`work_contents_cn`, `work_categories`/`work_categories_kr`), `worker_count`/`total_workers`, `locations`, and a `pdf_parsed` flag. `build_worklogs_html.py` embeds this JSON verbatim into the HTML and renders client-side — so to change the dashboard you regenerate the HTML, you do not hand-edit it.

- **Trade classification is keyword-driven.** `WORK_CATEGORIES` (in `morning_update.py`) and the `trade_system` / standard-trade tables (in `enhance_work_logs.py`) map Chinese + Korean keywords to construction trades (철거, 조적, 방수, 소방, etc.). Adding a trade or fixing misclassification means editing these keyword maps, not the rendering code.

- **Event extraction is threshold-based.** A chat day with **≥20 messages** (`MIN_MSG_FOR_EVENT` in `daily_update.py`, mirrored in `generate_chat_events.py`) becomes a tracker event. `EVT-001`…`EVT-032` are curated, hand-mapped events (`EXISTING_EVENTS_TOPICS` in `daily_update.py`, duplicated in `link_events.py`); auto-generated chat events start at `EVT-033`. `link_events.py` cross-links curated and chat events by date/topic.

- **CN→KR translation uses a persistent cache.** `translation_cache.json` (~170 KB) stores prior translations; `TRANSLATION_MAP` dicts in `enhance_work_logs.py` / `translate_existing_pdfs.py` hold the architecture/interior glossary. Reuse the cache rather than re-translating.

## Lark API integration

- Credentials are **hardcoded** in the scripts: `APP_ID = cli_a97aa70eeca15e15`, `APP_SECRET`, and the construction group `CHAT_ID = oc_943f27f012a4da28abb89083bc7095a3`, against `https://open.larksuite.com`. Treat these as the project's real keys — do not echo them into new public artifacts unnecessarily, and prefer reading them from the existing constants.
- A **user access token** is required for message history and is stored in `lark_user_token.txt` (gitignored). When it expires, scripts log a prompt to re-run with `--token`, which triggers the OAuth flow (`lark_oauth_login.py` runs a local OAuth callback server).
- All times are **KST** (`timezone(timedelta(hours=9))`); incremental fetches use a 26-hour look-back window to tolerate run-time drift.

## Conventions & gotchas

- **Generated files are committed.** `하이디라오_작업일지.html`, `하이디라오_이벤트트래커.html`, `작업일지_데이터.json`, and `이벤트_데이터.js` are build outputs but tracked in git. Regenerate them with the scripts rather than editing by hand, then commit the regenerated output.
- **Gitignored** (see `.gitignore`): `lark_user_token.txt`, `lark_auth_result.json`, `lark_raw_messages.json`, `*.log`, `browser/`, `.tempmediaStorage/`. These hold secrets/large raw caches and are recreated at runtime.
- **Filenames and directories are Korean** and some contain spaces (`라크 대화내용/`, `일일작업일보/`, `회의록/`, `도면수정내용/`). Quote paths in shell commands. `save_lark_chats.py` notes macOS NFD normalization for these names.
- `daily_update.py` and `morning_update.py` overlap heavily — `daily_update.py` is the unified entry point (events + work logs); `morning_update.py` is the work-log-focused scheduled job that additionally downloads PDFs. The older `auto_update_work_logs.py` and the `*_chat_events*.txt` / `inject_chat_events.py` / `generate_chat_events.py` scripts are earlier one-shot pipeline stages superseded by the unified updaters.
