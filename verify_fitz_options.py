import os
import fitz

BASE_DIR  = '/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결'
PDF_PATH  = os.path.join(BASE_DIR, '일일작업일보', '2026-06-17_하이디라오 한국 영등포점 프로젝트 시공일지-20260617.pdf')

def test_blocks():
    doc = fitz.open(PDF_PATH)
    page = doc[0]
    blocks = page.get_text("blocks")
    print("ALL BLOCKS:")
    for b in sorted(blocks, key=lambda x: (x[1], x[0])):
        x0, y0, x1, y1, text, block_no, block_type = b
        print(f"  y={y0:.2f}, x={x0:.2f} -> {repr(text.strip())}")
    doc.close()

if __name__ == '__main__':
    test_blocks()
