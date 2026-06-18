import json, os

BASE_DIR  = '/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결'
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')

def verify_data():
    with open(DATA_FILE, encoding='utf-8') as f:
        data = json.load(f)
    
    logs = {l['log_date']: l for l in data['logs']}
    
    dates_to_check = ['2026-06-17', '2026-05-20']
    for dt in dates_to_check:
        if dt not in logs:
            print(f"❌ {dt} 데이터가 없습니다.")
            continue
        
        log = logs[dt]
        print(f"\n📅 날짜: {dt}")
        print(f"  총 인원: {log.get('total_workers')}명")
        print("  공종별 상세 작업내용:")
        details = log.get('trade_work_details', {})
        for t, info in details.items():
            print(f"    - {t} ({info.get('count')}명): {info.get('work')}")
            
if __name__ == '__main__':
    verify_data()
