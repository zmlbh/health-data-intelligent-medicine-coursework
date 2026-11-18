
import docx, sys, io
sys.stdout.reconfigure(encoding='utf-8')
d = docx.Document('homework3/student-package/plan.docx')
out=[]
from docx.oxml.ns import qn
ti=0
for child in d.element.body.iterchildren():
    if child.tag==qn('w:p'):
        p=docx.text.paragraph.Paragraph(child,d)
        if p.text.strip(): out.append('[%s] %s'%(p.style.name,p.text))
    elif child.tag==qn('w:tbl'):
        t=docx.table.Table(child,d)
        out.append('TABLE#%d'%ti)
        for row in t.rows:
            out.append('   | '+' | '.join(c.text.replace(chr(10),' / ') for c in row.cells))
        ti+=1
print(chr(10).join(out))

