import sys, os, docx
from pathlib import Path
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
PROJECT = Path(__file__).resolve().parents[2]
SRC = PROJECT / 'student-package' / 'pbl-high-dimension-reduction-student-worksheet.docx'
d = docx.Document(SRC)
from collections import Counter
jc = Counter(); va = Counter(); ind = Counter()
for ti, t in enumerate(d.tables):
    for row in t.rows:
        for c in row.cells:
            tcpr = c._tc.find(qn('w:tcPr'))
            v = tcpr.find(qn('w:vAlign')) if tcpr is not None else None
            va[(v.get(qn('w:val')) if v is not None else None)] += 1
            for p in c.paragraphs:
                ppr = p._p.find(qn('w:pPr'))
                j = ppr.find(qn('w:jc')) if ppr is not None else None
                jc[(j.get(qn('w:val')) if j is not None else 'default')] += 1
                i = ppr.find(qn('w:ind')) if ppr is not None else None
                ind[(i.attrib.get(qn('w:firstLineChars')) if i is not None else 'none', i.attrib.get(qn('w:firstLine')) if i is not None else None)] += 1
print('cell vAlign:', va)
print('table paragraph jc:', jc)
print('table paragraph ind:', ind)
bjc = Counter(); bind = Counter()
for p in d.paragraphs:
    ppr = p._p.find(qn('w:pPr'))
    j = ppr.find(qn('w:jc')) if ppr is not None else None
    bjc[(j.get(qn('w:val')) if j is not None else 'default')] += 1
    i = ppr.find(qn('w:ind')) if ppr is not None else None
    bind[(i.attrib.get(qn('w:firstLineChars')) if i is not None else 'none', i.attrib.get(qn('w:firstLine')) if i is not None else None)] += 1
print('body paragraph jc:', bjc)
print('body paragraph ind:', bind)
print('styles used:', Counter(p.style.name for p in d.paragraphs))
s = d.styles['Normal']
print('Normal font', s.font.name, s.font.size, 'east asia', s.element.rPr.rFonts.get(qn('w:eastAsia')) if s.element.rPr is not None and s.element.rPr.rFonts is not None else None)
