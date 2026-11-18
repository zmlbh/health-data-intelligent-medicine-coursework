"""Render exported PDFs or execute the auxiliary notebook, entirely within lesson9."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if sys.argv[1]=='notebook':
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager
    path=ROOT/'notebook'/'pbl-svm-margin-lab.ipynb'
    nb=nbformat.read(path,as_version=4)
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    NotebookClient(nb,km=km,timeout=600,resources={'metadata':{'path':str(path.parent)}}).execute()
    nbformat.write(nb,path)
    assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
    assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    print('Executed',sum(c.cell_type=='code' for c in nb.cells),'code cells without errors.')
elif sys.argv[1]=='render':
    import pypdfium2 as pdfium
    from PIL import Image,ImageOps,ImageDraw
    stats=[]
    for path in (ROOT/'review'/'rendered').glob('*.pdf'):
        dest=path.with_suffix('');dest.mkdir(exist_ok=True)
        pdf=pdfium.PdfDocument(path)
        pages=[]
        for i,page in enumerate(pdf):
            img=page.render(scale=1.5).to_pil().convert('RGB')
            img.save(dest/f'page-{i+1:02d}.png')
            txt=page.get_textpage().get_text_range()
            (dest/f'page-{i+1:02d}.txt').write_text(txt,encoding='utf-8')
            pages.append(img)
            stats.append(dict(document=path.stem,page=i+1,characters=len(txt),width=img.width,height=img.height))
        for start in range(0,len(pages),4):
            sheet=Image.new('RGB',(1000,1456),'#ccd1d6')
            for j,img in enumerate(pages[start:start+4]):
                th=ImageOps.contain(img,(490,695))
                x=(j%2)*500+5;y=(j//2)*728+25
                sheet.paste(th,(x,y));ImageDraw.Draw(sheet).text((x,y-20),f'{path.stem} / {start+j+1}',fill='black')
            sheet.save(dest/f'contact-{start//4+1:02d}.png')
        print(path.stem,len(pages),'pages')
    (ROOT/'review'/'render-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
