import sys, os
import docx
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'C:\Users\zml\Documents\Codex\2026-09-16\ctrl-cmd-shift-p-python-create-2'
OUT = os.path.join(REPO, 'homework3', 'analysis', 'deliverable', 'pbl-high-dimension-reduction-student-worksheet-completed.docx')
d = docx.Document(OUT)
REF = [0, 1, 2, 3] + list(range(11, 14)) + list(range(16, 19)) + list(range(22, 24)) + list(range(26, 30)) + list(range(33, 36)) + [39]
missing = []
for ti, t in enumerate(d.tables):
    if ti in REF:
        continue
    for ri, row in enumerate(t.rows):
        for ci, c in enumerate(row.cells):
            body = c.text.replace(chr(10), '').strip()
            if ri == 0:
                continue
            if not body:
                missing.append((ti, ri, ci, c.text[:40]))
print('answer cells with NO text:', len(missing))
for m in missing:
    print('  ', m)
print()
print('paragraphs that are not in a table and look like prompts:')
print('total paragraphs', len(d.paragraphs))
