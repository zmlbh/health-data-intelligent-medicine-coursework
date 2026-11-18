
import docx, sys, io, zipfile, os
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
base = 'homework3/student-package/'
p = base + 'pbl-high-dimension-reduction-evidence-pack.docx'
d = docx.Document(p)
body = d.element.body
out=[]; ti=0; pi=0
for child in body.iterchildren():
    if child.tag == qn('w:p'):
        par = docx.text.paragraph.Paragraph(child, d)
        has_img = bool(child.findall('.//'+qn('w:drawing'))) or bool(child.findall('.//'+qn('w:pict')))
        if par.text.strip() or has_img:
            out.append('P%d%s\t%s\t%s' % (pi, ' [IMG]' if has_img else '', par.style.name, par.text))
        pi += 1
    elif child.tag == qn('w:tbl'):
        t = docx.table.Table(child, d)
        out.append('TABLE#%d\t%dx%d' % (ti, len(t.rows), len(t.columns)))
        for ri, row in enumerate(t.rows):
            out.append('\tr%d\t%s' % (ri, ' | '.join(c.text.replace(chr(10),' / ') for c in row.cells)))
        ti += 1
io.open('homework3/_work/evidence_dump.txt','w',encoding='utf-8').write(chr(10).join(out))
print('evidence dumped', len(out), 'paras', pi, 'tables', ti)
for f in ['pbl-high-dimension-reduction-student-worksheet.docx','pbl-high-dimension-reduction-evidence-pack.docx']:
    z = zipfile.ZipFile(base + f)
    media = [n for n in z.namelist() if n.startswith('word/media/')]
    print(f, 'media:', media)

