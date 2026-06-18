import os, re, sys
import fitz

BASE_DIR  = '/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결'
PDF_DIR   = os.path.join(BASE_DIR, '일일작업일보')

def parse_pdf_trades(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        page = doc[0]
        full = page.get_text()
        blocks = page.get_text('dict')['blocks']
        items = []
        for b in blocks:
            for line in b.get('lines', []):
                text = ''.join(sp['text'] for sp in line.get('spans', [])).strip()
                if text:
                    x1, y1, x2, y2 = line['bbox']
                    items.append({'x': x1, 'y': y1, 'text': text})
        items.sort(key=lambda v: (round(v['y'] / 4) * 4, v['x']))
        doc.close()
    except Exception as e:
        return []

    table_start_y = None
    table_end_y   = None
    for it in items:
        if '工种' in it['text'] and it['x'] < 200:
            table_start_y = it['y']
        if '今日施工人数总计' in it['text'] or '施工人数总计' in it['text']:
            table_end_y = it['y']
            break

    trades = []
    if table_start_y is not None:
        left_items = [
            it for it in items
            if it['x'] < 250
            and (table_start_y - 5) < it['y'] < (table_end_y or 9999)
            and it['text'] not in ('工种', '人数', '今日施工内容', '施工日志')
        ]
        for it in left_items:
            t = it['text'].strip()
            if not t:
                continue
            if not re.match(r'^\d+$', t) and not re.match(r'^\d+\s*人$', t):
                trades.append(t)
    return trades

def main():
    pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    all_raw_trades = set()
    for fname in pdf_files:
        pdf_path = os.path.join(PDF_DIR, fname)
        trades = parse_pdf_trades(pdf_path)
        for t in trades:
            all_raw_trades.add(t)
    print("ALL UNIQUE RAW TRADES IN PDFs:")
    for t in sorted(all_raw_trades):
        print(f"  - {t}")

if __name__ == '__main__':
    main()
