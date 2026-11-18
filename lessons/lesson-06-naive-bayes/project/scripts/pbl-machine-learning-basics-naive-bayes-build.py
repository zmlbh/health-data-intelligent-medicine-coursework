"""Course-specific Lesson 7 PBL package, approved 2026-09-17.

Numerics: D:/Python/python.exe scripts/lesson7_analysis.py
Documents: bundled runtime Python this_file.py --docs
All reads/writes for the generated package are local to this lesson.
The skill supplies a checker, never a content generator.
"""
from pathlib import Path
import argparse, json, shutil, sys, subprocess, hashlib
ROOT=Path(__file__).resolve().parents[1]
SLUG='pbl-machine-learning-basics-naive-bayes'
ASSET=ROOT/'assets'/SLUG
REVIEW=ROOT/'review'
TITLE='第7讲 机器学习基础与朴素贝叶斯'

def load_evidence():
    return json.loads((ASSET/'computed-evidence.json').read_text(encoding='utf-8'))

def prepare_design():
    draft=json.loads((ROOT/'planning/review-20260917/analysis-design-draft.json').read_text(encoding='utf-8'))
    names={'planned-a1-records.csv':'packet-a1.csv','planned-a2-provenance.csv':'packet-a2.csv','planned-a3-split.csv':'packet-a3.csv','planned-b1-counts.csv':'packet-b1.csv','planned-b2-queries.csv':'packet-b2.csv','planned-b3-classroom.csv':'packet-b3.csv','planned-b4-loss.csv':'packet-b4.csv','planned-b5-mse.csv':'packet-b5.csv','planned-c1-threshold.csv':'packet-c1.csv','planned-c2-ranking.png':'packet-c2-ranking.png','planned-c3-calibration.csv':'packet-c3.csv','planned-d1-dependence.csv':'packet-d1.csv','planned-d2-redundancy.csv':'packet-d2.csv','planned-d3-test-and-overlap.csv':'packet-d3.csv','planned-d4-transfer.csv':'packet-d4.csv'}
    text=json.dumps(draft,ensure_ascii=False)
    for a,b in names.items(): text=text.replace(a,b)
    design=json.loads(text); design['status']='approved and implemented 2026-09-17'
    for cov in design['course_coverage']:
        if cov['objective_id']=='LO8':cov['observable_outcome']=cov['observable_outcome'].replace('定位两阈值','定位0.10阈值的ROC及PR坐标')
    design['implementation_notes']=['表 B1只给原始训练计数；待求参数写在独立答题区，避免证据与答案混排。','表 B2两条查询只必算查询1；第二条为选做。','概率单调变换给出数值汇总；AP与梯形PR面积不混名。','课堂二症状练习使用同一72/24划分；不是在验证集重新估计条件概率。']
    # Revision after the 2026-09-17 pilot fill: module outputs, minutes and synthesis size follow the revised worksheet.
    revised={
      'Q1':(10,'按表 S1的二值表示写出表 A1第61条记录的X与Y，说明fθ(X)与阈值、肾炎列的问题；在追踪表第2行界定记录代表的对象。'),
      'Q2':(10,'重排五张流程卡并为每步分配训练/验证/测试数据，判断看过测试后改阈值的后果；在追踪表第3行写数据分工协议。'),
      'Q3':(20,'用计算表从表 B1计数得到查询1的先验、十二个条件因子、类别分数与后验；判断二元关键词表示的适配条件；在追踪表第4行写后验及其依赖的假设。'),
      'Q4':(20,'用损失表比较表 B4两模型的accuracy与平均交叉熵，计算表 B5的MSE及单位，完成一张证据卡；在追踪表第5行写损失选择。'),
      'Q5':(26,'用指标表计算阈值0.10的六个指标与先验基线precision，比较三个阈值，写出ROC/PR点并解释AUC的边界，读最小校准箱；在追踪表第6行写报告方案并在第1行写冻结草案。'),
      'Q6':(34,'比较表 D1类别内联合概率与乘积，解释表 D2复制症状并写NB优缺点，按表 D4完成作业原题计算与作答，在追踪表第7行限定推广范围；完成决策检验矩阵与150—250字备忘录初稿。')}
    by_q={}
    for q in design['problem_architecture']['inquiry_questions']:
        q['minutes'],q['student_action']=revised[q['id']];q['student_output']=q['student_action'];by_q[q['id']]=q
    for cov in design['course_coverage']:
        q=by_q[cov['inquiry_question_ids'][0]]
        if cov['objective_id']!='LO14':cov['student_action']=cov['analysis_method']=q['student_action']
        if cov['objective_id']=='LO15':cov['worksheet_location']='Phase 2 / Q6作业原题（计算表与作答框）及课外综合'
        if cov['objective_id']=='LO14':
            cov['worksheet_location']='Phase 3 / 课堂训练①至③'
            cov['student_action']=cov['analysis_method']='课堂训练①至③：用表 B1两行计数估计二症状NB参数，计算四种组合的后验，并按表 B3记录数加权汇总TP、FN、FP、TN及sensitivity与specificity。'
    for an in design.get('analyses',[]):
        if an.get('inquiry_question_ids'):an['method']=by_q[an['inquiry_question_ids'][0]]['student_action']
    design['syllabus_tasks'][0]['worksheet_location']='Phase 3前15分钟课堂训练①至③；数据表 B3；独立纸笔训练二症状NB并计算sensitivity/specificity；可用辅助notebook核对。'
    design['syllabus_tasks'][1]['worksheet_location']='Q6“作业原题”计算表与作答框（表 D4、表 C1）；课外综合的备忘录从追踪表引用结论。'
    design['workload']['phase2_includes']='阅读、计算表、写答、证据卡、追踪表更新、决策检验矩阵、150—250字备忘录初稿和accuracy作业；不另加必做迁移。'
    design['implementation_notes'].append('2026-09-17试填后修订：各模块暂定结论只写在总答案追踪表对应行，不另设重复答题框；手算用预排计算表；删去Q2缺口清单；决策检验矩阵只记已有证据；备忘录缩为150—250字四段结构。')
    (ASSET/'analysis-design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2),encoding='utf-8')
    return design

def build_docs():
    from docx import Document
    from docx.shared import Inches, Pt, Cm, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    E=load_evidence(); T=E['tables']; M=E['metrics']; design=prepare_design()
    class Writer:
        def __init__(self,kind):
            self.d=Document(); self.kind=kind; self.page=0
            s=self.d.sections[0]; s.page_width=Cm(21);s.page_height=Cm(29.7)
            s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Inches(.65)
            s.header_distance=s.footer_distance=Inches(.28)
            for name,size in [('Normal',10.5),('Title',23),('Subtitle',13),('Heading 1',16),('Heading 2',12),('Heading 3',11),('Caption',9)]:
                st=self.d.styles[name];st.font.name='Arial';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
                st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'微软雅黑')
                st.paragraph_format.space_after=Pt(5);st.paragraph_format.line_spacing=1.12
                if name.startswith('Heading'):st.paragraph_format.space_before=Pt(9)
                for border in list(st.element.iter(qn('w:pBdr'))): border.getparent().remove(border)
            n=self.d.styles['Normal'];n.paragraph_format.widow_control=True
            hp=s.header.paragraphs[0];hp.text='AI for Biomedical Data Science     第7讲     '+kind;hp.style='Caption';hp.runs[0].font.size=Pt(8)
            fp=s.footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
            fp.add_run('教学研究用途  •  ')
            fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');fp._p.append(fld)
        def p(self,text,style=None):
            return self.d.add_paragraph(text,style)
        def h(self,text,level=2):return self.d.add_heading(text,level)
        def new(self,heading):
            self.page+=1;h=self.h(heading,1);h.paragraph_format.page_break_before=True
        def table(self,headers,rows,widths=None,answer=False):
            table=self.d.add_table(rows=1,cols=len(headers));table.style='Table Grid';table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
            if widths is None: widths=[6.96/len(headers)]*len(headers)
            for col,w in zip(table.columns,widths):col.width=Inches(w)
            for i,text in enumerate(headers):table.rows[0].cells[i].text=str(text)
            trpr=table.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
            for row in rows:
                cells=table.add_row().cells
                for i,value in enumerate(row):cells[i].text=str(value)
            for ri,row in enumerate(table.rows):
                no=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no)
                if answer and ri>0:row.height=Inches(.50)
                for ci,cell in enumerate(row.cells):
                    cell.width=Inches(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    tcpr=cell._tc.get_or_add_tcPr();marg=OxmlElement('w:tcMar')
                    for side in ['top','left','bottom','right']:
                        v=OxmlElement('w:'+side);v.set(qn('w:w'),'45');v.set(qn('w:type'),'dxa');marg.append(v)
                    tcpr.append(marg)
                    if ri==0:
                        shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'E8EEF5');tcpr.append(shd)
                    for p in cell.paragraphs:
                        p.paragraph_format.space_after=Pt(0);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1.04
                        p.paragraph_format.keep_with_next=ri<len(table.rows)-1
                        for run in p.runs:run.font.size=Pt(9 if len(headers)>6 else 10);run.bold=(ri==0)
            borders=OxmlElement('w:tblBorders')
            for edge in ['top','left','bottom','right','insideH','insideV']:
                b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'D9D9D9');borders.append(b)
            table._tbl.tblPr.append(borders)
            spacer=self.d.add_paragraph();spacer.paragraph_format.space_after=Pt(0);spacer.paragraph_format.space_before=Pt(0);spacer.paragraph_format.line_spacing=Pt(3);spacer.add_run().font.size=Pt(1)
            return table
        def prompt(self,text):
            # Prompt card: bold the short title before the first full-width colon so cards are easy to scan.
            head,sep,body=text.partition('：')
            par=self.d.add_paragraph()
            if sep and len(head)<=40:
                par.add_run(head+sep).bold=True;par.add_run(body)
            else:par.add_run(text)
            par.paragraph_format.keep_with_next=True;par.paragraph_format.keep_together=True
            return par
        def card(self,text):
            # Tracker-update card: no answer box of its own; shaded with a left rule so it is not mistaken for body text.
            par=self.prompt(text);par.paragraph_format.keep_with_next=False
            pPr=par._p.get_or_add_pPr();after=('w:tabs','w:suppressAutoHyphens','w:kinsoku','w:wordWrap','w:overflowPunct','w:topLinePunct','w:autoSpaceDE','w:autoSpaceDN','w:bidi','w:adjustRightInd','w:snapToGrid','w:spacing','w:ind','w:contextualSpacing','w:mirrorIndents','w:suppressOverlap','w:jc','w:textDirection','w:textAlignment','w:textboxTightWrap','w:outlineLvl','w:divId','w:cnfStyle','w:rPr','w:sectPr','w:pPrChange')
            bdr=OxmlElement('w:pBdr');left=OxmlElement('w:left')
            for k,v in [('val','single'),('sz','18'),('space','6'),('color','5B7FA6')]:left.set(qn('w:'+k),v)
            bdr.append(left);pPr.insert_element_before(bdr,'w:shd',*after)
            shd=OxmlElement('w:shd');shd.set(qn('w:val'),'clear');shd.set(qn('w:fill'),'F2F5F9');pPr.insert_element_before(shd,*after)
            return par
        def answer(self,prompt,label='个人作答',lines=3):
            self.prompt(prompt)
            t=self.table([label],[['']],answer=True)
            t.rows[1].height=Inches(.20*lines+.08)
            return t
        def evidence(self,key):
            v=T[key]; self.p(v['caption'],'Caption').paragraph_format.keep_with_next=True
            widths={'A2':[1.6,5.36],'D3':[2,4.96],'D4':[3,3.96]}.get(key)
            self.table(v['headers'],v['rows'],widths)
        def eq(self,name):
            self.d.add_picture(str(ASSET/f'equation-{name}.png'),width=Inches({'mse':3.4,'loss':6.0,'bernoulli':6.2,'bayes':6.6}[name]))
            self.d.paragraphs[-1].alignment=WD_ALIGN_PARAGRAPH.CENTER
        def title(self,subtitle):
            p=self.p(TITLE,'Title');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p=self.p(subtitle,'Subtitle');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        def save(self,suffix):
            path=ROOT/f'{SLUG}-{suffix}.docx';self.d.save(path);print(path.name)
    # ---- Student worksheet. Revised 2026-09-17 after the pilot fill (review/pbl-...-pilot-report.md):
    # module conclusions live only in the tracker; computations use scaffolded tables; referents are explicit.
    options=[['A 保留当前基线','把当前配置（六项二值症状、NB、0.50阈值）原样冻结，作为下一轮离线比较的基线。'],['B 修改后冻结','先改动至少一项：症状表示（如体温切点、删去或合并症状）、平滑方式或阈值；说明将只用训练和验证记录检验改动，再冻结新配置。须写明改了什么。'],['C 暂缓提交','暂不提交任何配置；先补齐一项会决定选A还是选B的证据，并写明缺的是哪一项。']]
    qmap=[['Q1','表 A1、表 A2：八列中哪些是输入、哪一列是要预测的标签？这些记录代表什么对象？','任务、特征与标签','10'],['Q2','表 A3：72/24/24条记录怎样分担参数估计、阈值选择与最终评价？','训练、预测与泛化','10'],['Q3','表 B1、表 B2：训练计数怎样变成一条查询记录的预测？（表 B3留到翻转课堂）','Bayes定理与NB训练','20'],['Q4','表 B4、表 B5：两个模型判对同样多，为什么损失不同？','交叉熵与MSE','20'],['Q5','表 C1、图 C2、表 C3：分类、排序、概率分别怎样评价？','模型评价指标','26'],['Q6','表 D1至表 D4：模型假设与数据范围怎样改变研究方案？','假设、优缺点与综合','34']]
    roadmap=[['启动课堂','45分钟','只用第1页委托、表 S1和表 S2作初选；完成3W表与个人学习计划。'],['课外自学','120分钟','按Packet A→B→C→D顺序领取；完成Q1至Q6、决策检验矩阵与研究备忘录初稿。'],['翻转课堂','45分钟','独立训练二症状NB；随机1至2人白板说明；同伴提问与个人修订。']]
    phase1=[['7','读第1页委托、方案A–C、表 S1与表 S2，作出初选','总答案追踪表第1行'],['8','澄清输入、标签与预测目标','启动澄清'],['8','排列流程卡并写下一个疑问','启动流程'],['10','按三个概念簇完成3W表','3W表'],['8','读定向阅读指南中的在线段落，制订个人学习计划','个人学习计划'],['4','写给研究组的一个问题','启动退出条']]
    readings=[['R1','Q1/Q2','scikit-learn User Guide 3.1开头几段：训练集与测试集，以及为什么还要另留validation set（验证集）。'],['R2','Q3/Q6','User Guide 1.9开头（Bayes定理与朴素假设）和1.9.4 Bernoulli Naive Bayes。'],['R3','Q4/Q5','User Guide 3.4.4.6 Confusion matrix、3.4.4.9 Precision, recall and F-measures、3.4.4.12 Log loss、3.4.4.15 ROC；以及3.4中Regression metrics下的Mean squared error条目。'],['R4','Q5','User Guide 1.16.1 Calibration curves：reliability diagram（可靠性图）怎样分箱，以及每箱样本数的作用。']]
    w=Writer('学生学习与答题册')
    w.page=1;w.title('Problem Based Learning Student Worksheet')
    w.p('姓名与学号写在本页页眉处。每人独立提交本册；可以讨论、查资料或使用AI，但计算、证据核对与判断由本人负责。本册仅用于教学研究，不用于临床诊断、部署或患者照护。')
    w.h('研究组委托')
    w.p('研究组要把一个“根据六项症状预测膀胱炎症标签”的朴素贝叶斯（Naive Bayes，下文简称NB）模型纳入下一轮离线方法比较，作为其他方法都要对照的基线。你要交给研究组两样东西：①从下表方案A–C中选定的处理方案；②一份说明输入、训练、验证、评价和适用范围的研究备忘录。')
    w.table(['方案','研究组实际采取的动作'],options,[1.35,5.61])
    w.p('冻结：把输入表示、参数估计规则和阈值固定下来，此后不再根据测试结果修改。三个方案互斥，且都不授权临床使用；选哪一项都可能得高分，评分看你是否用Q1至Q6的证据把选择讲清楚。')
    w.p('表 S1  启动事实｜启动初选。每行是研究组提供的一项已知条件；数据为UCI Acute Inflammations，共120条记录、8列，来源说明称其为医学专家为测试专家系统而设计的潜在病例描述。','Caption').paragraph_format.keep_with_next=True
    w.table(['已知条件','当前事实'],[['数据','体温及五个有无症状，共六项候选输入；另外两列是膀胱炎症与肾炎的诊断决策。'],['已有方案','六项输入全部二值化：体温≥38℃记为发热=1，其余症状有=1、无=0；拟用NB和0.50阈值。'],['资料缺口','未提供独立患者身份、抽样过程或外部人群验证；尚未公布模型结果。'],['用途','研究组内部比较方法时的基线，不是诊疗系统。']],[1.3,5.66])
    w.p('表 S2  三条原始记录｜启动澄清。每行一条记录，取自120条中的第21、61、81条；体温单位为℃，其余各列1表示有、0表示无。Packet A的表 A1给出包含这三条在内的6条记录。','Caption').paragraph_format.keep_with_next=True
    a1=T['A1']
    w.table(a1['headers'],[a1['rows'][i] for i in (1,3,4)])
    w.p('最终产出：总答案追踪表、Q6作业原题作答、决策检验矩阵与研究备忘录初稿（课外综合页），以及翻转课堂上的修订段落。备忘录必须用到Q1至Q6的结果，不能只回答“不能用于临床”。')
    w.p('停止条件：若说不清哪些记录参与了参数估计、哪些参与了阈值选择，暂停提交；若测试集结果被用来调整阈值，撤回“独立测试”的说法。修改条件：若重复或相关的症状改变了预测概率，重新审查概率的含义；若测试记录的症状组合在训练集中都出现过，收窄对新症状组合的推广主张。')
    w.h('学习路线与探究问题',1)
    w.table(['阶段','预算','你将完成什么'],roadmap,[1.1,.8,5.06])
    w.table(['模块','案例中的问题及证据','学习内容','分钟'],qmap,[.5,3.75,2.1,.61])
    w.p('Q1至Q6是探究问题编号，每个编号对应一个Packet中的学习模块，不是额外作业。表中分钟数包含阅读、计算、写答和追踪表更新；Q6的34分钟含约14分钟的决策检验矩阵与备忘录初稿。翻转课堂的15分钟训练练习不计入课外时间。需要时用计算器，不要求编程。')
    w.h('本册过程用语')
    w.p('Packet：按A、B、C、D顺序领取的证据包，每个Packet含概念读页（完成本模块所需的简短知识）、证据表和题目。检查点：交完一个阶段的作答后才领取下一个Packet。冻结：固定输入表示、参数估计规则和阈值，此后不再根据测试结果修改。')
    w.p('总答案追踪表：本册中唯一持续修改的判断记录，用来保存你对研究组问题的当前判断。第1行记录当前方案（第1页方案A–C之一），第2至7行分别记录Q1至Q6的暂定结论；每个模块末尾的“更新追踪表”题卡会逐列说明这一行写什么。修改时保留旧内容，用删除线或“原：……”标出。')
    w.p('3W：按三个完整问题组织自学——What do I know（关于这个问题，我已经知道什么？）、What do I not know（要正确回答问题，我还不知道什么？）、What will I do next（下一步我要学习什么、查找什么或分析什么？）。证据卡：只核查一个具体说法，写明原话、来源、用本案例数字所作的检验和成立范围。退出条：阶段结束时的简短作答，用来暴露仍未解决的问题。白板说明：翻转课堂上随机抽到的同学解释自己的证据与推理，不背固定讲稿。')
    w.h('分阶段发放')
    w.p('启动课堂只使用第1页至“启动课堂（45分钟）”部分末尾的检查点S。之后依次领取：交检查点S后领取Packet A；交检查点A后领取Packet B；交检查点B后领取Packet C；交检查点C（含冻结草案）后领取Packet D。请勿提前查看未领取的Packet。翻转课堂页在课外自学结束后使用。')
    w.new('总答案追踪表')
    w.prompt('总答案追踪表：为给研究组留下一条可以核对的判断轨迹，请在启动课堂先填第1行；之后每完成Q1至Q6中的一个模块，按该模块末尾的“更新追踪表”题卡填对应的第2至7行，并在每个Packet结束时更新第1行。每格写关键词或一句话；“支持证据编号”格写表或图的编号（如表 S1），“最后更新于”格写启动、Q1至Q6、Packet A至D或课堂。')
    t=w.table(['行号及主题','当前判断','支持证据编号','反向证据','什么发现会改变判断','最后更新于'],[[r,'','','','',''] for r in ['1 当前方案（A–C）及主要理由','2 任务与记录对象','3 数据分工与评价流程','4 NB参数与查询预测','5 损失选择','6 分类、排序与概率评价','7 假设与推广范围']],[1.0,1.8,.8,1.2,1.45,.71],answer=True)
    for row in t.rows[1:]:row.height=Inches(.98)
    w.p('“反向证据”格写已知的、限制本行判断或支持另一方案的事实；尚未发现时写“目前未发现”，不要写成“已证明不存在”。“什么发现会改变判断”格写将来可能出现、会让你改变本行判断的发现。')
    w.new('启动课堂（45分钟）')
    w.table(['分钟','每人的动作','写答位置'],phase1,[.55,4.55,1.86])
    w.card('启动初选（写在总答案追踪表第1行）：从第1页方案A–C中选一个，只依据第1页研究组委托、表 S1和表 S2，暂不看任何Packet。在第1行“当前判断”格写方案字母和一句理由，理由须引用表 S1或表 S2中的一项事实；“支持证据编号”格写所引表号；“反向证据”格写一项不利于所选方案的已知事实，或写“目前未发现”；“最后更新于”格写“启动”。“什么发现会改变判断”格在写完启动退出条后再填。')
    w.answer('启动澄清：为弄清表 S1中的模型到底回答什么问题，请按表 S1“已有方案”的表示，写出表 S2第21条记录的六项输入取值和要预测的标签取值；再用一句话区分两个研究目标：“为一条与这120条来源相同的新病例描述预测膀胱炎症的概率”和“检验恶心与膀胱炎症是否相关”。写三行：①输入；②标签；③两个目标的区别。','启动澄清',3)
    w.p('启动流程卡（甲至戊五张，顺序已打乱）：甲，冻结配置；乙，计算最终评价指标；丙，从带标签的记录估计先验和条件概率；丁，比较几个候选阈值下的错误并选定阈值；戊，用已估计的参数为一批记录计算阳性概率。')
    w.answer('启动流程：为给研究组排出建模步骤，请把流程卡甲至戊排成你认为的先后顺序（写成“丙→……”的形式），再写一个你对其中某张卡最具体的疑问，并注明是哪张卡。写两行；此时不要求排对，Q2会再排一次。','启动流程',2)
    w.h('3W表与定向阅读')
    w.p('3W格式示例（另一情境，与本课数据无关）：比较两种培养基时，已知“两组平均生长量不同”；不知“每组有几个重复、组内波动多大”；下一步“查实验记录中的重复数，画每组散点图”。')
    w.prompt('3W表：为让课外自学直接服务于第1页方案A–C的选择，请为三个概念簇各写一行。第2列写你已有的相关知识（可来自前六讲或统计课）；第3列只写会影响方案选择的知识缺口；第4列写具体动作，并注明下方定向阅读指南中的资源编号R1至R4和要找的概念。每格1至2句。')
    w.table(['概念簇','关于这个问题，我已经知道什么？','要正确回答问题，我还不知道什么？','下一步我要学习什么、查找什么或分析什么？'],[[s,'','',''] for s in ['任务与流程（Q1/Q2）','概率与损失（Q3/Q4）','评价与边界（Q5/Q6）']],[1.15,1.7,1.75,2.36],answer=True)
    w.h('定向阅读指南')
    w.table(['资源','模块','只读这些部分'],readings,[.5,.8,5.66])
    w.p('R1至R4网址（均为scikit-learn官方用户指南）：R1 https://scikit-learn.org/stable/modules/cross_validation.html ；R2 https://scikit-learn.org/stable/modules/naive_bayes.html ；R3 https://scikit-learn.org/stable/modules/model_evaluation.html ；R4 https://scikit-learn.org/stable/modules/calibration.html 。')
    w.p('启动课堂和课外都可阅读R1至R4的在线段落，只读表中列出的部分，不要求整章通读。各Packet内的概念读页随Packet发放，足以完成对应必做题；在线原文用于补充和核对。')
    w.h('个人学习计划与退出条')
    w.answer('个人学习计划：为补上3W表中最影响方案A–C选择的一个缺口，请写四行：①这个缺口是什么，引用3W表中的哪一行；②它对应Q1至Q6中的哪个模块；③要读R1至R4中的哪一段，或要做什么计算、比较；④一个别人能检查的完成标准和预计分钟数。完成标准的格式示例（另一主题）：“能不看笔记说出t检验统计量分母中每一项的含义”；不能只写“看懂”。','个人学习计划',4)
    w.answer('启动退出条（最后4分钟）：依据表 S1“资料缺口”一行，写一个你想问研究组的具体问题，并写出它的两种可能回答分别会让你保留还是改选第1页方案A–C中的哪一个。写两至三句；写完后，在总答案追踪表第1行“什么发现会改变判断”格用不超过15个字记下这个问题。','启动退出条',3)
    w.p('提交检查点S：总答案追踪表第1行、启动澄清、启动流程、3W表、个人学习计划与启动退出条。此时只看问题是否具体、理由是否引用了表 S1或表 S2，不看是否猜中模型成绩。')
    w.new('Packet A：任务、数据与流程')
    w.h('Q1 八列数据怎样构成一个预测任务')
    w.p('约10分钟，含阅读、写答与追踪表更新。学习目标：把“数据模型”对应到本案例的输入、标签和预测对象；区分预测与关联检验。阅读下方概念读页与表 A1、表 A2；在线资源R1。')
    w.p('概念读页：数据模型用一个函数描述输入与输出的关系。一条记录的输入写成特征向量X（feature，特征），要预测的量称为标签Y（label）；本课把阳性记为1、阴性记为0。模型fθ(X)输出阳性概率p，θ是从训练数据估计出的参数；再用阈值t把p变成类别，p≥t时预测为1。两个变量统计相关，不代表能准确预测另一条记录，也不证明因果。')
    w.evidence('A1'); w.evidence('A2')
    w.answer('Q1建模：为确定交给研究组的输入和输出，请写五行：①按表 S1“已有方案”的表示（体温≥38℃记发热=1，其余症状有=1、无=0），写出表 A1第61条记录的X，六个分量依次为发热、恶心、腰痛、尿意频繁、排尿痛、尿道烧灼；②写出这条记录的主标签Y；③用一句话说明fθ(X)输出什么、阈值0.50怎样把它变成类别；④说明若把肾炎列也放进X会带来什么问题，以及研究组须先确认什么；⑤确认或修正你在启动澄清中对“预测”与“检验相关”的区分，一句话。','Q1 建模',5)
    w.card('Q1更新追踪表第2行：这一行回答“模型用什么预测什么，结果能用来说明什么对象”。在第2行“当前判断”格先用关键词写X与Y（可直接引用Q1建模），再依据表 A2的“来源文字”和“完整8列的重复”两行，写你暂时允许把模型结果用于什么对象；“支持证据编号”格写表号；“反向证据”格写表 A2中一项限制结论推广范围的观察结果，引用一个数字；“什么发现会改变判断”格写仍需向研究组确认的一项来源信息；“最后更新于”格写Q1。')
    w.h('Q2 怎样分工才能评价对新记录的预测')
    w.p('约10分钟，含阅读、写答与追踪表更新。在线资源R1。概念读页：训练是用带标签的记录估计参数；预测是参数固定后为记录计算输出。验证集用于比较和选择配置或阈值；测试集只在配置冻结后用于最终评价，不能再据其结果修改选择。泛化是指模型对没有参与参数估计或选择、且来自目标使用场景的数据仍有预测能力；三个集合的行号不重叠，本身并不保证这一点。')
    w.evidence('A3')
    w.answer('Q2数据分工：为让研究组的最终评价不受选择过程影响，请把启动课堂的五张流程卡重新排序（甲，冻结配置；乙，计算最终评价指标；丙，估计先验和条件概率；丁，比较候选阈值并选定；戊，用已估计参数计算阳性概率），并依据表 A3在每张卡后注明这一步第一次用到的数据：“训练72条”“验证24条”“测试24条”或“无需新数据”。再用一句话判断：若研究组看了测试集的错误后把阈值从0.50改成0.10，这24条测试记录的结果为什么不能再称为独立评价。写两行。','Q2 数据分工',3)
    w.card('Q2更新追踪表第3行和第1行：在第3行“当前判断”格写你给研究组的数据分工协议（哪一步用哪部分数据、在哪一步冻结）；“反向证据”格写表 A2中一项让“行号不重叠就等于独立评价”站不住的观察结果，引用数字；“什么发现会改变判断”格写一种会让这份协议失效的情况；“最后更新于”格写Q2。随后在第1行“当前判断”格保留或修改第1页方案A–C，写方案字母和一句理由（引用表 A2或表 A3），“最后更新于”格写Packet A。')
    w.p('提交检查点A：Q1建模、Q2数据分工，以及总答案追踪表第1至3行；然后领取Packet B。')
    w.new('Packet B：训练朴素贝叶斯与概率损失')
    w.h('Q3 训练计数怎样变成预测')
    w.p('约20分钟，含概念读页、手算表、迁移题与追踪表更新。学习目标：从训练计数估计先验与条件概率，用Bayes定理归一化得到后验，并理解取值为0的症状同样进入计算。在线资源R2。只必算表 B2的查询1。')
    w.p('概念读页：Bayes定理把“某类别下出现这组症状的可能性”与该类别的先验结合，得到看到症状后的类别后验。先验P(Y=c)用训练集中各类别的比例估计。“朴素”指在给定类别Y后，模型把各症状当作相互独立，因此可以把各症状的条件概率相乘；它并不是说症状在总体中互不相关。每个输入只取0或1的这种NB称为伯努利朴素贝叶斯（Bernoulli NB）。')
    w.eq('bayes')
    w.p('c是类别（0或1），j是症状编号，x_j是查询记录第j项症状的取值；S_c是类别c未归一化的分数，把两类分数相加再相除，就得到阳性后验。')
    w.eq('bernoulli')
    w.p('n_c是训练集中类别c的记录数；n_jc是其中症状j为1的记录数；θ_jc是“类别c中症状j为1”的条件概率。加一平滑在计数上加1、分母加2（症状只有0和1两种取值），避免某个零计数使整个乘积变成0。查询中症状为0时，因子取1−θ_jc，不能省略。先验P(Y=c)=n_c/72，不做平滑。')
    w.evidence('B1')
    w.p('训练的产物是两类先验以及每类的六个θ。模型并不记住某条查询的答案；预测时只使用已经估计好的参数。这里由计数直接得到参数，不需要编写优化算法。')
    w.h('Q3 参数与后验手算',3)
    w.evidence('B2')
    w.prompt('Q3计算：为让研究组能逐步复核一次预测，请用表 B1的计数和Q3概念读页中的加一平滑公式，为表 B2查询1填写下表。“查询1取值”列照表 B2抄0或1；六个症状行在两个类别列写条件因子的分式（症状为1时写θ，为0时写1−θ）；“先验”行写两类先验；“类别分数”行写先验与六个因子的乘积（可用计算器，保留4位有效数字）；最后一行在“阳性类（Y=1）”列写S1/(S1+S0)的结果（保留3位小数）和0.50阈值下的预测类别。')
    t=w.table(['项目','查询1取值','阳性类（Y=1）','阴性类（Y=0）'],[['先验 P(Y=c)','—','','']]+[[s,'','',''] for s in ['发热','恶心','腰痛','尿意频繁','排尿痛','尿道烧灼']]+[['类别分数 S1、S0','—','',''],['阳性后验与预测类别','—','','—']],[1.6,1.0,2.18,2.18],answer=True)
    for row in t.rows[1:]:row.height=Inches(.36)
    w.answer('Q3表示迁移：若研究组想用同一方法、依据医学摘要中六个关键词“出现/未出现”（1/0）给文献分类，请对照表 B2的0/1表示判断Bernoulli NB能否直接使用，并说明输入须满足什么条件；再说明若输入改为每个关键词在摘要中出现的次数（0、1、2……），为什么Q3概念读页中θ^x(1−θ)^(1−x)的写法不再适用。写两句。','Q3 表示迁移',2)
    w.card('Q3更新追踪表第4行：在第4行“当前判断”格写查询1的阳性后验与预测类别，并写明参数只来自表 B1中的哪部分记录；“反向证据”格写一项让你不敢完全相信这个后验的已知事实，引用表 B1或表 B2中的数字，若没有写“目前未发现”；“什么发现会改变判断”格写这个后验所依赖的症状关系假设的名称，以及什么样的数据会显示该假设不成立；“最后更新于”格写Q3。')
    w.p('表 B3在翻转课堂部分使用，课外不必提前计算。表 B2查询2为选做，不计入20分钟。')
    w.h('Q4 概率损失在衡量什么')
    w.p('约20分钟，含两段概念读页、损失计算、证据卡与追踪表更新。学习目标：把“预测与真实标签的差距”写成可计算的量，比较二分类交叉熵与连续结局的均方误差。在线资源R3。')
    w.p('概念读页：损失函数给一条或一组预测赋予误差大小。二分类交叉熵也称log loss：真实标签为1时取−ln(p)，为0时取−ln(1−p)，p是模型给出的阳性概率；ln是自然对数，损失越小越好。越有把握却判错，损失越大。')
    w.eq('loss');w.evidence('B4')
    w.prompt('Q4概率比较：为判断研究组能否只报告“判对了几条”，请用表 B4和上方交叉熵公式填写下表：每条记录写两个模型在0.50阈值下的预测类别，以及该条记录的交叉熵损失（自然对数，保留3位小数）；最后一行在两个“预测类别”列写accuracy，在两个“损失”列写平均交叉熵。对差距的解释写在追踪表第5行，见本Packet末尾的Q4更新题卡。')
    t=w.table(['教学记录','模型甲：预测类别','模型甲：损失','模型乙：预测类别','模型乙：损失'],[[str(i),'','','',''] for i in range(1,5)]+[['合计：accuracy／平均损失','','','','']],[1.56,1.35,1.35,1.35,1.35],answer=True)
    for row in t.rows[1:]:row.height=Inches(.36)
    w.p('训练与评价的区别：本课的NB直接用训练计数（加一平滑）得到参数，没有用迭代优化去最小化交叉熵；交叉熵在这里是评价预测概率好坏的工具。选读：不加平滑时，这种计数估计恰好使训练数据的联合似然最大。')
    w.h('Q4 连续误差与证据卡',3)
    w.p('概念读页：均方误差MSE用于比较连续数值的预测与真实值，先逐条平方再求平均。它的单位是目标单位的平方，体温的MSE单位是℃²。二元概率也可以用平方误差评价，称Brier score，但它不等于纯粹的校准误差。')
    w.eq('mse');w.evidence('B5')
    w.answer('Q4连续误差：为分清两类预测目标，请用表 B5写出两条记录的平方误差、MSE及其单位；再用一句话说明为什么不能拿这个MSE与表 B4中两个模型的平均交叉熵比大小。写两行。','Q4 连续误差',2)
    w.prompt('证据卡：为检验你对NB参数或交叉熵的一个理解是否可靠，请从R2的1.9开头或1.9.4、R3的3.4.4.12 Log loss，或你向AI提问得到的回答中，摘录一句与本案例计算直接相关的具体说法，按下表四行填写，每行1至2句。若说法来自AI，“来源”行还须写出你在R2或R3中核对到的小节号。')
    t=w.table(['项目','你的填写'],[['原话（保留原文语言）',''],['来源（小节号或网址；来自AI时写提问内容与核对到的小节）',''],['案例核对（用表 B1或表 B4中的一个数字检验这句话，写出计算或比较）',''],['限定（这句话在本案例中成立的条件，或需要限定的一处）','']],[2.4,4.56],answer=True)
    for row in t.rows[1:]:row.height=Inches(.45)
    w.card('Q4更新追踪表第5行和第1行：在第5行“当前判断”格写研究组除accuracy外还应报告哪一种损失，并引用Q4概率比较表中记录3的两个损失值说明理由；“反向证据”格写这一损失不能告诉研究组的一件事；“什么发现会改变判断”格写一种会让你加报其他评价量的情况；“最后更新于”格写Q4。随后在第1行保留或修改第1页方案A–C，理由引用表 B1、表 B2或表 B4中的一项结果，“最后更新于”格写Packet B。')
    w.p('提交检查点B：Q3计算表、Q3表示迁移、Q4概率比较表、Q4连续误差、证据卡，以及总答案追踪表第1、4、5行；然后领取Packet C。')
    w.new('Packet C：分类、排序与概率评价')
    w.h('Q5 怎样评价研究组的基线')
    w.p('约26分钟，含分类、排序、校准三部分及冻结草案。学习目标：分清六个分类指标的分母，读懂ROC与PR曲线，理解概率校准，并把评价与研究用途联系起来。在线资源R3、R4。')
    w.p('概念读页：TP/FP是预测为阳性的记录中的真/假；TN/FN是预测为阴性的记录中的真/假。Sensitivity（敏感度）=Recall（召回率）=TP/(TP+FN)；Specificity（特异度）=TN/(TN+FP)；Precision（精确率，即阳性预测值）=TP/(TP+FP)；Accuracy（准确率）=(TP+TN)/总数；F1=2TP/(2TP+FP+FN)。分母为0的量没有定义，不能随意当作0。')
    w.evidence('C1')
    w.prompt('Q5指标计算：为看清阈值0.10会带来哪类错误，请只用表 C1“0.10”行的四个计数和上方公式填写下表：每个指标写分子、分母（写出由哪几个计数相加）和结果（保留3位小数）。最后一行针对表 C1“先验基线，阈值0.50”行，在“结果”列用一句话说明它的precision为什么算不出一个数。')
    t=w.table(['指标','分子','分母','结果'],[[m,'','',''] for m in ['accuracy（准确率）','sensitivity（敏感度）','recall（召回率）','specificity（特异度）','precision（精确率）','F1（F1分数）','先验基线的precision（精确率）']],[1.8,1.2,2.0,1.96],answer=True)
    for row in t.rows[1:]:row.height=Inches(.34)
    w.answer('Q5阈值比较：为判断研究组是否该改动0.50阈值（第1页方案B允许的一种改动），比较表 C1中阈值0.10、0.50、0.90三行：第一句写从0.50降到0.10、从0.50升到0.90时分别增加了哪类错误，并引用计数；第二句写你还需要研究组告诉你哪一种错误的代价，才能决定阈值。写两句。','Q5 阈值比较',2)
    w.h('Q5 排序能力',3)
    w.p('概念读页：ROC曲线的横轴是假阳性率FP/(FP+TN)=1−specificity，纵轴是sensitivity；PR曲线的横轴是recall，纵轴是precision。改变阈值，点就沿曲线移动。ROC-AUC概括排序能力：随机抽一条阳性记录和一条阴性记录，阳性记录得分更高的概率（平局计一半）；它不是某个阈值下的准确率。PR曲线显示预测阳性中有多少是真阳性，受阳性比例影响。')
    w.p('PR-AUC要说明积分方式。本课的“梯形PR面积”把相邻点用直线相连后求面积；AP（average precision）按召回率的增量给precision加权求和，一般不等于梯形面积。本例两者相等，不代表总是相等；不要求手推插值算法。')
    w.p('图 C2  验证集排序曲线｜Q5 ROC与PR。曲线来自六症状NB在同一24条验证记录上的预测概率，阳性比例12/24；图中标出阈值0.10、0.50、0.90对应的点。面积无单位。','Caption').paragraph_format.keep_with_next=True
    w.d.add_picture(str(ASSET/'packet-c2-ranking.png'),width=Inches(6.9))
    w.p('图 C2附表：两行都用同一24条验证记录；第二行只把每个概率p换成0.25+0.50p，不重新训练，也不是另一批记录。这个变换不改变概率的大小顺序，平均交叉熵按变换后的概率重算。','Caption').paragraph_format.keep_with_next=True
    w.table(['概率表示','ROC-AUC','梯形PR面积','AP','平均交叉熵'],[['原概率p','1.000','1.000','1.000',f"{M['val_log_loss']:.4f}"],['变换0.25+0.50p','1.000','1.000','1.000',f"{M['transformed_log_loss']:.4f}"]],[2.1,1,1.2,1,1.66])
    w.answer('Q5排序判断：①用表 C1“0.10”行的计数，写出阈值0.10在图 C2中的ROC点（假阳性率, 真阳性率即sensitivity）和PR点（召回率, 精确率），用分式表示；②对照图 C2附表两行：ROC-AUC都是1.000，平均交叉熵却不同，用两句话说明AUC衡量的是什么、没有衡量什么，引用附表中的两个数字。写三行。','Q5 排序判断',3)
    w.h('Q5 概率能否按字面理解',3)
    w.p('概念读页：校准（calibration）问的是：在得到相近预测概率的记录中，实际阳性的比例是否接近这个概率？例如很多记录都预测为0.7时，约70%真为阳性才算吻合。分箱表或可靠性图给出各概率区间的观察结果；每箱记录越少，观察越不稳定。排序好、或某个阈值下全部判对，都不自动保证校准。')
    w.evidence('C3')
    w.answer('Q5校准观察：为判断表 C3中的概率能否直接当作风险值报告，请找出“记录数”最少的一行，写出它的记录数、阳性数、平均预测概率和实际阳性比例，并计算“实际阳性比例 − 平均预测概率”。再用两句话说明：这个差值提示了什么；为什么只凭这一行不能断言模型整体校准得好或差。写三行。','Q5 校准观察',3)
    w.card('Q5更新追踪表第6行：在第6行“当前判断”格写你建议研究组报告的三项评价——分类（注明阈值）、排序、概率各一项，每项注明证据编号（表 C1、图 C2或表 C3）和一个数字；“反向证据”格写表 C1至表 C3中暴露的一项局限，引用数字；“什么发现会改变判断”格写一项会让你改动阈值的信息；“最后更新于”格写Q5。')
    w.card('检查点C冻结草案（写在总答案追踪表第1行）：领取Packet D之前，在第1行“当前判断”格写出你现在选的第1页方案A–C及冻结内容：选A写当前配置（输入表示、平滑方式、阈值）；选B写具体改动，并说明将只用训练和验证记录检验；选C写暂缓前还缺哪一项证据。理由引用Packet C中的一个数字，“最后更新于”格写Packet C。Packet D中的测试结果只用来评价这份草案；若看了Packet D再改配置，须注明需要另一份未用过的测试数据。')
    w.p('提交检查点C：Q5指标计算表、Q5阈值比较、Q5排序判断、Q5校准观察，以及总答案追踪表第6行和第1行的冻结草案；然后领取Packet D。')
    w.new('Packet D：假设、推广范围与作业原题')
    w.h('Q6 哪些结论需要收窄或补证据')
    w.p('约34分钟：Packet D中的分析约20分钟，课外综合页的决策检验矩阵与备忘录初稿约14分钟。学习目标：检验条件独立假设，说明NB简单、快速、可解释的优点与局限，限定推广范围，并用低患病率场景回答作业原题。在线资源R2。')
    w.evidence('D1')
    w.answer('Q6条件独立：为检验表 B1背后“同一类别内各症状相互独立”的假设，请只用表 D1中真实类别为0的4行（共37条训练记录），不加平滑，写出P(尿意频繁=1且排尿痛=1 | Y=0)，以及P(尿意频繁=1 | Y=0)×P(排尿痛=1 | Y=0)，均用分式和小数表示。再用一句话说明两值是否接近，另一句说明为什么这个比较还不能证明总体中两症状独立或不独立。写三行。','Q6 条件独立',3)
    w.evidence('D2')
    w.answer('Q6复制症状：为评价NB的一项优点和一项局限，请读表 D2第1行（复制前后概率变化最大的向量），写出复制前后的阳性概率和变化方向；用一句话说明：复制恶心列没有增加任何新信息，为什么NB的概率仍会改变。再各用一句话写NB的一项优点（结合表 B1说明参数怎样得到）和一项局限（结合表 D1或表 D2）。写四行。','Q6 复制症状与优缺点',4)
    w.h('Q6 测试范围与低患病率',3)
    w.evidence('D3');w.evidence('D4')
    w.prompt('Q6作业原题“解释为什么医学诊断模型不能只看accuracy”——计算部分：请按表 D4的假设填写下表，每格写算式和结果（precision保留3位小数）。表 D4是假设场景，不是本数据的模型结果。')
    t=w.table(['要算的量','算式与结果'],[['患病人数；未患病人数',''],['TP；FN',''],['TN；FP',''],['模型的accuracy',''],['模型的precision',''],['全部预测为阴性时的accuracy；漏诊人数','']],[2.4,4.56],answer=True)
    for row in t.rows[1:]:row.height=Inches(.34)
    w.answer('Q6作业原题作答：用三至四句话回答“为什么医学诊断模型不能只看accuracy”。必须引用上方计算表中的两个accuracy和模型的precision，并联系表 C1中的一种错误类型（假阳性FP或假阴性FN），说明accuracy掩盖了什么。','Q6 作业原题作答',4)
    w.card('Q6更新追踪表第7行和第1行：在第7行“当前判断”格写表 D3“阈值0.50测试计数”一行能支持的一句结论，写明它对哪些记录成立，并用关键词并入你从表 D1、表 D2得到的结论；“反向证据”格引用表 D3中一个限制推广的数字，写出它使下列哪一种主张不能成立——对训练集中没有出现过的六项二值症状组合的预测，或对有独立来源的真实新患者的预测；“什么发现会改变判断”格写一项能让你放宽推广范围的新证据；“最后更新于”格写Q6。随后在第1行对照检查点C的冻结草案保留或修改第1页方案A–C，“最后更新于”格写Packet D。')
    w.new('课外综合：决策检验矩阵与研究备忘录初稿')
    w.p('本页已计入Q6的34分钟（约14分钟），不另加作业。')
    w.prompt('决策检验矩阵：为让研究组看到你为什么选这个方案、而不选另外两个，请为第1页方案A、B、C各填一行。只写已发放证据（表 S1至表 D4、图 C2）中已经观察到的发现，每格一条关键词，附证据编号和一个数字；确实没有时写“尚无”。将来可能出现的发现不写在这里，它们已记录在总答案追踪表“什么发现会改变判断”列。')
    t=w.table(['方案','已有证据中支持它的一项','已有证据中不利于它的一项'],[['A 保留当前基线','',''],['B 修改后冻结','',''],['C 暂缓提交','','']],[1.4,2.78,2.78],answer=True)
    for row in t.rows[1:]:row.height=Inches(.7)
    w.answer('研究备忘录初稿：请依据总答案追踪表第1至7行和决策检验矩阵，写150至250字交给研究组，按四部分写，每部分1至2句：①决定——所选方案（第1页A、B或C）及冻结或暂缓的具体内容（来自追踪表第1行）；②依据——最支持这个选择的两项证据，写出编号和数字（来自追踪表第2至6行中的任两行）；③为什么不选另外两个方案（来自决策检验矩阵“已有证据中不利于它的一项”列）；④边界——结论只适用于哪些记录和用途，以及哪一项新发现会让你改选（来自追踪表第7行和第1行）。作业原题已在Q6作答，这里不必重复。','个人研究备忘录初稿',8)
    w.p('提交检查点D：本册至本页的全部作答。保留计算过程；不要上传教师材料。翻转课堂上每个人都可能被随机抽到做白板说明，请准备好讲清自己的学习路径、一次判断修改和完整解题逻辑。')
    w.new('翻转课堂：独立训练与个人修订')
    w.p('课堂45分钟：前15分钟每人独立完成课堂训练①至③；随后随机抽1至2人白板说明12分钟，同伴提问6分钟，教师归纳5分钟，个人修订5分钟，退出条2分钟。白板说明按你自己的完整方案组织，没有固定讲稿，也不分组内角色。')
    w.h('课堂训练：只用两项症状重新训练NB')
    w.p('这是一次真正的参数估计和预测：输入只保留尿意频繁与排尿痛两项，标签仍为膀胱炎症；沿用表 B1的72条训练记录、先验35/72与37/72和加一平滑。其余四项症状的因子一律不进入乘积；分类阈值为0.50。')
    w.evidence('B3')
    w.prompt('课堂训练①参数：请用表 B1“尿意频繁”和“排尿痛”两行的计数，按加一平滑填写下表中的四个条件概率，写成分式。表 B3是验证记录，只用于课堂训练③的评价，不能用来估计参数。')
    t=w.table(['条件概率','阳性类（Y=1）','阴性类（Y=0）'],[['P(尿意频繁=1 | Y)','',''],['P(排尿痛=1 | Y)','','']],[2.4,2.28,2.28],answer=True)
    w.prompt('课堂训练②逐组合预测：请为下表四种症状组合各填一行：S1与S0（先验乘两个条件因子，症状为0时取1−θ，保留4位有效数字）、阳性后验S1/(S1+S0)（保留3位小数）和0.50阈值下的预测类别。同一症状组合无论真实标签是什么，预测都相同。')
    t=w.table(['尿意频繁','排尿痛','S1','S0','阳性后验','预测类别'],[['1','1','','','',''],['1','0','','','',''],['0','1','','','',''],['0','0','','','','']],[.9,.9,1.4,1.4,1.3,1.06],answer=True)
    for row in t.rows[1:]:row.height=Inches(.4)
    w.h('课堂评价与个人修订')
    w.prompt('课堂训练③评价：把课堂训练②的预测类别对应到表 B3的每一行，按该行“记录数”加权，填写下表（表 B3只有5行，却代表24条记录）。sensitivity和specificity写分式和小数；最后一行用一句话比较：与表 C1“0.50”行的六症状模型相比，二症状模型的错误类型和数量有何不同。')
    t=w.table(['要算的量','结果'],[['TP；FN',''],['FP；TN',''],['sensitivity',''],['specificity',''],['与表 C1“0.50”行比较','']],[2.4,4.56],answer=True)
    for row in t.rows[1:]:row.height=Inches(.36)
    w.answer('课堂同伴问题：白板说明结束后，针对被抽到同学讲的一步推理（须涉及表 B1、表 C1或表 D3中的一个数字），写一个能用证据检验的问题；再记下同伴回答或教师归纳中纠正的一个概念，并写出它影响总答案追踪表第几行。写三句。','课堂同伴问题与概念修正',3)
    w.answer('个人修订：重读研究备忘录初稿，依据课堂训练③的结果或“课堂同伴问题与概念修正”中记下的修正，写100至150字修订段落：说明保留还是改变第1页方案A–C，引用一个课堂上得到的数字或修正，并补写一项新的限定。写完后更新总答案追踪表第1行和受影响的那一行，“最后更新于”格写“课堂”。','个人研究备忘录修订段落',5)
    w.answer('课堂退出条（最后2分钟；课堂超时则课后2分钟内补写）：从表 C1、图 C2、表 C3、表 D3中选一项最改变你理解的证据，用一句话写它纠正了你原来的哪个想法；再写一个下次建模时你会主动检查的问题。写两句。','课堂退出条',2)
    w.new('数据来源与数据获取')
    w.p('除证据卡需要打开R2或R3核对原文外，完成必做题不需要编程或上网：所需数字都已在本册给出。辅助Notebook按Q1至Q6顺序组织，可离线运行；请只在领取相应Packet后运行对应单元，从头完整运行会提前显示Packet D的结果。')
    w.table(['资料','访问与核查信息'],[['数据','UCI Acute Inflammations；DOI 10.24432/C5V59S；https://archive.ics.uci.edu/dataset/184/acute%2Binflammations'],['许可及出处','CC BY 4.0；Jacek Czerniak，2009年入库。使用时保留来源、许可及本课的重编码说明。'],['文件与读取','原始diagnosis.data为UTF-16编码、制表符分隔、小数用逗号；变量说明在diagnosis.names。8列直接对应，无需合并。未观察到缺失；若重读时发现空值，应停下核查，不能默认填0。'],['本地副本','assets/pbl-machine-learning-basics-naive-bayes/acute-inflammations.csv，其中yes/no表示有无。Notebook在notebook/pbl-machine-learning-basics-naive-bayes-lab.ipynb。'],['预处理','体温≥38℃记为发热=1，五个症状yes/no转为1/0；膀胱炎症为主标签，肾炎不作为输入。38℃切点是教学预设，不是在测试集上搜索得到的。'],['R1','https://scikit-learn.org/stable/modules/cross_validation.html  3.1开头几段'],['R2','https://scikit-learn.org/stable/modules/naive_bayes.html  1.9开头与1.9.4'],['R3','https://scikit-learn.org/stable/modules/model_evaluation.html  3.4.4.6、3.4.4.9、3.4.4.12、3.4.4.15，以及Regression metrics中的Mean squared error'],['R4','https://scikit-learn.org/stable/modules/calibration.html  1.16.1']],[1.05,5.91])
    w.h('选做延伸（不计入必做时间与评分）')
    w.p('完成主任务后，可重算表 B2查询2，或按症状组合而不是按行号划分数据，观察结论如何改变。按组验证、跨医院验证、置信区间推导、Gaussian NB及其他算法比较属于后续学习；本课不要求从零实现。')
    w.p('提交前自查：六个模块的计算表都已填写；总答案追踪表每一行都有证据编号；检查点C的冻结草案在领取Packet D之前写好；作业原题在Q6作答；课堂训练中亲自估计了参数；证据卡中来自AI的说法已核对到R2或R3。')
    w.save('student-worksheet')

    # Evidence pack is student-safe; answer logic lives only in the teaching plan.
    e=Writer('分阶段证据包');e.page=1
    e.d.styles['Normal'].font.size=Pt(10);e.d.styles['Normal'].paragraph_format.line_spacing=1.02;e.d.styles['Normal'].paragraph_format.space_after=Pt(3)
    e.d.styles['Caption'].paragraph_format.line_spacing=1.0;e.d.styles['Caption'].paragraph_format.space_after=Pt(3)
    e.title('Packet A D Evidence Pack')
    e.p('发放规则：本包不含学生填答答案。不要一次发放全包；启动只用worksheet启动页，A/B/C/D分别在相应检查点后发布。所有证据也嵌入学生worksheet，Notebook不是找数字的唯一入口。')
    e.p('研究组要选择下一轮离线方法比较的基线。学生须交完整输入、训练、损失、评价与边界方案；A保持六症状NB与0.50，B修改后冻结，C补证据前暂不提交。')
    e.table(['模块','问题与证据','概念','分钟'],qmap,[.5,3.75,2.1,.61])
    e.p('A待查训练参数与损失；B后待查验证评价；C后仍待查类别内假设与固定测试；这些缺口分别由B、C、D提供。')
    for packet,keys in [('A',['A1','A2','A3']),('B',['B1','B2','B3','B4','B5']),('C',['C1','C3']),('D',['D1','D2','D3','D4'])]:
        e.new('Packet '+packet+' 证据与核查')
        for key in keys:
            if key=='D3': e.new('Packet D 测试与迁移')
            e.evidence(key)
        if packet=='C':
            e.p('图 C2  同24条验证记录；ROC与PR曲线，三处阈值同表 C1。')
            e.d.add_picture(str(ASSET/'packet-c2-ranking.png'),width=Inches(6.9))
            e.table(['概率表示','ROC-AUC','梯形PR面积','AP','平均交叉熵'],[['p',1,1,1,round(M['val_log_loss'],4)],['0.25+0.50p',1,1,1,round(M['transformed_log_loss'],4)]])
        prompts={'A':'核查：表 A2来源与表 A3分割分别允许你如何界定记录和评价？回到追踪表第2/3行说明A/B/C的理由还缺什么。','B':'核查：表 B1的分母与表 B4的概率损失如何改变你的模型理解？更新追踪表第4/5行及第1行，不以计算透明推断因果解释。','C':'核查：表 C1的错误数量、图 C2的排序与表 C3的概率频率，分别支持哪一种评价？把选定阈值写入第6行，冻结第1行配置后才看D。','D':'核查：表 D1、表 D2、表 D3是否要求改变第7行的假设或使用范围？用表 D4补充accuracy作业，再整合第1至7行，而非只写临床不可用。'}
        e.p(prompts[packet])
    e.new('证据的来源与边界')
    e.p('原始来源：UCI Acute Inflammations，https://doi.org/10.24432/C5V59S，CC BY 4.0。记录为医学专家设计的潜在病例；不能从公开资料确认独立临床队列。原文件UTF-16与说明ASCII不一致；本课显式读取并保留来源，没有删除重复记录。')
    e.p('B4、B5、D4是明确给定输入的教学构造；D2是对输入列的干预与64种组合穷举。它们不是额外患者资料。所有数值由固定划分及教学输入重算；作者曾看过固定测试，课堂只模拟冻结后解封。')
    e.p('本包支持学习参数估计、损失、分类/排序/概率评价与假设审查，不支持因果结论、真实患者风险保证或临床部署。表 D3的组合重复不单独证明泄漏；应结合来源和抽样过程判断。')
    e.save('evidence-pack')

    t=Writer('教师用书 含参考答案');t.page=1;t.title('PBL Flipped Classroom Teacher Plan')
    t.table(['项目','安排'],[['学生','生命科学高年级直博预备生；标准微积分、数理统计与前六讲；不预设CS训练。'],['组织','45分钟启动＋120分钟个人自学＋45分钟翻转课堂；教师讲授以追问和5分钟归纳为主。'],['数据','同一UCI数据120×8；六输入，两标签；主标签59阳性/61阴性。'],['总问题','向研究组交完整预测研究方案，选择保留、修改或暂缓基线。'],['学习产物','worksheet中的六模块、追踪表、证据卡、研究备忘录及课堂训练；Notebook仅辅助。']],[1.1,5.86])
    t.p('教师专用：本文件含参考计算及判卷逻辑，不向学生提前发放。所有个体均应准备完整解释，随机抽1至2人；不设置固定小组角色。')
    t.new('按源大纲验收学习行为')
    for cov in design['course_coverage']:
        t.p(cov['objective_id']+'  '+cov['observable_outcome']+'  对应'+','.join(cov['inquiry_question_ids']))
    t.new('三阶段组织与发放')
    t.table(['启动分钟','动作','学生写答位置'],phase1,[.6,4.3,2.06])
    t.p('启动讨论允许错误。用表 S1的来源与用途让初选有理由；不要透露最终100%成绩。先问“你缺什么资料”而非解释全部算法。流程正确顺序丙→戊→丁→甲→乙，启动时只收初想，Q2再修。')
    t.table(['自学模块','证据及检查点','预算'],[[q[0],q[1],q[3]+'分钟'] for q in qmap],[.7,5.35,.91])
    t.p('平台依次释放A/B/C/D：A交Q1/Q2和追踪更新，B交Q3/Q4及证据卡，C交Q5及冻结配置，D交综合初稿。R1至R4均给到具体章节，worksheet概念读页足够完成核心题；不要求通读英文文档。AI可用于解释或核对，证据卡必须把一个主张与源资料及案例数字核验。')
    t.table(['翻转分钟','组织','可观察产出'],[['15','每人训练二症状NB并汇总24条验证','参数、各组合后验、敏感度和特异度'],['12','随机1至2人白板说明','自己的证据链与一次修订'],['6','同伴针对证据提问','具体问题及回应'],['5','教师归纳相邻概念差异','分母、条件独立与泛化的纠偏'],['5','个人修订100至150字','备忘录修订和追踪表更新'],['2','退出条','一个概念变化与下一次检查']],[.65,3.4,2.91])
    t.new('Q1与Q2 任务和流程参考')
    t.p('Q1：输入为体温二值化的发热及五项症状；主标签是膀胱炎症。另一个疾病决策不属于本课指定六症状任务，且其预测时可用性未确立；不要一概说任何其他疾病标签都必然泄漏。fθ给出模型阳性概率，阈值给类别。关联检验针对总体关系；预测要评估新输入的表现，两者不等价。')
    t.p('Q2：训练72条拟合先验与条件概率；固定参数预测验证24条；验证比较阈值；冻结配置不需新样本；测试24条只评价被冻结配置。看test后改阈值把test用作选择，后续需另一个未使用测试集。行号不交叉不等于输入组合、患者或来源独立。')
    t.p('合理追问：若方案A是教学比较基线，为何仍可保留它？若选C，到底哪个未决证据会让你改选A或B？仅答“样本小，不能临床”而不给研究流程不能获得综合题高分。')
    t.h('来源核对')
    t.p('官方说明是专家设计潜在病例；不添加未公开生成机制。UTF-16与文档ASCII矛盾、体温范围、yes/no层级、零缺失及重复均写入表 A2。保留全部行，避免暗中改变与已有分析对应的样本。二值化切点38℃仅教学预设，不说由此发现医学最佳阈值。')
    t.new('Q3 参数估计参考')
    t.evidence('B1')
    t.p('先验35/72与37/72。阳性类每个θ分母37；阴性类分母39。P(尿意频繁=1|Y=1)=(35+1)/37=36/37；P(恶心=0|Y=0)=1−(5+1)/39=33/39。所有数字以表 B1为准。')
    # Derive the hand solution directly rather than relying on hardcoded counts.
    countrows=T['B1']['rows'];fac=[]
    x=[0,0,0,1,1,0]
    for c,n,index in [(1,35,1),(0,37,2)]:
        nums=[(int(row[index])+1 if xx else n-int(row[index])+1) for row,xx in zip(countrows,x)]
        score=(n/72)
        for num in nums:score*=num/(n+2)
        t.p(f'查询1：S{c} = {n}/72 × '+' × '.join(f'{v}/{n+2}' for v in nums)+f' = {score:.8f}。')
    t.p(f"归一化查询1阳性后验={M['query_probabilities'][0]:.6f}；查询2={M['query_probabilities'][1]:.6f}（选做）。查询1按0.50预测阳性。若学生漏掉症状0的补概率，要求回到二元概率定义，不直接给乘积答案。")
    t.p('六个关键词的出现/未出现适配Bernoulli表示；词频是非负计数，不符合每列只有0/1的这一似然，应改表示或选择与计数匹配的模型。可解释的是参数与计算路径，不是因果机制。零计数问题通过加一平滑处理；不要声称它证明独立。')
    t.new('Q4 损失参考与概念边界')
    t.p(f"表 B4两模型0.50阈值均预测[1,0,0,0]，accuracy=3/4。模型甲损失={M['loss_A']:.6f}，模型乙={M['loss_B']:.6f}；记录3为阳性却预测0.4或0.01，对应−ln0.4=0.916291与−ln0.01=4.605170。三次很小损失不能抵消一次极自信错误。")
    t.p('表 B5平方误差为1和4，MSE=2.5℃²；不是RMSE，也不是2.5℃。不能把不同预测对象、不同单位或评分规则的原始损失数值直接比高低。')
    t.p('训练细节：Bernoulli NB可用生成模型的类别条件计数估计；这里加一平滑。不能说“NB没有任何损失/似然”，也不能说该实现直接最小化了验证条件log loss。推导联合似然不在本课考核范围。')
    t.p('证据卡接受一个短而可检验的文档/AI主张，如“二元NB把未出现的信息纳入模型”。学生需引用本例0症状的补概率，给来源小节，再限定二元表示与条件独立。只有聊天截图或泛泛“AI说正确”不足。')
    t.new('Q5 分类 排序 校准参考')
    t.p('阈值0.10：accuracy=19/24=0.7917；sensitivity=recall=12/12=1；specificity=7/12=0.5833；precision=12/17=0.7059；F1=24/29=0.8276。先验基线无阳性预测，precision分母0，未定义；软件zero_division约定不改变数学含义。F1按2TP/(2TP+FP+FN)可得0。')
    t.p('阈值从0.10提高到0.50，FP由5到0且FN仍0；再到0.90，FP仍0而FN变2。已给候选中0.50在此验证集表现最好，但这不证明任意新分布或成本下最佳。成本未知应明确，不必人为为了高敏感度一律降阈值。')
    t.p(f"图 C2阈值0.10：ROC点=(5/12,1)；PR点=(1,12/17)。ROC-AUC、梯形PR面积与AP均1。严格递增变换0.25+0.50p保留排序，平均log loss却从{M['val_log_loss']:.4f}变为{M['transformed_log_loss']:.4f}；说明排序与概率评分不是同一个量。不能仅由这项损失差把改善全部归因于校准。")
    t.evidence('C3')
    smallest=min(T['C3']['rows'],key=lambda r:r[1]);t.p('最小非空箱：'+str(smallest)+f'；实际阳性比例减平均预测概率={smallest[4]-smallest[3]:+.4f}（学生册要求此方向）。小箱频率随机性很大；观察差异不能直接证明总体校准/失校准，亦不能由分类全对推出概率精确。')
    t.p('可接受报告：混淆矩阵与敏感度/特异度/precision，加明确阈值；ROC与PR及阳性比例、积分方式；log loss和带人数的校准表。Brier同时受多个概率预测性质影响，不是纯校准误差。AP与梯形PR面积相等只是此例，不能混名。')
    t.new('Q6 假设 泛化 与综合参考')
    pos=[r for r in T['D1']['rows'] if r[0]==0];joint=sum(r[3] for r in pos if r[1:3]==[1,1]);a=sum(r[3] for r in pos if r[1]==1);b=sum(r[3] for r in pos if r[2]==1)
    t.p(f'阴性类：联合={joint}/37={joint/37:.4f}；边缘乘积=({a}/37)×({b}/37)={a*b/37**2:.4f}。经验频率不等，提示乘积假设不符合该有限表的联合分布；不是总体独立性检验。若对照阳性类，会发现尿意频繁恒为1导致经验相等；也不能由此证明所有症状总体条件独立。')
    t.p(f"复制恶心不增加信息，但乘积模型对该条件概率再计一次权重。64种向量有{M['duplicate_class_changes']}种跨0.50类别边界，最大概率变化{M['duplicate_max_change']:.4f}；它们不是观测患者。朴素模型训练仅需计数，成本随记录×特征近似线性；小模型参数可追溯，但依赖可能影响概率，解释不等于因果。")
    t.p('表 D3仅支持固定教学分割上24条全部正确；这些二值组合都在训练出现，不证明新组合、真实新患者、跨机构泛化。重复组合本身不是泄漏的充分证据；来源、重复行、无患者身份共同限制独立性主张。作者曾看test，不包装成全新盲测。')
    t.p('表 D4：患病100、无病9900；TP95、FN5、FP495、TN9405；precision=95/590≈16.10%。此假设模型accuracy=9500/10000=95%；全阴性基线accuracy=99%，却漏掉全部100名患者。说明错误结构、阳性组成及使用代价不能被一个accuracy取代；这些是假设外推，不是本课数据性能。')
    t.p('决策检验矩阵只收已发放证据中已观察到的发现（附编号和数字），将来可能的发现属于追踪表“什么发现会改变判断”列；学生写“尚无”是允许的，例如B的支持证据可能只有表 D1或表 D2提示的假设问题。备忘录150至250字，四段依次为决定、依据、为何不选另两个方案、边界，应能在追踪表和矩阵中找到出处。')
    t.p('综合备忘录评分不限定A/B/C。A可保留为方法学基线且明确适用范围；B须指出实际修改及仅用训练/验证重新选配置，不能声称未测的新模型更好；C须指定待补证据及其改判作用。三者均需纳入Q1至Q6，不允许靠“不能临床”跳过学习。')
    t.new('课堂训练答案与评分')
    t.p('二症状模型先验仍35/72与37/72。两症状θ按表 B1各自计数加一，不能使用验证计数。删除四个症状改变了模型，必须重新计算乘积；不能把六症状概率当作答案。')
    t.table(['尿意频繁','排尿痛','真实标签','记录数','阳性后验','预测类别'],[[*r[:4],f'{r[4]:.6f}',r[5]] for r in M['two_results']])
    tn,fp=M['two_confusion'][0];fn,tp=M['two_confusion'][1]
    t.p(f'合计TN={tn}、FP={fp}、FN={fn}、TP={tp}；sensitivity={tp}/{tp+fn}={tp/(tp+fn):.4f}；specificity={tn}/{tn+fp}={tn/(tn+fp):.4f}。聚合表按记录数加权，不按表格行计数。')
    t.table(['评分项','权重','达标证据及部分分'],[['任务与流程','20%','Q1 8分：变量与预测对象；Q2 12分：数据职责、冻结与测试用途。'],['NB训练与预测','25%','Q3 15分：先验、平滑、0值因子、归一化与文本迁移；课堂10分：亲自拟合与加权评价。'],['损失理解','15%','Q4交叉熵比较8分、MSE与单位4分、证据卡3分。'],['分类 排序 概率','25%','Q5分类分母10分、阈值理由5分、AUC/PR5分、校准及人数5分。'],['假设与综合方案','15%','Q6条件独立与重复信息4分、迁移反例4分、六模块整合及边界7分。']],[1.35,.65,4.96])
    t.p('算术失误但分母/方法正确给方法分；不因选C自动加分，不因100%分数加分。优秀答案能主动引用反向证据，并说明改变判断的条件。抄概念而没有表中数字不能满足对应案例分析项。')
    t.new('教师归纳与实施风险')
    t.p('5分钟归纳只抓三组混淆：训练与预测及验证选择；P(症状|疾病)与P(疾病|症状)及条件独立；分类、排序、概率与目标人群。先用学生的具体错误追问，再给最小必要解释。')
    t.p('工作量：120分钟是强生物背景学生、允许计算器并只阅读指定短段的设计预算，不是实测保证。若英文阅读卡住，先读本册概念页；若算乘积慢，让学生先保留分数因子再用计算器。不要添加肾炎重训、置信区间推导等必做任务。')
    t.p('分阶段技术风险：完整Notebook从头执行会泄露D；课程平台按Packet分发worksheet页面并注明只运行对应单元。教师持有全册，学生最终保存合并个人作答版。质量检查及红字试填文件仅教师可见，不上传给学生。')
    t.p('若真实课堂出现大面积超时，应记录实际用时并减少重复抄写或把同伴回应移至课后，不静默删掉源大纲目标。真实学生试教仍是后续应做的检验；AI模拟不代替这一证据。')
    t.save('teaching-plan-flipped-classroom')

    r=Writer('教学设计说明');r.page=1;r.title('Purpose Design Rationale Expected Outcomes')
    r.h('为什么重构这一课')
    r.p('这批学生有生物学、微积分和数理统计基础，但没有稳定的算法背景。直接讲大量指标公式会让学习退化为记名词；只让Notebook跑出高分又掩盖了输入、参数、阈值和使用范围之间的区别。本课要求第一次形成能被另一位研究者复核的预测研究方案。')
    r.h('为什么采用这组问题')
    r.p('主问题是下一轮离线方法比较的基线决策，允许保留、修改或暂缓；它不能被一个分数或“不能临床”的结论完成。六模块将模型、训练流程、Bayes计算、损失、评价及假设连接到同一张追踪表。难度来自分母、计算与证据推断，不依赖工程技能。')
    r.table(['模块','覆盖簇','最终方案中的责任'],[['Q1','数据模型 特征 标签','明确研究对象与输入输出'],['Q2','训练 预测 泛化 划分','给出可复核的数据职责'],['Q3','Bayes Bernoulli 文本迁移','解释参数从何而来及预测过程'],['Q4','损失 交叉熵 MSE','说明概率与连续误差怎样衡量'],['Q5','分类 排序 校准','形成不混淆的评价报告'],['Q6','条件独立 优缺点 迁移','限定主张并给出下一步']],[.6,3,3.36])
    r.p('原大纲课堂训练与sensitivity/specificity计算保留在翻转课堂前15分钟；原题“解释为什么医学诊断模型不能只看 accuracy”保留为Q6“作业原题”的计算表与作答框，备忘录不再重复作答。前六讲仅作为数据/统计基础，不借本课加入后续验证课程的完整内容。')
    r.new('数据和分析选择')
    r.p('保留用户已选UCI Acute Inflammations，便于六项症状的手算与可解释训练。主标签为膀胱炎症，不把另一疾病决策偷当输入。其来源是专家设计潜在病例，非可确认的独立患者队列；这使它适合算法教学，却不能承担临床效果证明。')
    r.p('120条保留原始重复；固定72/24/24分层与种子7，不选择漂亮划分。预设38℃把六输入统一为Bernoulli，原始99种输入变为9种组合，代价在D公开审查。测试作者已见，透明称固定教学测试；课堂冻结是教学流程，不是假装全新盲测。')
    r.p('为了让完整大纲在一个数据背景中可做：B4用四条合成概率对照呈现accuracy与交叉熵差异；B5以两条连续体温目标使MSE实际可算；C使用验证阈值0.10/0.50/0.90制造的是同数据上的真实取舍，不改标签。严格递增概率变换说明排序不等于概率质量。D4的1%患病率反例明确是假设场景，不当作模型外部验证。')
    r.p('不把有限经验频率的比较当作总体独立性证明：D1必做计算选阴性类，联合频率与边缘乘积不同；阳性类存在常量症状，可供教师说明相等也不是普遍证明。D2复制一列展示朴素乘积对冗余信息的敏感性；64种向量是设计空间，不是患者样本量。')
    r.h('预期学习压力与支架')
    r.p('不给推导优化算法的负担，但保留先验、平滑、0值因子与后验归一化；给指标公式却要求解释具体分母；给AUC结果却要求算点坐标与说明边界；给原始频数而不把判断写进证据。可用AI，必须用证据卡核查一个案例主张。')
    r.new('覆盖链与考核')
    for cov_i,cov in enumerate(design['course_coverage']):
        if cov_i in [5,10]:r.new('覆盖链与考核续页')
        r.h(cov['objective_id']+' '+','.join(cov['inquiry_question_ids']),3)
        r.p('来源要求：'+cov['source_excerpt'])
        r.p('可观察产出：'+cov['observable_outcome']+'；证据：'+'、'.join(cov['evidence_ids'])+'；最终使用：'+cov['synthesis_use'])
    r.new('阅读设计与质量验收')
    r.p('沿用课程已有worksheet的浅蓝表头、Arial文字与0.65英寸页边距；按本次批准改为A4，中文用微软雅黑10.5pt，表格10pt，极宽原始数据表9pt。短题卡直接置于可编辑答案表之前；追踪表仅一份，行名与模块引用一致。独立分页允许教师按阶段发放，避免Notebook变成唯一教材。')
    r.p('质量门：分析设计逐目标覆盖检查与worksheet lint应为0错误；冷读检查每个指代与选项；新读者只看学生文件逐格试填，记录估计时间与阻塞，修订后复查。四份DOCX均转PDF/页面图检查；Notebook离线执行验证核心数字。实际检查报告存review，不能以模板存在代替通过。')
    r.p('本课不声称：真实患者诊断有效、跨医院泛化、概率风险已校准、观察性关联具有因果意义、AI试填能替代真实学生试教。精确的内部成绩和数字重算只证明固定教学流程可复核。')
    r.p('迁移时，学生应先换对象与标签、重审预测时可用输入、明确数据职责，再选择损失与报告指标，最后核查模型假设和新环境的证据。不能把本课38℃切点、0.50阈值或50%验证阳性比例原样移植。')
    r.p('原大纲来源：D:/XMU/AI4BiomedicalDS/plan.docx第7讲；课程专属批准设计及逐目标覆盖保存在本课planning和assets。未修改pbl-ml-package技能文件。')
    r.save('design-rationale')
    write_notebook()
    manifest={'topic':TITLE,'slug':'machine-learning-basics-naive-bayes','mode':'PBL + flipped classroom','dataset':{'name':'UCI Acute Inflammations','source':'https://doi.org/10.24432/C5V59S','license':'CC BY 4.0','task':'binary teaching classification','target':'bladder_inflammation'},'outputs':{k:f'{SLUG}-{k}.docx' for k in ['student-worksheet','evidence-pack','teaching-plan-flipped-classroom','design-rationale']},'boundary':'Teaching only; no clinical, deployment, causal or patient-care claim.','core_question':design['problem_architecture']['overarching_problem'],'problem_architecture':design['problem_architecture'],'course_coverage':design['course_coverage'],'customized':True,'course_brief':'../../../../plan.docx','analysis_design':f'assets/{SLUG}/analysis-design.json','build_script':f'scripts/{SLUG}-build.py','analysis_script':'scripts/lesson7_analysis.py','assets':[str(p.relative_to(ROOT)).replace('\\','/') for p in ASSET.iterdir() if p.is_file()], 'qa':{'lint':f'review/{SLUG}-lint.md','design':'review/design-check.md','pilot_fill':f'review/{SLUG}-pilot-fill.docx','pilot_report':f'review/{SLUG}-pilot-report.md','release_status':'2026-09-17试填后修订：lint与design 0错误，self-pilot 0阻塞，课外估计约131/120分钟；待真实课堂记录用时'}}
    manifest['outputs']['notebook']=f'notebook/{SLUG}-lab.ipynb'
    active_assets={'acute-inflammations.csv','analysis-design.json','computed-evidence.json','dataset-summary.csv','split-indices.csv','validation-predictions.csv','redundancy-all64.csv','packet-c2-ranking.png',*[f'packet-{label.lower()}.csv' for label in T],*[f'equation-{x}.png' for x in ['bayes','bernoulli','loss','mse']]}
    manifest['assets']=[f'assets/{SLUG}/{name}' for name in sorted(active_assets)]
    manifest['legacy_note']='Older unlisted assets are retained for recoverability, not part of this release. Prior notebooks and generator are preserved under planning/archive-before-20260917.'
    (ROOT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

def write_notebook():
    import nbformat as nbf
    nb=nbf.v4.new_notebook();cells=[]
    def md(x):cells.append(nbf.v4.new_markdown_cell(x))
    def code(x):cells.append(nbf.v4.new_code_cell(x))
    md('# 第7讲 机器学习基础与朴素贝叶斯 辅助实验\n核心学习与答案写在Word worksheet。Notebook只供重现和核对；不需要从零编程。按已发Packet执行，不要提前运行D；完整执行仅供教师复现。全部数据离线可用，禁止临床应用。')
    code("from pathlib import Path\nimport sys, json, itertools\nimport numpy as np\nimport pandas as pd\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.naive_bayes import BernoulliNB\nfrom sklearn.metrics import confusion_matrix, log_loss, mean_squared_error, roc_auc_score, precision_recall_curve, average_precision_score, auc, brier_score_loss\nroot = Path.cwd().resolve()\nif root.name == 'notebook': root = root.parent\nassert (root/'assets').exists(), '请从本课目录或notebook目录运行'\nassets = root/'assets/pbl-machine-learning-basics-naive-bayes'\ndf = pd.read_csv(assets/'acute-inflammations.csv')\nprint('Python:', sys.executable)\nprint(df.shape)\ndisplay(df.head())")
    md('## Packet A Q1 记录与表示\n一行不是已确认独立患者。核对层级、缺失、重复与连续/二值表示；不要静默去重。')
    code("assert df.shape == (120,8)\nassert df.isna().sum().sum() == 0\ndisplay(df.describe(include='all'))\nprint('全行重复余量:', df.duplicated().sum(), '重复组总行:', df.duplicated(keep=False).sum())\nprint('原始输入组合:', df.iloc[:,:6].drop_duplicates().shape[0])\nX = np.column_stack([(df.iloc[:,0]>=38).astype(int), *(df[c].eq('yes').astype(int) for c in df.columns[1:6])])\ny = df['bladder_inflammation'].eq('yes').to_numpy(dtype=int)\nprint('二值组合:', np.unique(X,axis=0).shape[0], '类别计数:', np.bincount(y))")
    md('## Q2 固定数据职责\n先保留20%测试，再从剩余80%中取25%为验证，总比例60/20/20。不根据分数换种子。')
    code("dev, te = train_test_split(np.arange(len(y)), test_size=.2, random_state=7, stratify=y)\ntr, va = train_test_split(dev, test_size=.25, random_state=7, stratify=y[dev])\nassert not (set(tr)&set(va) or set(tr)&set(te) or set(va)&set(te))\nfor name, ix in [('训练',tr),('验证',va),('测试',te)]: print(name, len(ix), np.bincount(y[ix]))\nsaved=pd.read_csv(assets/'split-indices.csv')\nfor label,ix in [('tr',tr),('va',va),('te',te)]: assert saved.loc[saved.split==label,'source_row'].tolist()==(ix+1).tolist()")
    md('## Packet B Q3 用计数训练\n模型估计每类中各症状为1的概率，加一平滑；0症状使用补概率。先手算worksheet查询1，再运行核对。')
    code("counts=np.array([X[tr][y[tr]==c].sum(axis=0) for c in [0,1]])\nn=np.bincount(y[tr]); theta=(counts+1)/(n[:,None]+2); priors=n/n.sum()\nmodel=BernoulliNB(alpha=1).fit(X[tr],y[tr])\nassert np.allclose(theta,np.exp(model.feature_log_prob_))\nq=np.array([0,0,0,1,1,0])\nfactors=np.where(q,theta,1-theta)\nscores=priors*factors.prod(axis=1); post=scores/scores.sum()\nprint('counts',counts,'theta',theta,'priors',priors,sep='\\n')\nprint('因子',factors,'类别分数',scores,'后验',post,sep='\\n')\nassert np.allclose(post,model.predict_proba([q])[0])\nsaved_counts=pd.read_csv(assets/'packet-b1.csv'); assert np.array_equal(saved_counts.iloc[:,1:].to_numpy(),counts[[1,0]].T)")
    md('反思：为什么查询中0值的症状仍要参与乘积？若把关键词出现改成频次，这个式子改变了什么？')
    md('## Q4 两种损失\n以下是明确给定输入的合成教学例，不是额外患者。')
    code("toy_y=np.array([1,0,1,0]); pa=np.array([.8,.2,.4,.1]); pb=np.array([.99,.01,.01,.01])\nfor name,p in [('甲',pa),('乙',pb)]:\n    per=-(toy_y*np.log(p)+(1-toy_y)*np.log(1-p))\n    print(name,'逐例损失',per,'平均',per.mean(),'accuracy',((p>=.5)==toy_y).mean())\n    assert np.isclose(per.mean(),log_loss(toy_y,p))\nprint('MSE',mean_squared_error([37,39],[38,37]),'℃²')\nassert mean_squared_error([37,39],[38,37])==2.5")
    md('## Packet C Q5 分类、排序与概率\n所有选阈值动作只使用验证；先写冻结配置再运行D。')
    code("p=model.predict_proba(X[va])[:,1]\nrows=[]\nfor threshold in [.1,.5,.9]:\n    tn,fp,fn,tp=confusion_matrix(y[va],p>=threshold,labels=[0,1]).ravel()\n    rows.append([threshold,tn,fp,fn,tp,(tp+tn)/len(va),tp/(tp+fn),tn/(tn+fp),tp/(tp+fp),2*tp/(2*tp+fp+fn)])\nmetric_table=pd.DataFrame(rows,columns=['threshold','TN','FP','FN','TP','accuracy','sensitivity','specificity','precision','F1'])\ndisplay(metric_table)\nassert np.array_equal(metric_table.iloc[:3,1:5].to_numpy(),pd.read_csv(assets/'packet-c1.csv').iloc[:3,1:].to_numpy())\nprint('先验基线precision分母为0：未定义；recall=0。')")
    code("import matplotlib.pyplot as plt\nfrom sklearn.metrics import roc_curve\nfpr,tpr,_=roc_curve(y[va],p); precision,recall,_=precision_recall_curve(y[va],p)\nfig,ax=plt.subplots(1,2,figsize=(9,3))\nax[0].plot(fpr,tpr);ax[0].set(xlabel='False positive rate',ylabel='Sensitivity',title='Validation ROC')\nax[1].plot(recall,precision);ax[1].set(xlabel='Recall',ylabel='Precision',title='Validation PR');plt.show()\nfor name,prob in [('original',p),('0.25+0.50p',.25+.5*p)]:\n    pp,rr,_=precision_recall_curve(y[va],prob)\n    print(name, 'ROC',roc_auc_score(y[va],prob),'PR trapezoid',auc(rr,pp),'AP',average_precision_score(y[va],prob),'logloss',log_loss(y[va],prob))\n# 非完美排序支持例，说明AP与梯形PR面积一般不等\npp,rr,_=precision_recall_curve([1,0,1,0],[.9,.8,.7,.1])\nprint('Optional illustration: AP',average_precision_score([1,0,1,0],[.9,.8,.7,.1]),'PR trapezoid',auc(rr,pp))")
    code("cal=[]\nfor lo,hi in [(0,.1),(.1,.5),(.5,.9),(.9,1)]:\n    mask=(p>=lo)&((p<hi) if hi<1 else (p<=hi))\n    if mask.sum(): cal.append([lo,hi,int(mask.sum()),int(y[va][mask].sum()),p[mask].mean(),y[va][mask].mean()])\ncal=pd.DataFrame(cal,columns=['lower','upper','n','positive','mean_p','observed_rate']);display(cal)\nsaved_cal=pd.read_csv(assets/'packet-c3.csv')\nassert np.allclose(cal.iloc[:,2:].to_numpy(),saved_cal.iloc[:,1:].to_numpy(),atol=5e-5)\nprint('Brier',brier_score_loss(y[va],p),'（不是纯校准误差）')")
    md('反思：什么性质被单调变换保留？每箱人数怎样限制校准结论？')
    md('## Packet D Q6 条件独立与复制输入\n此处仅在D解封后运行。64种穷举向量不等于64患者。')
    code("joint=[]\nfor c in [1,0]:\n    for a,b in itertools.product([0,1],repeat=2):\n        joint.append([c,a,b,int(((y[tr]==c)&(X[tr,3]==a)&(X[tr,4]==b)).sum())])\ndisplay(pd.DataFrame(joint,columns=['class','urine','pain','n']))\nassert np.array_equal(np.array(joint),pd.read_csv(assets/'packet-d1.csv').values)\ngrid=np.array(list(itertools.product([0,1],repeat=6)))\ndup=BernoulliNB(alpha=1).fit(np.column_stack([X[tr],X[tr,1]]),y[tr])\npg=model.predict_proba(grid)[:,1];pdg=dup.predict_proba(np.column_stack([grid,grid[:,1]]))[:,1]\nprint('类别改变',((pg>=.5)!=(pdg>=.5)).sum(),'最大概率差',abs(pg-pdg).max())\nassert np.allclose(np.column_stack([grid,pg,pdg]),pd.read_csv(assets/'redundancy-all64.csv').to_numpy())")
    code("testp=model.predict_proba(X[te])[:,1]\nprint('固定测试',confusion_matrix(y[te],testp>=.5,labels=[0,1]),'log loss',log_loss(y[te],testp))\ntrain_patterns=set(map(tuple,X[tr]));raw=df.iloc[:,:6].astype(str).to_numpy();raw_train=set(map(tuple,raw[tr]))\nfor name,ix in [('validation',va),('test',te)]:\n    print(name,'binary patterns',len(set(map(tuple,X[ix]))),'seen',sum(tuple(v) in train_patterns for v in X[ix]),'raw seen',sum(tuple(v) in raw_train for v in raw[ix]))\nassert np.array_equal(confusion_matrix(y[te],testp>=.5),[[12,0],[0,12]])\nTP,FN,FP,TN=95,5,495,9405\nprint('假设低患病率precision',TP/(TP+FP),'accuracy',(TP+TN)/10000,'all negative accuracy',.99)")
    md('## 翻转课堂 二症状训练复现\n仍从训练72条拟合，仅保留尿意频繁与排尿痛；验证24条按人数加权。')
    code("two=BernoulliNB(alpha=1).fit(X[tr][:,[3,4]],y[tr])\nclassroom=pd.read_csv(assets/'packet-b3.csv')\nclassroom['posterior']=two.predict_proba(classroom.iloc[:,:2].to_numpy())[:,1]\nclassroom['prediction']=(classroom['posterior']>=.5).astype(int);display(classroom)\ncm=confusion_matrix(y[va],two.predict(X[va][:,[3,4]]),labels=[0,1]); print(cm)\nweighted=np.zeros((2,2),dtype=int)\nfor row in classroom.itertuples(index=False,name=None): weighted[int(row[2]),int(row[5])]+=int(row[3])\nassert np.array_equal(cm,weighted)\ntn,fp,fn,tp=cm.ravel();print('sensitivity',tp/(tp+fn),'specificity',tn/(tn+fp))\nprint('核心复现检查全部通过。')")
    md('最终反思：把任务、数据职责、训练、损失、分类/排序/校准和假设写进同一研究备忘录。选择A、B、C都需证据；不要把固定教学测试当成真实部署证据。')
    nb.cells=cells;nb.metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3'}}
    nbf.write(nb,ROOT/'notebook'/f'{SLUG}-lab.ipynb')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--docs',action='store_true');parser.add_argument('--all',action='store_true');args=parser.parse_args()
    REVIEW.mkdir(exist_ok=True)
    if args.all: subprocess.run([sys.executable,str(ROOT/'scripts/lesson7_analysis.py')],check=True)
    if args.docs or args.all: build_docs()
    else: parser.error('use --docs after numerical generation, or --all in a compatible environment')
