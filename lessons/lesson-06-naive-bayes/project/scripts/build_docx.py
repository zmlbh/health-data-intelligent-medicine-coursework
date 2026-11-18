"""Convert formal Markdown worksheets to printable A4 DOCX using bundled Python."""
from pathlib import Path
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE=Path(__file__).resolve().parents[1]

def clean(text):
    return text.replace('`','').replace('**','')

def make(name):
    doc=Document()
    section=doc.sections[0]
    section.page_width=Cm(21); section.page_height=Cm(29.7)
    section.top_margin=Cm(1.8); section.bottom_margin=Cm(1.8)
    section.left_margin=Cm(1.6); section.right_margin=Cm(1.6)
    for st in ['Normal','Title','Heading 1','Heading 2','Heading 3']:
        style=doc.styles[st]
        style.font.name='Microsoft YaHei'
        style.element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei')
        style.font.color.rgb=RGBColor(0,0,0)
    normal=doc.styles['Normal']; normal.font.size=Pt(10.5)
    normal.paragraph_format.space_after=Pt(6)
    normal.paragraph_format.line_spacing=1.18
    doc.styles['Title'].font.size=Pt(21)
    doc.styles['Heading 1'].font.size=Pt(15)
    doc.styles['Heading 2'].font.size=Pt(12)
    footer=section.footer.paragraphs[0]
    footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run('生物医学数据科学  第7讲  |  ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    lines=(BASE/(name+'.md')).read_text(encoding='utf-8').splitlines()
    i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line: i+=1; continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[clean(c.strip()) for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',x) for x in row):rows.append(row)
                i+=1
            table=doc.add_table(rows=0,cols=len(rows[0])); table.autofit=False
            usable=17.8
            weights=[max(5,min(24,max(len(r[c]) for r in rows))) for c in range(len(rows[0]))]
            for col,w in zip(table.columns,weights):col.width=Cm(usable*w/sum(weights))
            for ri,row in enumerate(rows):
                cells=table.add_row().cells
                for ci,value in enumerate(row):
                    cells[ci].width=Cm(usable*weights[ci]/sum(weights))
                    cells[ci].text=value
                    for p in cells[ci].paragraphs:
                        p.paragraph_format.space_after=Pt(4)
                        p.paragraph_format.space_before=Pt(4)
                        for run in p.runs:run.font.size=Pt(9 if len(row)>6 else 10)
                    tcPr=cells[ci]._tc.get_or_add_tcPr()
                    borders=OxmlElement('w:tcBorders')
                    for side in ['top','left','bottom','right']:
                        edge=OxmlElement('w:'+side);edge.set(qn('w:val'),'single');edge.set(qn('w:sz'),'4');edge.set(qn('w:color'),'D9D9D9');borders.append(edge)
                    tcPr.append(borders)
                    if ri==0:
                        fill=OxmlElement('w:shd');fill.set(qn('w:fill'),'E8EEEC');tcPr.append(fill)
                        for run in cells[ci].paragraphs[0].runs:run.bold=True
                trPr=table.rows[-1]._tr.get_or_add_trPr()
                trPr.append(OxmlElement('w:cantSplit'))
                if ri==0:trPr.append(OxmlElement('w:tblHeader'))
            doc.add_paragraph().paragraph_format.space_after=Pt(1)
            continue
        if line.startswith('# '):
            title='第7讲 机器学习基础与朴素贝叶斯 '+('学生工作单' if name.startswith('student') else '教师参考')
            doc.add_paragraph(title,'Title')
        elif line.startswith('## '):
            # Deliberate section pages give students room and prevent cramped form tables.
            p=doc.add_paragraph(re.sub(r'[：？]',' ',line[3:]),'Heading 1')
            if name.startswith('student') and not line.startswith('## 1　'):p.paragraph_format.page_break_before=True
            if name.startswith('teacher') and any(line.startswith('## '+str(k)+' ') for k in [3,4,5,6,7,8,9]):p.paragraph_format.page_break_before=True
        elif line.startswith('### '):doc.add_paragraph(clean(line[4:]),'Heading 2')
        else:
            p=doc.add_paragraph(clean(line))
            if name.startswith('student') and '________________' in line:
                p.paragraph_format.space_after=Pt(12)
        i+=1
    doc.save(BASE/(name+'.docx'))

if __name__=='__main__':
    for name in ['student-worksheet','teacher-reference']:make(name)
