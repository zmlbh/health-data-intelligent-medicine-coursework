from pathlib import Path
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / '论文交付'
OUT.mkdir(exist_ok=True)
text = (BASE / '论文式作业.md').read_text(encoding='utf-8')
text = text.replace('从区分能力到决策后果：心脏病分类中线性模型的比较与解释边界', '心脏病分类中线性模型的比较与解释边界')
text = text.replace('这一研究展示了从测量依据到预测检验的证据组织方式。本作业借鉴其以多面板图组织论证的方式，在较小的公开基准中研究线性模型的选择问题；两者的数据规模、任务和验证层级不同，性能数值不作横向比较。', '这一研究将测量依据与预测检验连接起来，也说明模型评价需要与其目标人群和验证层级相联系。在公开心脏病基准中，线性模型的比较则提供了考察概率建模与决策评价关系的可控场景。')
text = re.sub(r'数据来自 `packet-b-repeated-cv.csv` 和 `packet-b-model-comparison.csv`。', '', text)
text = re.sub(r'完整数据见 `packet-c-logistic-coefficients.csv` 与 `packet-c-threshold-audit.csv`。', '', text)
text = text.replace('原始点估计来自 `packet-d-locked-test.csv`；区间来自固定模型预测上的 1,000 次分层 bootstrap。', '区间来自固定模型预测上的 1,000 次分层 bootstrap。')
text = text.replace('数值来自 `packet-c-collinearity-stress-test.csv`。这是已保存的诊断性压力测试', '这是诊断性压力测试')
start = text.index('**数据与版本。**')
end = text.index('**阈值与指标。**')
text = text[:start] + '''**数据。** 本研究使用 UCI Statlog (Heart)[2]，包含 270 条记录、13 个原始输入，结局为心脏病存在或不存在，阳性 120 条、阴性 150 条。分析限于该公开基准，不将其他站点整理的教学记录并入本数据集。

**开发与评估。** 分层划分 80% 的记录用于开发、20% 用于测试，随机种子为 2026，分别得到 216 条开发记录和 54 条测试记录。预处理在训练折内拟合，包括数值变量标准化与分类变量编码。开发集采用 5 折、5 次重复的分层交叉验证。比较模型为 LDA、逻辑回归、高斯朴素贝叶斯和患病率基线。

**概率模型。** 逻辑回归以线性评分 z = β₀ + xᵀβ 建模条件概率，p = 1/(1 + exp(−z))。LDA 假设各类别的特征服从具有不同均值、共享协方差的多元高斯分布，并结合类别先验计算后验概率。共享协方差使类别对数密度之差中的二次项抵消，从而产生线性判别边界。混合变量并不严格满足连续高斯假设，因此模型比较同时依赖实际验证表现。

''' + text[end:]
text = text.replace('PR 指标的具体实现与全部次要指标保留在源代码和结果表中，不以文件名替代指标定义。', '阈值仅依据开发集选择；测试结果用于描述所选操作规则的表现。')
text = text.replace('原区间表的 `estimate` 字段是 bootstrap 中位数；本文测试点估计取原测试表。', '点估计由原始测试记录计算，区别于重采样分布的中位数。')

doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Cm(29.7), Cm(21)
sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.7)
sec.left_margin, sec.right_margin = Cm(1.9), Cm(1.9)
sec.header_distance = Cm(.7)
sec.footer_distance = Cm(.8)
for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
    s=doc.styles[name]
    s.font.name='Times New Roman'
    s.font.color.rgb=RGBColor(0,0,0)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), '宋体' if name in ['Normal','Caption'] else '黑体')
    s.paragraph_format.space_after=Pt(6)
normal=doc.styles['Normal']
normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.2
normal.paragraph_format.widow_control=True
for name,size in [('Title',21),('Heading 1',13),('Heading 2',12),('Caption',9)]:
    doc.styles[name].font.size=Pt(size)
doc.styles['Title'].paragraph_format.space_after=Pt(12)
doc.styles['Heading 1'].paragraph_format.space_before=Pt(12)
doc.styles['Heading 2'].paragraph_format.space_before=Pt(8)
doc.styles['Caption'].paragraph_format.line_spacing=1.1
doc.styles['Caption'].paragraph_format.space_after=Pt(10)
doc.styles['Caption'].font.bold=False
doc.styles['Caption'].font.italic=False
for el in list(doc.styles.element.iter(qn('w:pBdr'))):
    el.getparent().remove(el)

footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

def add_inline(p, s):
    for i,part in enumerate(re.split(r'(\*\*.*?\*\*|\*[^*]+\*)',s)):
        if part.startswith('**'):
            p.add_run(part[2:-2]).bold=True
        elif part.startswith('*'):
            p.add_run(part[1:-1]).italic=True
        else:
            p.add_run(part.replace('`',''))

blocks=text.split('\n\n')
for block in blocks:
    block=block.strip()
    if not block:continue
    if block.startswith('# '):
        p=doc.add_paragraph(block[2:], 'Title')
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p=doc.add_paragraph('作者姓名________________    单位或课程________________')
        p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.runs[0].font.size=Pt(9)
        continue
    if block.startswith('## '):
        title=block[3:]
        if title=='2 结果':
            doc.add_page_break()
        if title=='4 方法':doc.add_page_break()
        doc.add_paragraph(title, 'Heading 1')
        continue
    if block.startswith('### '):
        title=block[4:]
        if title.startswith(('2.2','2.3','2.4')):doc.add_page_break()
        doc.add_paragraph(title, 'Heading 2')
        continue
    if block.startswith('!['):
        rel=re.search(r'\]\((.*?)\)',block).group(1)
        p=doc.add_paragraph()
        p.paragraph_format.keep_with_next=True
        p.paragraph_format.space_after=Pt(5)
        p.add_run().add_picture(str(BASE/rel),width=Cm(17.2))
        continue
    if block.startswith('|'):
        rows=[r for r in block.splitlines() if not re.match(r'^\|[\s:|\-]+$',r)]
        table=doc.add_table(rows=0, cols=3)
        table.autofit=False
        for col,w in zip(table.columns,[8.2,4,5]):col.width=Cm(w)
        for ri,row in enumerate(rows):
            cells=table.add_row().cells
            for j,val in enumerate(row.strip('|').split('|')):
                p=cells[j].paragraphs[0];p.add_run(val.strip())
                p.paragraph_format.space_before=Pt(5);p.paragraph_format.space_after=Pt(5)
                p.paragraph_format.line_spacing=1.1
                if j:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                if ri==0:
                    p.runs[0].bold=True
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EEEEEE');cells[j]._tc.get_or_add_tcPr().append(shade)
                borders=OxmlElement('w:tcBorders')
                for edge in ['top','bottom','left','right']:
                    el=OxmlElement('w:'+edge);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');borders.append(el)
                cells[j]._tc.get_or_add_tcPr().append(borders)
        doc.add_paragraph().paragraph_format.space_after=Pt(0)
        continue
    caption=block.startswith(('**图 ','**表 '))
    if re.match(r'^1\. Adil',block):
        for ref in block.splitlines():
            p=doc.add_paragraph()
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing=1.1
            add_inline(p,ref)
        continue
    p=doc.add_paragraph(style='Caption' if caption else 'Normal')
    p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    add_inline(p,block)

doc.core_properties.title='心脏病分类中线性模型的比较与解释边界'
doc.core_properties.author=''
doc.core_properties.subject='线性判别分析与逻辑回归的实证比较'
dest=OUT/'线性模型比较研究.docx'
doc.save(dest)
print(dest)
