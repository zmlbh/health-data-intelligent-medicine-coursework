
import sys
from pptx import Presentation
sys.stdout.reconfigure(encoding='utf-8')
p = Presentation('homework3/student-package/pbl-instruction.pptx')
print('slides', len(p.slides))
for i, s in enumerate(p.slides):
    txt = []
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            txt.append(sh.text_frame.text.strip().replace('\n', ' | '))
    if txt:
        print('--- slide', i, '---')
        for t in txt:
            print('   ', t[:500])

