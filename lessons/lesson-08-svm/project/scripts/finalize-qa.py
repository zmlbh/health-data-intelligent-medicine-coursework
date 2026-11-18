"""Verify final release artifacts and record hashes; no document authoring here.

Run after: pbl-svm-margin-build.py, qa-artifacts.py notebook, the pilot fill (review/pilot-fields.json +
worksheet_check.py apply) and render-word.ps1 -IncludeReleases. Every number written here is recomputed
from the artifacts, so a rebuild that invalidates the pilot or the renders makes this script fail.
"""
from pathlib import Path
import hashlib,json
import nbformat,pypdfium2
from docx import Document
ROOT=Path(__file__).resolve().parents[1]
slug='pbl-svm-margin'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(ROOT/'package-manifest.json');design=read(ROOT/m['analysis_design'])
for name in list(m['outputs'].values())+m['assets']+m['student_release']:
    assert (ROOT/name).is_file(),name
for report in ['lint','design-check']:
    text=(ROOT/'review'/f'{slug}-{report}.md').read_text(encoding='utf-8')
    assert 'Errors: **0**' in text and 'Warnings: **0**' in text,report
# The pilot must belong to the current worksheet: same fields, same prompts.
import subprocess,sys,tempfile
skill=ROOT.parents[2]/'.codex'/'skills'/'pbl-ml-package'/'scripts'/'worksheet_check.py'
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable,str(skill),'extract',str(ROOT/f'{slug}-student-worksheet.docx'),'-o',tmp+'/f.json'],check=True,capture_output=True)
    fresh=read(Path(tmp)/'f.json')['fields']
fields=read(ROOT/'review'/'pilot-fields.json')['fields']
assert [(f['id'],f['prompt']) for f in fields]==[(f['id'],f['prompt']) for f in fresh],'pilot-fields.json is stale; re-run the pilot'
assert all(f['answer'] and isinstance(f['minutes'],(int,float)) for f in fields)
blocking=[f['id'] for f in fields for b in f['blockers'] if b['severity']=='block']
friction=[f['id'] for f in fields for b in f['blockers'] if b['severity']!='block']
assert not blocking,blocking
def phase(f):
    if f['part'].startswith('Phase 1') or f.get('row_label')=='T0 初选':return 'phase1'
    if f['part'].startswith('Phase 3'):return 'phase3_writing'
    return 'phase2'
minutes={}
for f in fields:minutes[phase(f)]=minutes.get(phase(f),0)+f['minutes']
minutes={k:round(v,1) for k,v in minutes.items()}
budget=design['time_budget']
timing={'phase1':[minutes['phase1'],budget['phase1']],'phase2':[minutes['phase2'],budget['phase2']],'phase3_writing':[minutes['phase3_writing'],budget['phase3']]}
assert abs(minutes['phase1']/budget['phase1']-1)<=.2 and abs(minutes['phase2']/budget['phase2']-1)<=.2 and minutes['phase3_writing']<=budget['phase3']
nbpath=ROOT/m['outputs']['notebook'];nb=nbformat.read(nbpath,as_version=4)
cells=[c for c in nb.cells if c.cell_type=='code']
assert cells and all(c.execution_count is not None for c in cells),'notebook not executed'
assert not any(o.output_type=='error' for c in cells for o in c.outputs)
docs=[ROOT/p for p in m['outputs'].values() if p.endswith('.docx')]
pages={}
for p in docs+[ROOT/x for x in m['student_release']]:
    d=Document(p);assert d.paragraphs and (d.tables or p.name.endswith('-design-rationale.docx'))
    pdf_path=ROOT/'review'/'rendered'/(p.stem+'.pdf')
    assert pdf_path.stat().st_mtime>=p.stat().st_mtime,'render older than '+p.name
    pdf=pypdfium2.PdfDocument(pdf_path)
    pages[p.name]=len(pdf)
    assert all(len(page.get_textpage().get_text_range().strip())>15 for page in pdf),'Blank page: '+p.name
checks=dict(lint_errors=0,lint_warnings=0,design_errors=0,design_warnings=0,
    pilot_mode='self-pilot',pilot_fields=len(fields),pilot_answered=sum(bool(f['answer']) for f in fields),pilot_blocking=len(blocking),pilot_friction=len(friction),
    timing=timing,executed_notebook_cells=len(cells),pages=pages,renderer='Microsoft Word + pypdfium2',
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in docs+[nbpath,ROOT/'review'/'pilot-fields.json',ROOT/'scripts'/(slug+'-build.py')]})
(ROOT/'review'/'release-verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
m['qa'].update(status='passed',verification='review/release-verification.json',visual='review/visual-qa.md',independence='self-pilot',student_fields=len(fields),pilot_blocking=len(blocking),pilot_friction=len(friction),executed_notebook_cells=len(cells))
(ROOT/'package-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
