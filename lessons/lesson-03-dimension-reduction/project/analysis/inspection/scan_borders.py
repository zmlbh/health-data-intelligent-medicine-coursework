
import docx, sys, io, zipfile, re
sys.stdout.reconfigure(encoding='utf-8')
PATH='homework3/student-package/pbl-high-dimension-reduction-student-worksheet.docx'
z=zipfile.ZipFile(PATH)
doc=z.read('word/document.xml').decode('utf-8')
print('len', len(doc))
for pat in ['<w:pBdr','<w:bottom','<w:u ','___','<w:tab/>','<w:highlight','<w:shd']:
    print(repr(pat), doc.count(pat))
m=re.findall(r'<w:pBdr>.*?</w:pBdr>', doc)
print('pBdr samples', len(m), m[:2])

