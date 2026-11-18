import docx, sys, io
sys.stdout.reconfigure(encoding='utf-8')
p = r'homework3\student-package\pbl-high-dimension-reduction-student-worksheet.docx'
d = docx.Document(p)
print('PARAGRAPHS', len(d.paragraphs), 'TABLES', len(d.tables))
# iterate body in document order
from docx.oxml.ns import qn
body = d.element.body
ti = 0; pi = 0
def para_under(p):
    return any(r.underline for r in p.runs)
out=[]
for child in body.iterchildren():
    if child.tag == qn('w:p'):
        par = docx.text.paragraph.Paragraph(child, d)
        txt = par.text
        u = para_under(par)
        if txt.strip() or u:
            out.append(('P%d%s' % (pi, ' [U]' if u else ''), par.style.name, txt))
        pi += 1
    elif child.tag == qn('w:tbl'):
        t = docx.table.Table(child, d)
        out.append(('TABLE#%d' % ti, '%dx%d' % (len(t.rows), len(t.columns)), ''))
        for ri, row in enumerate(t.rows):
            cells = [c.text.replace(chr(10), ' / ') for c in row.cells]
            out.append(('', 'r%d' % ri, ' | '.join(cells)))
        ti += 1
io.open(r'homework3\_work\worksheet_dump.txt','w',encoding='utf-8').write(
    chr(10).join('%s\t%s\t%s' % x for x in out))
print('dumped', len(out))
