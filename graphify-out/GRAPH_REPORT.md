# Graph Report - .  (2026-07-31)

## Corpus Check
- 132 files · ~147,505 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 515 nodes · 774 edges · 42 communities (32 shown, 10 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.84)
- Token cost: 669,241 input · 61,500 output

## Community Hubs (Navigation)
- 5-6월 시공 협의 채팅
- 착공·초기 협의 (4월)
- 5월 초 도면·마감 협의
- 회의록·설계변경 관리
- 대시보드 (작업일지·트래커)
- 입구·외관 디자인 협의
- 아침 자동 업데이트 파이프라인
- 일일 갱신·채팅 이벤트
- 회의록 자동 처리
- 그리스트랩·4층 협의
- 작업일지 자동 추출
- 시공일지 PDF 다운로드
- 라크 채팅 수집
- PDF 파싱·인원 반영
- 대시보드 업데이트 서버
- 작업일지 고도화
- 라크 OAuth 로그인
- 시공일지 문서 구조
- 라크 채팅 저장
- ALC 자재·마감 확인
- MBTI 테스트 (무관)
- 이벤트 데이터 파일
- 이벤트 ID 체계
- 방화셔터·방수 협의
- PDF 번역 도구
- 공종 파싱 검사
- 가구 심화도면 확인
- 5/23 채팅
- 프로젝트 메모리
- 애플 터치 아이콘
- PWA 아이콘 192
- PWA 아이콘 192 마스커블
- PWA 아이콘 512
- PWA 아이콘 512 마스커블

## God Nodes (most connected - your core abstractions)
1. `시공일지 (海底捞韩国永登浦店项目施工日志 PDF, 매일 공유)` - 22 edges
2. `일일 공사일지 (海底捞韩国永登浦店项目施工日志 PDF)` - 15 edges
3. `refresh_via_refresh_token()` - 11 edges
4. `parse_file_to_event()` - 11 edges
5. `update_event_tracker()` - 10 edges
6. `main()` - 10 edges
7. `2026.04.24 하이디라오 영등포 회의록 (한국어버전)` - 10 edges
8. `배기팬 선정 (원심팬 요구, DR-F35HTC 등 11대 확정)` - 10 edges
9. `main()` - 9 edges
10. `log()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `SCHEDULE 공정 일정 데이터 상수` --semantically_similar_to--> `7~8월 잔여 공정 간트 일정 (주방/화장실/홀/전기/공조/급배수/가스/소방/제작가구/준공청소)`  [INFERRED] [semantically similar]
  /Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/하이디라오_작업일지.html → /Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/실제_잔여공사일정표_하이디라오영등포점(0708).pdf
- `auto_refresh_token()` --calls--> `refresh_via_refresh_token()`  [EXTRACTED]
  download_work_logs.py → daily_update.py
- `main()` --calls--> `refresh_via_refresh_token()`  [EXTRACTED]
  morning_update.py → daily_update.py
- `main()` --calls--> `update_event_tracker()`  [EXTRACTED]
  morning_update.py → daily_update.py
- `update_html()` --calls--> `translate_data_for_html()`  [EXTRACTED]
  parse_and_apply.py → work_i18n.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **하이디라오 영등포점 회의록 시리즈 (착공 전~7월 4주차)** — graphify_out_converted_20260403_meeting_final_3b350f9f, graphify_out_converted_20260420_video_meeting_dc7412fe, graphify_out_converted_20260424_meeting_korean_ad063253, graphify_out_converted_20260508_meeting_korean_17554a2b, graphify_out_converted_20260519_meeting_b4b5b6a1, graphify_out_converted_20260630_weekly_meeting_37106586, graphify_out_converted_20260714_weekly_meeting_29106ab2, graphify_out_converted_20260716_site_meeting_ceiling_0baceb12, graphify_out_converted_20260720_weekly_meeting_b60a50a4, graphify_out_converted_20260728_weekly_meeting_67fcd355 [EXTRACTED 1.00]
- **설계 변경 통지서 시리즈 (HGYDP01·02, 급배수·전기)** — graphify_out_converted_design_change_notice_260415_v2_80bff4c2, graphify_out_converted_change_notice_0507_819c11a7, graphify_out_converted_plumbing_electrical_change_notice_0512_cdaa6ad1, graphify_out_converted_20260522_design_change_notice_3ac06e83, graphify_out_converted_design_change_notice_260415_v2_80bff4c2_design_change_notice_process [EXTRACTED 1.00]
- **배기 방식 결정 흐름 (층고 계산 → 측면/바닥 배기 비교 → 설계 변경 반영)** — graphify_out_converted_20260424_meeting_korean_ad063253_ceiling_height_calculation, graphify_out_converted_20260424_meeting_korean_ad063253_side_exhaust_system, graphify_out_converted_20260424_meeting_korean_ad063253_floor_exhaust_system, graphify_out_converted_design_change_notice_260415_v2_80bff4c2 [INFERRED 0.85]
- **주입구 방화문 소방 적합성 검토 흐름 (법규 확인 → 대안 설계 → 최종 확인)** — lark_chat_2026_04_30_james_kim, lark_chat_2026_04_30_fire_shutter_regulation_issue, lark_chat_2026_04_30_fire_code_rule_article14, lark_chat_2026_04_30_main_entrance_door_proposals, lark_chat_2026_05_01_fire_door_compliance_ruling [EXTRACTED 1.00]
- **일일 공사일지 보고 체계 (새누리 → 라크 그룹)** — lark_chat_2026_04_16_kim_changmin, lark_chat_2026_04_16_daily_construction_log, lark_chat_2026_04_16_saenuri_contractor [EXTRACTED 1.00]
- **도면 교부·문제 제기·수정 사이클** — lark_chat_2026_04_17_drawing_briefing_meeting, lark_chat_2026_04_24_drawing_issue_list, lark_chat_2026_04_27_dimension_discrepancy, lark_chat_2026_04_28_revised_floor_plan, lark_chat_2026_05_01_post_briefing_blueprint, lark_chat_2026_04_27_yan_jiaojie [INFERRED 0.85]
- **그리스트랩 설치 이슈 흐름 (천장 개구 → 4층 허가 분쟁 → 책임 정리)** — lark_conversation_2026_05_08_grease_trap_ceiling_opening, lark_conversation_2026_05_09_fourth_floor_opening_permission, lark_conversation_2026_05_21_grease_trap_4f_negotiation [EXTRACTED 1.00]
- **온수기실 설계 결정 (방화구획·급기/배수·위치 확정)** — lark_conversation_2026_05_14_water_heater_fire_compartment, lark_conversation_2026_05_19_water_heater_room_ventilation, lark_conversation_2026_05_21_hot_water_room_location [INFERRED 0.85]
- **설계변경통지서 시리즈 (0507·0512·0522)** — lark_conversation_2026_05_07_design_change_notice_0507, lark_conversation_2026_05_12_design_change_notice_0512, lark_conversation_2026_05_22_design_change_notice_0522 [INFERRED 0.85]
- **배기팬 선정·검토 협업 (총 11대 파라미터 확인)** — lark_daehwanaeyong_2026_05_27_james_kim, lark_daehwanaeyong_2026_06_06_wu_yiqi, lark_daehwanaeyong_2026_05_27_qian_qijiang, lark_daehwanaeyong_2026_06_04_wang_yong, lark_daehwanaeyong_2026_06_04_exhaust_fan_selection [EXTRACTED 1.00]
- **분전반 3개 위치 이동 의사결정 흐름 (제안-확인-변경도면)** — lark_daehwanaeyong_2026_05_27_james_kim, lark_daehwanaeyong_2026_05_26_chen_yuliang, lark_daehwanaeyong_2026_05_26_wei_zhonglong, lark_daehwanaeyong_2026_05_26_kim_seolhwa, lark_daehwanaeyong_2026_06_06_electric_box_relocation [EXTRACTED 1.00]
- **EPS1/EPS2 전기 인입 협의 (요청-회의-최종확정-연락함)** — lark_daehwanaeyong_2026_05_24_lim_jiyoung, lark_daehwanaeyong_2026_05_28_hu_xincai, lark_daehwanaeyong_2026_05_29_huang_jianhui, lark_daehwanaeyong_2026_05_26_chen_yuliang, lark_daehwanaeyong_2026_06_09_eps_power_allocation [EXTRACTED 1.00]
- **공사일지 PDF 일일 보고 및 작업일지 대시보드 집계 플로우** — lark_chat_2026_06_15_construction_log_20260615, lark_chat_2026_06_16_construction_log_20260616, lark_chat_2026_06_17_construction_log_20260617, haidilao_work_log [INFERRED 0.85]
- **바닥 되메우기 사양(철망/폼시멘트) 결정 논의** — lark_chat_2026_06_17, lark_chat_2026_06_17_floor_backfill_wire_mesh, lark_chat_2026_06_17_foam_cement_backfill [EXTRACTED 1.00]
- **하이디라오 영등포점 프로젝트 모니터링 시스템 (트래커/작업일지/공정표/채팅 아카이브)** — haidilao_event_tracker, haidilao_work_log, remaining_schedule_haidilao_yeongdeungpo_0708, lark_chat_readme [INFERRED 0.75]

## Communities (42 total, 10 thin omitted)

### Community 0 - "5-6월 시공 협의 채팅"
Cohesion: 0.06
Nodes (61): 라크 대화 2026-05-24, 시공일지 (海底捞韩国永登浦店项目施工日志 PDF, 매일 공유), 하이디라오 영등포점 프로젝트 (海底捞韩国永登浦店), 임지영(林智煐) — 시공사 엔지니어(林工), 박현우(朴玹瑀) — 시공일지 발송 담당, 라크 대화 2026-05-25, 라크 대화 2026-05-26, 陈玉亮 (기전 설계 담당, 陈工) (+53 more)

### Community 1 - "착공·초기 협의 (4월)"
Cohesion: 0.06
Nodes (58): 라크 시공 그룹 대화 2026-04-01, 총괄시공사 인수인계 회의 (4/3 금 14:30, 5층 현장), 金雪花 김설화 (하이디라오 측 관리자), 李津梅 이진매 (하이디라오 측 현장 조율 담당), 임지영 林智煐 (새누리 시공사 담당), 魏钟龙 (하이디라오 본사 공정 담당 팀장), 라크 시공 그룹 대화 2026-04-03, 라크 시공 그룹 대화 2026-04-09 (+50 more)

### Community 2 - "5월 초 도면·마감 협의"
Cohesion: 0.05
Nodes (44): 라크 시공그룹 대화 2026-05-03, 하이디라오 영등포점 공사일지 20260503 (PDF), 도면 변경사항 요약 설명 요청, 방화판 상단 마감 처리 (씰링 스트립), 지하1층 임대구역 칸막이벽 철거, 배경음악 배선 (오디오케이블 L-2S8F), 라크 시공그룹 대화 2026-05-04, 하이디라오 영등포점 공사일지 20260504 (PDF) (+36 more)

### Community 3 - "회의록·설계변경 관리"
Cohesion: 0.10
Nodes (36): 2026.04.03 회의록 최최종 (착공 전 현장인계 회의), 준공·인도 목표일 2026-08-15, 에스컬레이터 철거 (5층, 건물측 선행 공사), 소방 도면 한국 법규 적합성 검토, 하이디라오 영등포점 신5점 프로젝트, 세누리건축 (시공사), 웨이중롱 (魏钟龙, 하이디라오 공사 총괄), 2026.04.20 화상회의록 (먹작업 지연 점검) (+28 more)

### Community 4 - "대시보드 (작업일지·트래커)"
Cohesion: 0.08
Nodes (35): 하이디라오 영등포점 공사 이벤트 트래커 대시보드, BUILTIN_ID_SET 내장 이벤트 ID 집합, 이벤트 카테고리 분류 (확정/변경/이슈/비용/회의/도면/일정/보고/채팅/메일), 하이디라오 영등포점 시공 작업일지 대시보드, 엑셀(xlsx) 내보내기 기능, PWA 홈화면 지원 (manifest.webmanifest, 앱 아이콘), SCHEDULE 공정 일정 데이터 상수, 공종 분류 체계 (TRADE_ORDER, TRADE_COLORS, ROLE_TO_TRADE, MANAGER/SUPPORT_TRADES) (+27 more)

### Community 5 - "입구·외관 디자인 협의"
Cohesion: 0.06
Nodes (34): 경매공지 안내문 20260506 (PDF·번역), 라크 시공그룹 대화 2026-05-06, 하이디라오 영등포점 공사일지 20260505·20260506 (PDF), 입면도 누락 지적 및 보완, 입구 벽 1200 방화문 개구 요구, 주출입구 효과도 수정 보고안 20260506 (PDF), 입구 벽 원형 5개 디자인 검토 (직경 1645), 펫공간 유리프레임 자재 표기 불일치 (입면 MT-08 vs 단면 L-01) (+26 more)

### Community 6 - "아침 자동 업데이트 파이프라인"
Cohesion: 0.13
Nodes (27): download_pdf(), fetch_messages(), get_token(), group_messages_by_date(), lark_get(), log(), main(), msg_timestamp() (+19 more)

### Community 7 - "일일 갱신·채팅 이벤트"
Cohesion: 0.12
Nodes (30): build_chat_event_js(), fetch_all_messages(), fetch_messages(), _fetch_messages_range(), _get_app_token(), get_existing_chat_dates(), get_existing_chat_event_ids(), get_refresh_token() (+22 more)

### Community 8 - "회의록 자동 처리"
Cohesion: 0.14
Nodes (24): build_meeting_event_js(), clean_lines(), doc_to_text(), download_file(), extract_date(), extract_summary(), extract_title(), get_existing_sources_and_maxnum() (+16 more)

### Community 9 - "그리스트랩·4층 협의"
Cohesion: 0.11
Nodes (20): 라크 시공그룹 대화 2026-05-08 (주간회의일), 하이디라오 영등포점 공사일지 20260508 (PDF), 그리스트랩 설치용 4층 천장 개구 작업, 발주 수량 확인 (방화판 마감재·배수구 그레이트·석재), 라크 시공그룹 대화 2026-05-09, 하이디라오 영등포점 공사일지 20260509 (PDF), 에스컬레이터 위치 구조도면 발송 요청, 4층 임차인 천장 개구 허가 번복 문제 (+12 more)

### Community 10 - "작업일지 자동 추출"
Cohesion: 0.33
Nodes (12): extract_day_context(), extract_work_log_from_messages(), fetch_recent_messages(), get_token(), log(), main(), 저장된 User Access Token 읽기, 브라우저를 열어 새 User Access Token 발급 (+4 more)

### Community 11 - "시공일지 PDF 다운로드"
Cohesion: 0.29
Nodes (12): auto_refresh_token(), download_file(), get_token(), load_work_logs(), log(), main(), make_safe_filename(), Lark 파일 다운로드 API: GET /open-… (+4 more)

### Community 12 - "라크 채팅 수집"
Cohesion: 0.32
Nodes (11): api_request(), find_construction_group(), generate_events(), get_messages(), get_tenant_token(), group_messages_by_date(), list_chats(), main() (+3 more)

### Community 13 - "PDF 파싱·인원 반영"
Cohesion: 0.38
Nodes (9): load_data(), log(), main(), parse_pdf(), PDF 1페이지에서 구조화된 데이터 추출 (좌표 기반): - 날짜 - 공종별 인원 (좌측 컬럼: x < 200) - 총 인원수 - 시공내용…, 하이디라오_작업일지.html의 WORK_LOGS 객체 업데이트, translate_trade(), translate_work() (+1 more)

### Community 15 - "작업일지 고도화"
Cohesion: 0.46
Nodes (7): classify_by_trade(), extract_work_details_by_trade(), extract_worker_count(), main(), process_raw_messages(), lark_raw_messages.json에서 날짜별 텍스트 메시지 그룹화, translate_text()

### Community 16 - "라크 OAuth 로그인"
Cohesion: 0.33
Nodes (4): get_user_token(), main(), OAuthHandler, Authorization Code → User Access Token

### Community 17 - "시공일지 문서 구조"
Cohesion: 0.38
Nodes (7): Daily construction log document (2026-06-17) — rendered page for Haidilao Korea Store 5 (Yeongdeungpo), Today's work summary (오늘 시공 내용) — site cleanup/waste disposal, metal work, carpentry, waterproofing, water supply/drain piping, electrical, duct, HVAC piping, fire protection piping, Haidilao Korea 5th store (Yeongdeungpo) construction project — 서울시 영등포구 영중로 28 점프밀라노 5층; start 2026-04-15, completion 2026-08-15, Project info header block — project name/address, regional manager 윤대진, store manager 김설화, construction supervisor 웨이중롱, management company 전과건축공정유한공사 (책임자 쑨텅페이, 현장 책임자 치엔치장), contractor SENOORI ARCHITECTURE CO., LTD. (책임자 이응진, 현장 책임자 김창민), SENOORI ARCHITECTURE CO., LTD. — construction contractor (시공업체), Trade-by-trade manpower table (공종/인원수/시공 내용) — 관리인원 5, 번역 2, 직영반장 6, 금속공 7, 목공 2, 전기공 7, 덕트공 8, 방수공 3, 배관공 4, 냉난방공조공 12, 소방공 4; total 60명, 공종별 작업자 인원 (per-trade worker counts) concept — the data category the gongjong worker pipeline fills from parsed PDFs

### Community 19 - "ALC 자재·마감 확인"
Cohesion: 0.33
Nodes (6): (주)성은 ALC블럭 자재승인서류 (PDF), 등띠 스테인리스 마감 확인 (고동색 브러시드), 천장 형태 모형 제출 일정 (익일 완료), 라크 시공그룹 대화 2026-05-11, 하이디라오 영등포점 공사일지 20260511 (PDF), 옥외 간판 최종 효과도 문의

### Community 20 - "MBTI 테스트 (무관)"
Cohesion: 0.60
Nodes (5): MBTI 테스트 웹앱, computeType 점수 집계 함수, QUESTIONS 36문항 데이터 (E/I·S/N·T/F·J/P 각 9문항), share 결과 공유 기능 (Web Share API + URL 해시), TYPES 16유형 결과 데이터

### Community 21 - "이벤트 데이터 파일"
Cohesion: 0.40
Nodes (4): CAT_CONFIG, EVENTS, MONTHS, WEEKDAYS

### Community 22 - "이벤트 ID 체계"
Cohesion: 0.67
Nodes (4): 이벤트 ID 목록 (EVT-001~053), 이벤트 ID 최종 목록 (EVT-001~053), index.html (이벤트 트래커 리다이렉트), 하이디라오 이벤트 트래커 (EVT ID 체계)

### Community 23 - "방화셔터·방수 협의"
Cohesion: 0.50
Nodes (4): 라크 시공그룹 대화 2026-05-17, 하이디라오 영등포점 공사일지 20260517 (PDF), 엘리베이터홀 방화 롤러셔터 철거 불가, 방수 시공 시 사전 통보 요청 (화장실·주방·세척실)

### Community 24 - "PDF 번역 도구"
Cohesion: 0.83
Nodes (3): rename_and_translate_all(), translate_pdf_file(), translate_text()

### Community 26 - "가구 심화도면 확인"
Cohesion: 0.67
Nodes (3): 라크 시공그룹 대화 2026-05-02, 하이디라오 영등포점 공사일지 20260502 (PDF), 목재·스테인리스 가구 심화도면 매장 최종확인

## Ambiguous Edges - Review These
- `펫공간 유리프레임 자재 표기 불일치 (입면 MT-08 vs 단면 L-01)` → `펫공간 캐비닛 치수 변경 (신규 도면 기준 적용)`  [AMBIGUOUS]
  /Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/라크 대화내용/2026-05-12.md · relation: conceptually_related_to
- `입구 벽 원형 5개 디자인 검토 (직경 1645)` → `L1 완성형 소프트 조명 스트립 사양`  [AMBIGUOUS]
  /Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/라크 대화내용/2026-05-07.md · relation: conceptually_related_to
- `라크 대화 2026-06-12` → `EPS1/EPS2 전기 인입 및 케이블 배분 (최종 각 75A+300A)`  [AMBIGUOUS]
  /Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/라크 대화내용/2026-06-12.md · relation: references

## Knowledge Gaps
- **103 isolated node(s):** `EVENTS`, `CAT_CONFIG`, `WEEKDAYS`, `MONTHS`, `Project Memory (CLAUDE.md)` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `펫공간 유리프레임 자재 표기 불일치 (입면 MT-08 vs 단면 L-01)` and `펫공간 캐비닛 치수 변경 (신규 도면 기준 적용)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `입구 벽 원형 5개 디자인 검토 (직경 1645)` and `L1 완성형 소프트 조명 스트립 사양`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `라크 대화 2026-06-12` and `EPS1/EPS2 전기 인입 및 케이블 배분 (최종 각 75A+300A)`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `라크 시공그룹 대화 2026-05-19 (주간회의일)` connect `5월 초 도면·마감 협의` to `입구·외관 디자인 협의`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `translate_data_for_html()` connect `아침 자동 업데이트 파이프라인` to `PDF 파싱·인원 반영`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `라크 시공그룹 대화 2026-05-21` connect `5월 초 도면·마감 협의` to `그리스트랩·4층 협의`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **What connects `EVENTS`, `CAT_CONFIG`, `WEEKDAYS` to the rest of the system?**
  _103 weakly-connected nodes found - possible documentation gaps or missing edges._