
import docx, sys, io
from docx.oxml.ns import qn
sys.stdout.reconfigure(encoding='utf-8')
PATH='homework3/student-package/pbl-high-dimension-reduction-student-worksheet.docx'
d = docx.Document(PATH)
# count all underline runs incl in tables
def all_paras(doc):
    for p in doc.paragraphs: yield ('body',p)
    for ti,t in enumerate(doc.tables):
        for ri,row in enumerate(t.rows):
            for ci,c in enumerate(row.cells):
                for p in c.paragraphs: yield ('tbl%d.r%d.c%d'%(ti,ri,ci),p)
                for p in c.tables:
                    pass
n=0
for loc,p in all_paras(d):
    u=[r for r in p.runs if r.underline]
    if u:
        n+=1
        print('UND', loc, repr(p.text)[:160])
print('paras with underline runs:', n)
# also count w:u elements anywhere
xml = d.element.body.xml
print('w:u count', xml.count('<w:u '))
print('w:br count', xml.count('<w:br/>'))
print('w:br any', xml.count('<w:br'))

