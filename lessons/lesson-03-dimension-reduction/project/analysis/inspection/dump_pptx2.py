
import sys
from pptx import Presentation
from pptx.util import Emu
sys.stdout.reconfigure(encoding='utf-8')
p = Presentation('homework3/student-package/pbl-instruction.pptx')
for i, s in enumerate(p.slides):
    print('slide', i, 'shapes', len(s.shapes))
    for sh in s.shapes:
        print('   ', sh.shape_type, repr(getattr(sh, 'name', ''))[:40],
              'has_tf', sh.has_text_frame)
        if sh.has_text_frame:
            print('        text', repr(sh.text_frame.text)[:300])

