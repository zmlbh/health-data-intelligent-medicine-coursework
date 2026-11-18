import sys, os, docx, zipfile, re, importlib.util
from pathlib import Path
from collections import Counter
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
PROJECT = Path(__file__).resolve().parents[2]
BASE = PROJECT / 'student-package' / 'pbl-high-dimension-reduction-student-worksheet.docx'
OUT = PROJECT / 'analysis' / 'deliverable' / 'pbl-high-dimension-reduction-student-worksheet-completed.docx'
spec = importlib.util.spec_from_file_location('fw', PROJECT / 'analysis' / 'scripts' / 'fill_worksheet.py')
fw = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw)
ANS = fw.ANSWERS
a, b = docx.Document(BASE), docx.Document(OUT)
print('tables', len(a.tables), '->', len(b.tables), '| body paras', len(a.paragraphs), '->', len(b.paragraphs))

# --- blank writing lines: only the ones inside filled cells may disappear ---
def br_in_cell(cell):
    return len(cell._tc.findall('.//'+qn('w:br')))
br_base_total = len(a.element.body.findall('.//'+qn('w:br')))
br_out_total = len(b.element.body.findall('.//'+qn('w:br')))
br_filled = sum(br_in_cell(a.tables[ti].rows[r].cells[c]) for ti, cs in ANS.items() for (r, c) in cs)
br_filled_out = sum(br_in_cell(b.tables[ti].rows[r].cells[c]) for ti, cs in ANS.items() for (r, c) in cs)
print('w:br total', br_base_total, '->', br_out_total)
print('w:br inside filled answer cells', br_filled, '->', br_filled_out, '(expected 0)')
print('w:br outside filled cells (must be unchanged):', br_base_total - br_filled, '->', br_out_total - br_filled_out)

REF = [0,1,2,3]+list(range(11,14))+list(range(16,19))+list(range(22,24))+list(range(26,30))+list(range(33,36))+[39]
def cells(t): return [[c.text for c in r.cells] for r in t.rows]
bad = [i for i in REF if cells(a.tables[i]) != cells(b.tables[i])]
print('reference tables whose TEXT changed:', bad)

# --- filled cells: exactly one paragraph, no blanks, answer present ---
issues = []
for ti, cs in ANS.items():
    for (r, c) in cs:
        cell = b.tables[ti].rows[r].cells[c]
        ps = [p for p in cell.paragraphs]
        if len(ps) != 1: issues.append(('paras', ti, r, c, len(ps)))
        for p in ps:
            if not p.text.strip(): issues.append(('empty', ti, r, c))
            if p._p.findall('.//'+qn('w:br')): issues.append(('br', ti, r, c))
        if ANS[ti][(r, c)][:10] not in cell.text: issues.append(('missing', ti, r, c))
        if re.search(r' {2,}|\u3000', cell.text): issues.append(('space', ti, r, c))
print('filled-cell issues:', issues)

# --- alignment properties ---
va = Counter(); jcl = Counter(); indc = Counter()
empty = []
for ti, t in enumerate(b.tables):
    for ri, row in enumerate(t.rows):
        for ci, c in enumerate(row.cells):
            tcpr = c._tc.find(qn('w:tcPr'))
            v = tcpr.find(qn('w:vAlign'))
            va[v.get(qn('w:val')) if v is not None else None] += 1
            for p in c.paragraphs:
                ppr = p._p.find(qn('w:pPr'))
                j = ppr.find(qn('w:jc')) if ppr is not None else None
                jcl[j.get(qn('w:val')) if j is not None else 'default'] += 1
                i2 = ppr.find(qn('w:ind')) if ppr is not None else None
                indc[i2.attrib.get(qn('w:firstLineChars')) if i2 is not None else 'none'] += 1
            if ti not in REF and ri > 0 and not c.text.replace(chr(10), '').strip():
                empty.append((ti, ri, ci))
print('cell vAlign:', dict(va))
print('cell paragraph jc:', dict(jcl))
print('cell paragraph ind:', dict(indc))
print('answer cells still empty:', empty)
tj = [i for i, t in enumerate(b.tables) if t._tbl.tblPr.find(qn('w:jc')) is not None]
print('tables with tblPr/jc:', len(tj), '/', len(b.tables))

bj = Counter(); bi = Counter()
for p in b.paragraphs:
    ppr = p._p.find(qn('w:pPr'))
    j = ppr.find(qn('w:jc')) if ppr is not None else None
    bj[(p.style.name, j.get(qn('w:val')) if j is not None else 'default')] += 1
    i2 = ppr.find(qn('w:ind')) if ppr is not None else None
    bi[(p.style.name, i2.attrib.get(qn('w:firstLineChars')) if i2 is not None else 'none')] += 1
print('body paragraph jc:', dict(bj))
print('body paragraph ind:', dict(bi))
