#!/usr/bin/env python3
import os
import json
import re
import fitz

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, '일일작업일보')
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')
HTML_FILE = os.path.join(BASE_DIR, '하이디라오_작업일지.html')
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 1. 통합 번역 사전 구축 (기존 스크립트 번역 정보 통합 + 레이아웃 항목 추가)
TRANSLATION_MAP = {
    # 레이아웃 고정 텍스트 (Page 1)
    "项目名称": "프로젝트 명",
    "项目地址": "프로젝트 주소",
    "大区经理": "지역 매니저",
    "店经理": "매장 매니저",
    "工程项目督查": "공사 감독",
    "设计督导": "설계 지도",
    "管理公司": "관리회사",
    "全科建筑工程有限公司": "전과건축공정유한공사",
    "管理公司负责人": "관리회사 책임자",
    "管理公司现场负责人": "관리회사 현장 책임자",
    "施工单位": "시공업체",
    "施工单位负责人": "시공업체 책임자",
    "施工单位现场负责人": "시공업체 현장 책임자",
    "进场时间": "착공일",
    "验收时间": "준공일",
    "阶段重要节点": "단계별 중요 일정",
    "完成时间": "완료 시간",
    "今日施工内容": "오늘 시공 내용",
    "今日施工人数总计": "금일 총 시공 인원",
    "施工日志": "시공일지",
    "施工内容": "시공 내용",
    "项目信息": "프로젝트 정보",
    "工种": "공종",
    "人数": "인원수",
    "海底捞韩国   5店(永登浦店）项目工程施工日志": "하이디라오 한국 5호점(영등포점) 프로젝트 공사 시공일지",
    "海底捞韩国   5店(永登浦店）": "하이디라오 한국 5호점(영등포점)",
    "首尔市永登浦区永中路28 Jump Milano 5层": "서울시 영등포구 영중로 28 점프밀라노 5층",

    # 레이아웃 고정 텍스트 (Page 2)
    "项目阶段": "프로젝트 단계",
    "阶段进度": "단계별 진척도",
    "阶段进度百分比": "단계별 진척율",
    "位置": "위치",
    "说明": "설명",
    "序号": "일련번호",
    "分类": "분류",
    "甲供品": "발주처 지급품",
    "到货时间": "도착 시간",
    "是否到货": "도착 여부",
    "是否安装": "설치 여부",
    "重要节点": "중요 일정",
    "施工阶段重要节点检查": "시공단계 중요일정 점검",
    "检查人": "점검자",
    "特殊情况": "특이사항",
    "甲供品分类统计表": "발주처 지급품 분류 통계표",
    "项目照片": "프로젝트 사진",

    # 담당자 이름 번역
    "孙腾飞": "쑨텅페이",
    "钱齐江": "치엔치장",
    "魏钟龙": "웨이중롱",
    "尹大进": "윤대진",
    "金雪花": "김설화",
    "李應振": "이응진",
    "金昌民": "김창민",

    # 장소
    "餐厅": "홀(객석)",
    "后厨": "주방",
    "包间": "룸(룸구역)",
    "等待区": "대기 구역",
    "等候区": "대기 구역",
    "厨房": "주방",
    "卫生间": "화장실",
    "用餐区": "객석 구역",
    "过道": "복도",
    "入口": "입구",

    # 공종 (TRADE_MAP 기반)
    "管理人员": "관리인원",
    "翻译": "번역",
    "现场班长": "직영반장",
    "木工": "목공",
    "电工": "전기공",
    "水泥工": "미장공",
    "保养工": "보양공",
    "拆除工": "철거공",
    "防水": "방수공",
    "防水工": "방수공",
    "砌墙": "조적공",
    "砌墙工": "조적공",
    "金屬": "금속공",
    "金属": "금속공",
    "金属工": "금속공",
    "轻钢工": "경량철골공",
    "暖通空调工": "냉난방공조공",
    "暖通空调": "냉난방공조공",
    "风管（新风，排风)": "덕트공(급기·배기)",
    "风管(新风,排风)": "덕트공(급기·배기)",
    "风管": "덕트공",
    "风管工": "덕트공",
    "消防工": "소방공",
    "脚手架工": "비계공",
    "保温": "단열공",
    "保温工": "단열공",
    "水工": "배관공(수도공)",
    "油漆工": "도장공(페인트공)",
    "保洁工": "청소공",
    "保洁": "청소공",
    "玻璃工": "유리공",
    "小工": "조무공(잡부)",
    "杂工": "잡부",
    "打压工": "압력 시험공",
    "打孔工": "코어 타공공",
    "打孔": "코어 타공",

    # 시공 내용 번역 (WORK_KR 기반)
    "现场清理": "현장청소/폐기물처리",
    "建筑垃圾清运": "건축폐기물 반출",
    "弹线": "먹매김",
    "墨线作业": "먹매김 작업",
    "现场弹线": "현장 먹매김",
    "拆除": "철거/해체",
    "室内外冷暖空调管道施工": "실내외 냉난방 에어컨 배관 시공",
    "消防管道施工": "소방 배관 시공",
    "给水管道施工": "급수 배관 시공",
    "天花 / 墙体 / 地面配管作业": "천장 / 벽체 / 바닥 배관 작업",
    "厨房地沟制作 / 灯箱制作安装 / 轻钢龙骨修整": "주방 트렌치 제작 / 라이트박스 제작 설치 / 경량철골 천정틀 보수",
    "地面排风施工": "바닥 배기 시공",
    "现场勘查，图纸/甲供材料数量核算": "현장 실사, 도면 및 지급자재 수량 정산",
    "现场协调 / 翻译资料": "현장 조율 / 번역 자료",
    "瓷砖搬运": "타일 양중(반입)",
    "隔墙石膏板施工": "경량벽체 석고보드 시공",
    "金属作业": "금속 작업",
    "木工作业": "목공 작업",
    "防水作业": "방수 작업",
    "给排水设备作业": "급배수 설비 작업",
    "电气作业": "전기 작업",
    "风管作业": "덕트 작업",
    "消防作业": "소방 작업",

    # 전문 용어 번역 (TERM_MAP 기반)
    "拆除材料": "해체자재",
    "拆除单位": "철거업체",
    "拆墙": "벽체 철거",
    "拆掉": "해체",
    "楼板": "바닥 슬래브",
    "开洞": "코어 천공",
    "结构图纸": "구조도면",
    "结构": "구조체",
    "钢筋": "철근",
    "混凝土": "콘크리트",
    "预埋件": "매립철물",
    "隔油池": "그리스트랩",
    "地沟篦子": "배수 트렌치 격자뚜껑",
    "地沟": "바닥 트렌치",
    "地漏": "바닥 배수구",
    "砌筑": "블록 조적",
    "隔墙": "경량벽체",
    "墙体": "벽체",
    "砖": "벽돌(ALC블록)",
    "加气砖": "ALC 블록",
    "水泥": "시멘트",
    "抹灰": "미장",
    "刮腻子": "퍼티 미장",
    "石膏": "석고",
    "放线施工": "먹매김 시공",
    "放线": "먹매김(먹놓기)",
    "먹작업": "먹작업",
    "弹线": "먹줄 놓기",
    "尺寸差": "치수 차이",
    "尺寸不符": "치수 불일치",
    "尺寸": "치수",
    "复尺": "실측",
    "标注": "치수기입",
    "防水涂料": "방수도막",
    "防水高度": "방수 높이",
    "闭水试验": "방수 담수시험",
    "闭水": "담수 시험",
    "漏水": "누수",
    "冷热水供水问题": "냉온수 급수 문제",
    "冷热水": "냉온수 배관",
    "给排水": "급배수",
    "排水": "배수배관",
    "给水": "급수배관",
    "管道": "배관",
    "水管": "수도배관",
    "供水": "급수",
    "管井": "배관 샤프트(PS)",
    "PIPE SHAFT": "배관 샤프트",
    "螺旋风管": "스파이럴 덕트",
    "风管": "덕트",
    "电线桥架": "전선 케이블 트레이",
    "电线管": "전선관",
    "电气问题": "전기설비 문제",
    "电气": "전기설비",
    "电线": "전선",
    "布线": "배선",
    "电箱": "분전반",
    "配电": "배전",
    "桥架盖板": "케이블 트레이 덮개",
    "桥架": "케이블 트레이",
    "线管": "전선관(CD관)",
    "变压器": "변압기",
    "灯带": "LED 간접조명",
    "钢管": "금속 전선관(EMT)",
    "软管": "플렉시블 전선관",
    "调光功能": "디밍 제어 기능",
    "调光": "디밍 제어",
    "灯光": "조명",
    "消防法规": "소방법규",
    "消防审批": "소방 인허가",
    "消防图纸": "소방도면",
    "消防要求": "소방 규정",
    "消防演习": "소방훈련",
    "消防门": "비상구(방화문)",
    "消防": "소방설비",
    "防火门": "방화문",
    "防火卷帘": "방화셔터",
    "防火板收口条": "방화판 마감 몰딩",
    "防火板": "방화판(불연보드)",
    "防火分区": "방화구획",
    "防火": "방화",
    "排烟罩": "주방 후드(배기 후드)",
    "排烟窗": "배연창",
    "排烟": "배연설비",
    "喷淋图纸": "스프링클러 도면",
    "喷淋": "스프링클러",
    "灭火": "소화",
    "火灾": "화재",
    "新风机防止冬季冻坏": "전열교환기 겨울 동파 방지",
    "新风机": "전열교환기(HRV)",
    "新风": "환기(전열교환기)",
    "空调": "에어컨",
    "排风管道": "배기 덕트",
    "排风": "배기",
    "通风": "환기",
    "风机": "송풍기",
    "风压": "정압",
    "静压": "정압(Static Pressure)",
    "防冻": "동파 방지",
    "燃气热水器": "가스보일러",
    "燃气公司": "가스회사",
    "燃气量": "가스 공급량",
    "燃气": "도시가스",
    "热水器房间": "보일러실",
    "热水器": "보일러",
    "锅炉": "보일러",
    "氧气不足": "산소 부족",
    "氧气": "산소",
    "燃烧": "연소",
    "熄火": "화염 꺼짐",
    "天花板样子": "천장 형상",
    "天花板": "천장 슬래브",
    "天花灯光": "천장 조명",
    "天花上部": "천장 상부",
    "天花": "천장(반자)",
    "吊顶": "달대 천장",
    "铝方通": "알루미늄 루버 천장",
    "铝隔扇": "알루미늄 그릴 천장",
    "格栅贴图": "그릴 마감재",
    "格栅": "그릴 천장",
    "石膏板": "석고보드",
    "地面": "바닥",
    "石材类": "석재류",
    "石材": "석재",
    "踢脚线": "걸레받이",
    "走廊宽度": "복도 폭",
    "走廊": "복도",
    "不锈钢架子": "SUS 프레임",
    "不锈钢明细": "SUS 내역서",
    "不锈钢到顶": "SUS 천장까지 시공",
    "不锈钢家具": "SUS 가구",
    "不锈钢": "스테인리스 스틸(SUS)",
    "木家具": "목재 가구",
    "高柜": "키 큰 장(톨 캐비닛)",
    "矮柜": "낮은 수납장",
    "家具": "가구(FF&E)",
    "收口条": "마감 몰딩",
    "收口": "마감 처리",
    "封板条": "마감 띠장",
    "贴膜": "필름 시공",
    "模型": "시공 목업(모형)",
    "图纸交底": "도면 설명회",
    "图纸问题回复": "도면 문의 회신",
    "图纸问题": "도면 문제",
    "图纸": "도면",
    "设计变更": "설계 변경",
    "设计师": "설계사",
    "设计": "설계",
    "变更内容": "변경 내용",
    "变更": "설계 변경(VE)",
    "深化图": "시공 상세도(Shop DWG)",
    "效果图": "투시도(렌더링)",
    "效果方案": "디자인 시안",
    "平面图": "평면도",
    "建筑图纸": "건축도면",
    "建筑图面": "건축도",
    "建筑图": "건축도면",
    "装饰图纸": "인테리어 도면",
    "装饰平面图": "인테리어 평면도",
    "装饰": "인테리어",
    "云线标注": "구름표시 표기",
    "云线": "구름 표시(변경 마크)",
    "蓝线": "청색선",
    "黑色": "검은색",
    "材料清单": "자재 내역서(BOM)",
    "甲供材料": "발주처 지급자재",
    "甲供品": "발주처 지급품",
    "材料": "자재",
    "计划单数量": "발주 요청 수량",
    "计划单": "발주 요청서",
    "下单": "발주",
    "订单": "주문서",
    "样品": "시공 샘플",
    "剩余的": "잔여",
    "重复下单": "중복 발주",
    "重复": "중복",
    "加工制作": "가공 제작",
    "玻璃": "유리",
    "镜子": "거울",
    "窗台设计方案": "창대 설계안",
    "窗台": "창대",
    "验收": "검수(검사)",
    "确认好": "확인 완료",
    "确认下": "확인 요청",
    "再确认": "재확인",
    "确认后": "확인 후",
    "确认": "확인",
    "核对": "대조 확인",
    "核实": "검토 확인",
    "检查": "점검",
    "施工进度": "시공 진도",
    "施工时间": "시공 시간",
    "施工日志": "시공일지",
    "施工完成后": "시공 완료 후",
    "施工": "시공",
    "现场确认": "현장 확인",
    "现场进度问题": "현장 진도 문제",
    "现场": "현장",
    "工地": "공사현장",
    "楼主协调": "건물주 협의",
    "楼主要求": "건물주 요구",
    "楼主": "건물주(오너)",
    "管理室的要求": "관리사무소 요구",
    "管理室": "관리사무소",
    "总包所有": "원청 전체",
    "总包": "원청(종합건설)",
    "噪音施工": "소음 공사",
    "门迎区": "고객 대기구역",
    "等候区": "대기 공간",
    "奶茶吧": "음료 바(드링크바)",
    "储物间": "창고",
    "男卫生间": "남자 화장실",
    "女卫生间": "여자 화장실",
    "后堂": "후방(BOH)",
    "后厨": "주방(BOH)",
    "门店端": "매장측",
    "门店": "매장",
    "变脸区域": "변검 퍼포먼스 구역",
    "宠物区": "펫존",
    "富川工地": "부천 공사현장",
    "富川铝方通": "부천점 알루미늄 루버",
    "富川": "부천점(기 시공점)",
    "新五店": "영등포점",
    "12店": "12호점",
    "进货口": "반입구",
    "进货": "자재 반입",
    "扶梯位置": "에스컬레이터 위치",
    "扶梯": "에스컬레이터",
    "电梯拆除材料": "에스컬레이터 해체자재",
    "废电梯材料": "폐 에스컬레이터 자재",
    "马桶": "양변기",
    "座椅": "좌석",
    "卡座內": "부스좌석 내",
    "卡座": "부스 좌석",
    "洗碗间排烟罩": "세척실 배기후드",
    "刷碗机": "식기세척기",
    "签证": "설계 변경 승인서",
    "背景音乐": "배경음악",
    "地排": "바닥 배기",
    "地下不用": "지하는 불필요",
}

def translate_text(text):
    if not text or not text.strip():
        return text
    
    # 1. 완벽 매칭 확인
    cleaned = text.strip()
    if cleaned in TRANSLATION_MAP:
        return TRANSLATION_MAP[cleaned]
        
    # 2. 부분 단어 치환 (긴 단어 순)
    sorted_keys = sorted(TRANSLATION_MAP.keys(), key=lambda x: len(x), reverse=True)
    res = text
    for key in sorted_keys:
        if key in res:
            res = res.replace(key, TRANSLATION_MAP[key])
            
    # 3. 추가적인 특수 규칙 치환 (인원수, 날짜)
    res = re.sub(r'(\d+)\s*人', r'\1명', res)
    res = re.sub(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', r'\1년 \2월 \3일', res)
    res = re.sub(r'（(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日）', r'(\1년 \2월 \3일)', res)
    
    return res

def translate_pdf_file(in_path, out_path):
    try:
        doc = fitz.open(in_path)
    except Exception as e:
        print(f"  ❌ PDF 열기 실패 {in_path}: {e}")
        return False

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        blocks = page.get_text("dict")["blocks"]
        
        redact_requests = []
        
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                spans = line["spans"]
                if not spans:
                    continue
                
                # Sort spans horizontally by their X coordinate
                spans = sorted(spans, key=lambda s: s["bbox"][0])
                
                # Group/merge spans that are extremely close horizontally (gap < 2.0 pt)
                merged_spans = []
                curr = dict(spans[0])
                curr_orig_spans = [spans[0]]
                
                for s in spans[1:]:
                    gap = s["bbox"][0] - curr["bbox"][2]
                    if gap < 2.0:
                        curr["text"] += s["text"]
                        curr["bbox"] = [
                            curr["bbox"][0],
                            min(curr["bbox"][1], s["bbox"][1]),
                            max(curr["bbox"][2], s["bbox"][2]),
                            max(curr["bbox"][3], s["bbox"][3])
                        ]
                        curr_orig_spans.append(s)
                    else:
                        merged_spans.append((curr, curr_orig_spans))
                        curr = dict(s)
                        curr_orig_spans = [s]
                merged_spans.append((curr, curr_orig_spans))
                
                # Translate merged spans
                for m_span, orig_list in merged_spans:
                    original_text = m_span["text"]
                    translated = translate_text(original_text)
                    
                    if translated != original_text:
                        # Redact all individual original spans that made up this merged span
                        rects_to_redact = [fitz.Rect(s["bbox"]) for s in orig_list]
                        
                        # Font properties from the first original span
                        first_orig = orig_list[0]
                        fs = first_orig["size"]
                        
                        col = first_orig["color"]
                        r = ((col >> 16) & 255) / 255.0
                        g = ((col >> 8) & 255) / 255.0
                        b = (col & 255) / 255.0
                        
                        redact_requests.append({
                            "rects": rects_to_redact,
                            "translated": translated,
                            "origin": first_orig["origin"],
                            "size": fs,
                            "color": (r, g, b)
                        })
                        
        # Apply redactions and insert translated text
        if redact_requests:
            for r in redact_requests:
                for rect in r["rects"]:
                    page.add_redact_annot(rect, fill=(1, 1, 1))
            page.apply_redactions()
            
            # Insert Korean font (must be done after apply_redactions)
            try:
                page.insert_font(fontname="KoreanFont", fontfile=FONT_PATH, set_simple=False)
            except Exception as e:
                print(f"  ❌ Font insertion failed on page {page_idx+1}: {e}")
                doc.close()
                return False
            
            # Insert the translated Korean text
            for r in redact_requests:
                point = fitz.Point(r["origin"][0], r["origin"][1])
                page.insert_text(
                    point, 
                    r["translated"], 
                    fontname="KoreanFont",
                    fontsize=r["size"], 
                    color=r["color"]
                )
                
    try:
        doc.save(out_path)
        doc.close()
        return True
    except Exception as e:
        print(f"  ❌ PDF 저장 실패 {out_path}: {e}")
        try: doc.close()
        except: pass
        return False

def rename_and_translate_all():
    print("🚀 기존 PDF 파일 및 내용 한글화 작업 시작...")
    
    if not os.path.exists(PDF_DIR):
        print(f"❌ PDF 디렉토리가 없습니다: {PDF_DIR}")
        return
        
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    pdf_files.sort()
    
    print(f"📂 총 {len(pdf_files)}개 PDF 파일 감지")
    
    rename_mapping = {}
    
    for fname in pdf_files:
        old_path = os.path.join(PDF_DIR, fname)
        
        # 새 파일명 결정
        # 예: 2026-04-16_海底捞韩国永登浦店项目施工日志-20260416.pdf -> 2026-04-16_하이디라오 한국 영등포점 프로젝트 시공일지-20260416.pdf
        new_name = fname.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지")
        # 중복 .pdf.pdf 정리
        new_name = new_name.replace(".pdf.pdf", ".pdf")
        
        new_path = os.path.join(PDF_DIR, new_name)
        
        print(f"📄 처리 중: {fname} -> {new_name}")
        
        # PDF 내용 번역 후 임시 저장 후 교체
        temp_path = os.path.join(PDF_DIR, "temp_" + new_name)
        success = translate_pdf_file(old_path, temp_path)
        
        if success:
            # 기존 파일 삭제
            os.remove(old_path)
            # 임시 파일을 한글화된 새 파일로 이름 변경
            os.rename(temp_path, new_path)
            rename_mapping[fname] = new_name
            print(f"   ✅ 성공적으로 번역 및 이름 변경 완료!")
        else:
            print(f"   ❌ 번역 및 이름 변경 실패!")
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    # 2. JSON 데이터 파일 업데이트
    if os.path.exists(DATA_FILE) and rename_mapping:
        print("\n📝 작업일지_데이터.json 업데이트 중...")
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        data["project"] = "하이디라오 영등포점 (하이디라오 한국 영등포점 프로젝트)"
        
        updated_count = 0
        for log_entry in data.get("logs", []):
            old_fname = log_entry.get("file_name", "")
            old_pdf_file = log_entry.get("pdf_file", "")
            
            # file_name 한글화
            if old_fname:
                new_fname = old_fname.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지").replace(".pdf.pdf", ".pdf")
                log_entry["file_name"] = new_fname
                
            # pdf_file 한글화
            if old_pdf_file in rename_mapping:
                log_entry["pdf_file"] = rename_mapping[old_pdf_file]
                updated_count += 1
            elif old_pdf_file:
                new_pdf_file = old_pdf_file.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지").replace(".pdf.pdf", ".pdf")
                log_entry["pdf_file"] = new_pdf_file
                updated_count += 1
                
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 작업일지_데이터.json 업데이트 완료 ({updated_count}개 참조 수정)")
        
        # 3. HTML 파일 업데이트
        if os.path.exists(HTML_FILE):
            print("\n🌐 하이디라오_작업일지.html 업데이트 중...")
            with open(HTML_FILE, 'r', encoding='utf-8') as f:
                html = f.read()
                
            js_data = json.dumps(data, ensure_ascii=False)
            js_data = js_data.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n')
            escaped_js_data = js_data.replace('\\', '\\\\')
            
            new_html, count = re.subn(
                r'const WORK_LOGS = \{.*?\};',
                f'const WORK_LOGS = {escaped_js_data};',
                html, count=1, flags=re.DOTALL
            )
            
            if count > 0:
                with open(HTML_FILE, 'w', encoding='utf-8') as f:
                    f.write(new_html)
                print("✅ 하이디라오_작업일지.html 업데이트 완료!")
            else:
                print("⚠️ HTML에서 WORK_LOGS 패턴을 찾지 못해 업데이트 실패")
                
    print("\n🏁 모든 파일 한글화 및 참조 업데이트 완료!")

if __name__ == "__main__":
    rename_and_translate_all()
