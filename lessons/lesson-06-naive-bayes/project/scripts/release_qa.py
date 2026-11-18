"""Execute notebooks and verify/render this lesson without external temp folders."""
from pathlib import Path
import argparse,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/'review'
SLUG='pbl-machine-learning-basics-naive-bayes'
NATIVE=Path(r'C:/Users/qiuha/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')

def render():
    import win32com.client
    # An isolated hidden Word instance; never attach to or close the user's instance.
    app=win32com.client.DispatchEx('Word.Application');app.Visible=False;app.DisplayAlerts=0
    results=[]
    try:
        for file in ROOT.glob(f'{SLUG}-*.docx'):
            out=REVIEW/('render-'+file.stem.removeprefix(SLUG+'-'));out.mkdir(exist_ok=True)
            doc=app.Documents.Open(str(file),ReadOnly=True,AddToRecentFiles=False)
            try:
                doc.Repaginate()
                pages=int(doc.ComputeStatistics(2));pdf=out/(file.stem+'.pdf')
                doc.ExportAsFixedFormat(str(pdf),17)
                results.append({'file':file.name,'pages':pages,'pdf':str(pdf.relative_to(ROOT))})
            finally:doc.Close(False)
            subprocess.run([str(NATIVE/'pdftoppm.exe'),'-scale-to','1300','-png',str(pdf),str(out/'page')],check=True,capture_output=True)
            bundled=r'C:/Users/qiuha/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            extract_code="import sys,json;from pypdf import PdfReader;print(json.dumps([p.extract_text() or '' for p in PdfReader(sys.argv[1]).pages],ensure_ascii=True))"
            per_page=json.loads(subprocess.check_output([bundled,'-c',extract_code,str(pdf)],text=True))
            extracted='\n\f\n'.join(per_page)
            (out/'text.txt').write_text(extracted,encoding='utf-8')
            print(file.name,pages,flush=True)
    finally:app.Quit()
    (REVIEW/'render-summary.json').write_text(json.dumps({'renderer':'Microsoft Word COM isolated instance; PDF exported then bundled Poppler rasterization','preferred_renderer_attempt':'render_docx.py failed: LibreOffice soffice.exe unavailable','documents':results},ensure_ascii=False,indent=2),encoding='utf-8')
    from PIL import Image,ImageOps,ImageDraw
    for item in results:
        out=ROOT/item['pdf'];out=out.parent
        pages=sorted((p for p in out.glob('page-*.png') if int(p.stem.split('-')[-1])<=item['pages']),key=lambda p:int(p.stem.split('-')[-1]))
        for start in range(0,len(pages),6):
            selected=pages[start:start+6];sheet=Image.new('RGB',(1200,2*605),'#d0d0d0');draw=ImageDraw.Draw(sheet)
            for i,p in enumerate(selected):
                im=Image.open(p);im.thumbnail((384,570));x=(i%3)*400+(400-im.width)//2;y=(i//3)*605+25
                sheet.paste(im,(x,y));draw.text(((i%3)*400+10,(i//3)*605+6),p.stem,fill='black')
            sheet.save(out/f'contact-{start//6+1}.png')

def notebook():
    import nbformat
    from nbclient import NotebookClient
    path=ROOT/'notebook'/f'{SLUG}-lab.ipynb'
    nb=nbformat.read(path,as_version=4)
    client=NotebookClient(nb,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(ROOT/'notebook')}})
    client.execute()
    nbformat.write(nb,REVIEW/f'{SLUG}-lab-executed.ipynb')
    errors=[o for c in nb.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
    assert not errors
    (REVIEW/'notebook-execution.json').write_text(json.dumps({'code_cells':sum(c.cell_type=='code' for c in nb.cells),'executed':sum(c.get('execution_count') is not None for c in nb.cells),'errors':len(errors),'execution_cwd':str(ROOT/'notebook'),'runner_python':sys.executable},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Notebook executed without errors.')

def check():
    from docx import Document
    design=json.loads((ROOT/'assets'/SLUG/'analysis-design.json').read_text(encoding='utf-8'))
    for section in ['evidence_items','analyses']:
        for item in design[section]:
            for file in item['artifacts']:assert (ROOT/'assets'/SLUG/file).exists(),file
    checker=Path(r'D:/XMU/AI4BiomedicalDS/.codex/skills/pbl-ml-package/scripts/worksheet_check.py')
    result=subprocess.run([sys.executable,str(checker),'design',str(ROOT/'assets'/SLUG/'analysis-design.json'),'--homework-minutes','120'],capture_output=True,text=True,encoding='utf-8')
    (REVIEW/'design-check.md').write_text(result.stdout+result.stderr,encoding='utf-8');print(result.stdout);assert result.returncode==0
    subprocess.run([sys.executable,str(checker),'lint',str(ROOT/f'{SLUG}-student-worksheet.docx'),'-o',str(REVIEW/f'{SLUG}-lint.md')],check=True)
    for file in ROOT.glob(f'{SLUG}-*.docx'):
        d=Document(file);text='\n'.join([p.text for p in d.paragraphs]+[c.text for t in d.tables for r in t.rows for c in r.cells]);assert '\ufffd' not in text
        print(file.name,len(d.tables),'tables',len(text),'text characters')
    manifest=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
    for file in [*manifest['outputs'].values(),*manifest['assets']]:assert (ROOT/file).exists(),file

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['render','notebook','check']);a=p.parse_args()
    work=REVIEW/'runtime-work';work.mkdir(exist_ok=True)
    os.environ['TEMP']=os.environ['TMP']=str(work)
    if a.mode=='render':render()
    elif a.mode=='notebook':notebook()
    else:check()
