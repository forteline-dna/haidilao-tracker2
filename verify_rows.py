import os, re
import fitz

BASE_DIR  = '/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결'
PDF_PATH  = os.path.join(BASE_DIR, '일일작업일보', '2026-06-17_하이디라오 한국 영등포점 프로젝트 시공일지-20260617.pdf')

def analyze_pdf():
    doc = fitz.open(PDF_PATH)
    page = doc[0]
    blocks = page.get_text('dict')['blocks']
    items = []
    for b in blocks:
        for line in b.get('lines', []):
            text = ''.join(sp['text'] for sp in line.get('spans', [])).strip()
            if text:
                x1, y1, x2, y2 = line['bbox']
                items.append({'x': x1, 'y': y1, 'text': text})
    items.sort(key=lambda v: (v['y'], v['x']))
    
    print("ALL TEXT ITEMS SORTED BY Y:")
    for it in items[:60]:
        print(f"  y={it['y']:.2f}, x={it['x']:.2f} -> {it['text']}")

if __name__ == '__main__':
    analyze_pdf()
