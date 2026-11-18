from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(r"C:\Users\zml\Documents\Codex\2026-09-16\ctrl-cmd-shift-p-python-create-2")
OUT_DIR = ROOT / "10. Ensemble" / "submission_materials"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "CTG_Ensemble_Learning_Conference_Paper_7pages.docx"
FIG = OUT_DIR / "fig1_model_comparison.png"
FIG2 = OUT_DIR / "fig2_tree_convergence.png"
FIG3 = OUT_DIR / "fig3_stability.png"
FIG4 = OUT_DIR / "fig4_feature_importance.png"
FIG5 = OUT_DIR / "fig5_evidence_map.png"
FIG6 = OUT_DIR / "fig6_validation_operating_points.png"
FIG7 = OUT_DIR / "fig7_cv_summary.png"
FIG8 = OUT_DIR / "fig8_grouped_protocol.png"

NAVY = "000000"; BLUE = "1F4E79"; LIGHT = "FFFFFF"; GRID = "000000"

def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), fill); tcPr.append(shd)
def set_cell_margin(cell, top=80, start=90, bottom=80, end=90):
    tc = cell._tc; tcPr = tc.get_or_add_tcPr(); mar = tcPr.first_child_found_in('w:tcMar')
    if mar is None: mar = OxmlElement('w:tcMar'); tcPr.append(mar)
    for side, v in [('top',top),('start',start),('bottom',bottom),('end',end)]:
        el = mar.find(qn('w:'+side))
        if el is None: el = OxmlElement('w:'+side); mar.append(el)
        el.set(qn('w:w'), str(v)); el.set(qn('w:type'), 'dxa')
def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr(); x = OxmlElement('w:tblHeader'); x.set(qn('w:val'), 'true'); trPr.append(x)
def set_table_borders(table):
    tblPr=table._tbl.tblPr; borders=OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'6'); e.set(qn('w:color'),'000000'); borders.append(e)
    tblPr.append(borders)
def set_column_section(section, cols):
    sectPr = section._sectPr; old = sectPr.find(qn('w:cols'))
    if old is not None: sectPr.remove(old)
    c=OxmlElement('w:cols'); c.set(qn('w:num'),str(cols)); c.set(qn('w:space'),'360'); sectPr.append(c)
def font(run, size=9, bold=False, italic=False, color=None):
    run.font.name='Times New Roman'; run._element.rPr.rFonts.set(qn('w:eastAsia'),'瀹嬩綋'); run._element.rPr.rFonts.set(qn('w:ascii'),'Times New Roman'); run._element.rPr.rFonts.set(qn('w:hAnsi'),'Times New Roman'); run.font.size=Pt(size); run.bold=bold; run.italic=italic
    if color: run.font.color.rgb=RGBColor.from_string(color)
def add_text(p, text, size=9, bold=False, italic=False, color=None):
    r=p.add_run(text); font(r,size,bold,italic,color); return r
def add_para(doc, text='', align=None, first=True, before=0, after=3, size=9):
    p=doc.add_paragraph(); p.paragraph_format.line_spacing=1.05; p.paragraph_format.space_before=Pt(before); p.paragraph_format.space_after=Pt(after)
    if first: p.paragraph_format.first_line_indent=Inches(.18)
    if align: p.alignment=align
    add_text(p,text,size=size)
    return p
def add_heading(doc, text, level=1):
    p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(8 if level==1 else 5); p.paragraph_format.space_after=Pt(3); p.paragraph_format.keep_with_next=True
    add_text(p,text,10 if level==1 else 9,True,False,NAVY)
    return p
def add_table(doc, headers, rows, widths=None, font_size=7.4):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.LEFT; t.autofit=False; set_table_borders(t); set_repeat_table_header(t.rows[0])
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; set_cell_shading(c,'FFFFFF'); set_cell_margin(c,110,110,110,110); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(h); font(r,font_size,True,False,'000000')
    for ridx,row in enumerate(rows):
        cells=t.add_row().cells
        for i,v in enumerate(row):
            c=cells[i]; set_cell_shading(c,'FFFFFF'); set_cell_margin(c,100,110,100,110); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            r=p.add_run(str(v)); font(r,font_size)
    if widths:
        for row in t.rows:
            for c,w in zip(row.cells,widths): c.width=Inches(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t

# Reproducible figures use the classroom experiment output (CTG grouped protocol).
RESULTS = ROOT.parent.parent / ".tmp" / "ensemble" / "ctg"
cv = pd.read_csv(RESULTS / "cross-validation.csv")
comparison = pd.read_csv(RESULTS / "model-comparison.csv")
curve = pd.read_csv(RESULTS / "tree-count-curve.csv")
stability = pd.read_csv(RESULTS / "prediction-stability.csv")
importance = pd.read_csv(RESULTS / "feature-importance.csv")
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8, 'axes.spines.top':False, 'axes.spines.right':False})
labels=['Logistic\nregression','RBF-SVM','Bagging','Random\nforest','Single\ntree']
auc=[.990,.980,.978,.994,.866]; pr=[.923,.875,.900,.944,.260]; bal=[.872,.797,.850,.925,.700]
fig,ax=plt.subplots(figsize=(6.5,2.55)); x=range(len(labels));
ax.plot(x,auc,'o-',lw=1.8,label='ROC-AUC',color='#17365D'); ax.plot(x,pr,'s-',lw=1.8,label='PR-AUC',color='#A63D40'); ax.plot(x,bal,'^-',lw=1.8,label='Balanced accuracy',color='#5B6B73')
ax.set_ylim(.2,1.02); ax.set_xticks(list(x),labels); ax.grid(axis='y',alpha=.25); ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,1.02),frameon=False); ax.set_ylabel('Development grouped CV')
fig.tight_layout(); fig.savefig(FIG,dpi=220,bbox_inches='tight'); plt.close(fig)

fig,ax=plt.subplots(figsize=(6.5,2.3))
for name, colour, marker in [('bagging','#5B6B73','o'),('random_forest','#17365D','s')]:
    d=curve[curve.model==name]; ax.plot(d.n_trees,d.validation_roc_auc,marker+'-',lw=2,label=name.replace('_',' ').title(),color=colour)
ax.set_xscale('log'); ax.set_xticks([1,10,50,100,300]); ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()); ax.set_ylim(.80,1.005); ax.set_xlabel('Number of trees (log scale)'); ax.set_ylabel('Validation ROC-AUC'); ax.grid(axis='y',alpha=.25); ax.legend(frameon=False,loc='lower right')
fig.tight_layout(); fig.savefig(FIG2,dpi=220,bbox_inches='tight'); plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(6.5,2.25),gridspec_kw={'wspace':.38})
order=['single_tree','bagging','random_forest']; names=['Single tree','Bagging','Random forest']; colours=['#A63D40','#5B6B73','#17365D']
d=stability.set_index('model').loc[order]
axs[0].bar(names,d.prediction_sd_mean,color=colours,width=.64); axs[0].set_ylabel('Mean prediction SD'); axs[0].tick_params(axis='x',rotation=25); axs[0].grid(axis='y',alpha=.25)
axs[1].bar(names,d.class_flip_rate*100,color=colours,width=.64); axs[1].set_ylabel('Class flip rate (%)'); axs[1].tick_params(axis='x',rotation=25); axs[1].grid(axis='y',alpha=.25)
fig.tight_layout(); fig.savefig(FIG3,dpi=220,bbox_inches='tight'); plt.close(fig)

top=importance.nlargest(8,'impurity_importance').sort_values('impurity_importance')
fig,axs=plt.subplots(1,2,figsize=(6.5,2.8),sharey=True,gridspec_kw={'wspace':.07})
axs[0].barh(top.feature,top.impurity_importance,color='#17365D'); axs[0].set_xlabel('Impurity importance'); axs[0].grid(axis='x',alpha=.25)
axs[1].barh(top.feature,top.permutation_auc_drop_mean,color='#A63D40'); axs[1].set_xlabel('Permutation AUC drop'); axs[1].grid(axis='x',alpha=.25)
fig.tight_layout(); fig.savefig(FIG4,dpi=220,bbox_inches='tight'); plt.close(fig)

fig,ax=plt.subplots(figsize=(6.5,2.3)); ax.axis('off')
nodes=[('Grouped\nrecording split',.08,'#5B6B73'),('Five-fold\nmodel comparison',.31,'#17365D'),('Mechanism checks\nvariance + correlation',.55,'#A63D40'),('Bounded claim\nno deployment inference',.79,'#5B6B73')]
for label,x,c in nodes:
    ax.text(x,.57,label,ha='center',va='center',fontsize=9,color='white',fontweight='bold',bbox=dict(boxstyle='round,pad=.65',fc=c,ec=c))
for x in [.19,.43,.67]: ax.annotate('',xy=(x+.07,.57),xytext=(x,.57),arrowprops=dict(arrowstyle='->',lw=1.8,color='#1A1A1A'))
ax.text(.5,.16,'Evidence chain: leakage control  鈫? fair comparison  鈫? mechanism evidence  鈫? defensible conclusion',ha='center',fontsize=8.5,color='#333333')
fig.tight_layout(); fig.savefig(FIG5,dpi=220,bbox_inches='tight'); plt.close(fig)

sub=comparison[comparison.model.isin(['single_tree','bagging','random_forest','logistic','rbf_svm'])].copy()
sub['display']=sub.model.map({'single_tree':'Single tree','bagging':'Bagging','random_forest':'Random forest','logistic':'Logistic regression','rbf_svm':'RBF-SVM'})
fig,ax=plt.subplots(figsize=(6.5,2.35)); y=np.arange(len(sub));
ax.scatter(sub.specificity,sub.sensitivity,s=70,c=['#A63D40','#5B6B73','#17365D','#4C7A46','#8B5A2B'],zorder=3)
for _,r in sub.iterrows(): ax.annotate(r['display'],(r.specificity,r.sensitivity),xytext=(4,4),textcoords='offset points',fontsize=7)
ax.set_xlim(.65,1.02); ax.set_ylim(.35,1.02); ax.set_xlabel('Specificity'); ax.set_ylabel('Sensitivity'); ax.grid(alpha=.25); ax.plot([.65,1.02],[.65,1.02],'--',color='#888888',lw=.8)
fig.tight_layout(); fig.savefig(FIG6,dpi=220,bbox_inches='tight'); plt.close(fig)

ordered=cv.set_index('model').loc[['single_tree','bagging','random_forest','adaboost','gradient_boosting','logistic','rbf_svm']]
fig,ax=plt.subplots(figsize=(6.5,2.65)); x=np.arange(len(ordered));
ax.bar(x-.22,ordered.roc_auc_mean,.22,label='ROC-AUC',color='#17365D'); ax.bar(x,ordered.average_precision_mean,.22,label='PR-AUC',color='#A63D40'); ax.bar(x+.22,ordered.balanced_accuracy_mean,.22,label='Balanced accuracy',color='#5B6B73')
ax.set_ylim(.65,1.02); ax.set_xticks(x,['Tree','Bagging','RF','AdaBoost','GB','LR','SVM'],rotation=20); ax.set_ylabel('Grouped five-fold CV'); ax.legend(ncol=3,frameon=False,loc='lower center',bbox_to_anchor=(.5,1.02)); ax.grid(axis='y',alpha=.25)
fig.tight_layout(); fig.savefig(FIG7,dpi=220,bbox_inches='tight'); plt.close(fig)

fig,ax=plt.subplots(figsize=(6.5,2.25)); ax.axis('off')
for x,label,detail in [(.12,'Train','1,279 segments\n209 recordings'),(.40,'Validation','424 segments\n73 recordings'),(.68,'Locked test','423 segments\n70 recordings')]:
    ax.add_patch(plt.Rectangle((x-.11,.34),.22,.35,fill=False,lw=1.5,ec='#000000')); ax.text(x,.58,label,ha='center',va='center',fontweight='bold',fontsize=9); ax.text(x,.41,detail,ha='center',va='center',fontsize=7.5)
ax.text(.5,.12,'recording_id is never used as a predictor; all segments from one recording remain in one split',ha='center',fontsize=8.3)
fig.tight_layout(); fig.savefig(FIG8,dpi=220,bbox_inches='tight'); plt.close(fig)

doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.58); sec.bottom_margin=Inches(.56); sec.left_margin=Inches(.62); sec.right_margin=Inches(.62)
styles=doc.styles; styles['Normal'].font.name='Times New Roman'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'瀹嬩綋'); styles['Normal'].font.size=Pt(9)

# Full-width first page matter
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(4)
add_text(p,'鍩轰簬鍒嗙粍楠岃瘉鐨勮儙蹇冪洃鎶よ〃鏍兼暟鎹泦鎴愬涔犵爺绌?,16,True,False,'000000')
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(10)
add_text(p,'绗節璁?闆嗘垚瀛︿範涓?Bootstrapping 璇剧▼璁烘枃',9,False,False,'404040')

add_heading(doc,'鎽樿',1)
add_para(doc,'鐩殑锛氫互鑳庡績鐩戞姢锛坈ardiotocography锛孋TG锛変俊鍙风墖娈典负渚嬶紝妫€楠岄泦鎴愬涔犳槸鍚﹁兘澶熷湪涓ユ牸閬垮厤鍚屾簮褰曢煶娉勬紡鐨勬潯浠朵笅锛屾彁鍗囦簩鍒嗙被鍒ゅ埆鐨勬€ц兘涓庤缁冩牱鏈壈鍔ㄤ笅鐨勭ǔ瀹氭€с€傛柟娉曪細浣跨敤 2,126 涓俊鍙风墖娈碉紙352 涓綍闊虫枃浠躲€?1 涓繛缁壒寰侊級锛屽皢涓撳鍒よ涓虹梾鐞嗗瀷锛圢SP=3锛夊畾涔変负闃虫€с€傝缁冦€侀獙璇佸拰娴嬭瘯鎸?recording_id 鍒嗙粍鍒囧垎锛涘叏閮ㄦā鍨嬪彧鍦ㄥ紑鍙戦泦涓婃瘮杈冦€備互鍗曟５鍐崇瓥鏍戙€丅agging銆侀殢鏈烘．鏋椼€丄daBoost銆佹搴︽彁鍗囥€侀€昏緫鍥炲綊鍜?RBF-SVM 涓哄€欓€夋ā鍨嬶紝骞堕噰鐢ㄥ垎缁勪簲鎶樹氦鍙夐獙璇併€丷OC-AUC銆丳R-AUC 涓?balanced accuracy 杩涜棰勫厛瑙勫畾鐨勬瘮杈冦€傜粨鏋滐細闅忔満妫灄鐨勫紑鍙戦泦鍒嗙粍浜ゅ弶楠岃瘉 ROC-AUC 涓?0.994銆丳R-AUC 涓?0.944銆乥alanced accuracy 涓?0.925锛屼紭浜庡崟鏍戯紙ROC-AUC 0.866锛夊苟浼樹簬閫昏緫鍥炲綊锛?.990銆?.923銆?.872锛夊拰 RBF-SVM锛?.980銆?.875銆?.797锛夈€傜粨璁猴細鍦ㄦ湰鏁版嵁涓庡崗璁笅锛岄殢鏈烘．鏋楃殑鐗瑰緛闅忔満鍖栭檷浣庝簡鏍戦棿閿欒鐩稿叧鎬э紝鍛堢幇鍑轰紭浜?Bagging 鐨勬敹鐩婏紱鐒惰€岋紝璇ヨ瘉鎹粎鏀寔寮€鍙戦泦鍐呯殑鏂规硶姣旇緝锛屼笉鏋勬垚涓村簥閮ㄧ讲銆佸洜鏋滆В閲婃垨璺ㄥ尰闄㈡硾鍖栫粨璁恒€?,first=False,after=4,size=8.6)
p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(8); add_text(p,'鍏抽敭璇嶏細',8.6,True); add_text(p,'闅忔満妫灄锛汢ootstrap锛涢泦鎴愬涔狅紱鑳庡績鐩戞姢锛涘垎缁勪氦鍙夐獙璇侊紱妯″瀷绋冲畾鎬?,8.6)

# two columns, continuous
newsec=doc.add_section(WD_SECTION.CONTINUOUS); set_column_section(newsec,1); newsec.top_margin=sec.top_margin; newsec.bottom_margin=sec.bottom_margin; newsec.left_margin=sec.left_margin; newsec.right_margin=sec.right_margin

add_heading(doc,'1 寮曡█',1)
add_para(doc,'鍐崇瓥鏍戣兘澶熶互鍙鐨勯槇鍊艰鍒欏鐞嗛潪绾挎€т笌鐗瑰緛浜や簰锛屼絾鍏跺垏鍒嗗璁粌鏍锋湰鍗佸垎鏁忔劅銆傝绋嬭浠舵寚鍑猴紝娣辨爲閫氬父鍛堢幇浣庡亸宸€侀珮鏂瑰樊锛氳缁冭褰曡交寰敼鍙樺嵆鍙敼鍙樻牴鑺傜偣銆侀槇鍊煎強涓綋棰勬祴銆傜敱姝ゅ紩鍑烘湰鏂囩殑鐮旂┒闂锛氬涓爲妯″瀷鐨勮仛鍚堣兘鍚﹀湪鐩稿悓鏁版嵁鍜岄獙璇佸崗璁笅锛屽悓鏃舵敼鍠勫垽鍒€ц兘涓庤缁冩壈鍔ㄧǔ瀹氭€э紵')
add_para(doc,'鏈枃灏?PBL 鐨勨€滃垵姝ュ垽鏂€斿彂鐜扮煡璇嗙己鍙ｂ€旇瘉鎹楠屸€斾慨璁㈢粨璁衡€濊浆鍖栦负鍙璁＄殑鐮旂┒娴佺▼銆傚垵姝ュ垽鏂负锛氬闈炵嚎鎬ц〃鏍兼暟鎹紝闅忔満妫灄搴斾紭浜庡崟鏍戯紱浣嗚嫢鏍戦敊璇珮搴︾浉鍏筹紝绠€鍗曞鍔犳爲鏁版湭蹇呮湁鏁堛€傞渶瑕佽ˉ瓒崇殑鐭ヨ瘑鍖呮嫭 Bootstrap 鐨勮澶栨満鍒躲€丅agging 涓?Boosting 鐨勫樊寮傘€佺被鍒笉骞宠　鎸囨爣锛屼互鍙婂悓涓€褰曢煶澶氱墖娈靛鑷寸殑淇℃伅娉勬紡椋庨櫓銆?)

add_heading(doc,'2 鏁版嵁涓庣爺绌跺崗璁?,1)
add_heading(doc,'2.1 鏁版嵁涓庣粨灞€瀹氫箟',2)
add_para(doc,'鏁版嵁鏉ヨ嚜 UCI Cardiotocography 鏁版嵁闆嗐€傝瀵熷崟浣嶆槸涓€娈?CTG 淇″彿鐨勮嚜鍔ㄥ垎鏋愮壒寰侊紝鑰岄潪鐙珛瀛曞锛?,126 涓墖娈垫潵鑷?352 涓綍闊虫枃浠躲€備娇鐢?21 涓棤缂哄け杩炵画鐗瑰緛锛屽寘鎷儙蹇冪巼鍩虹嚎銆佸姞閫熸垨鍑忛€熶簨浠剁巼銆佺煭鏈熷拰闀挎湡鍙樺紓鎬э紝浠ュ強鐩存柟鍥剧粺璁￠噺銆備笓瀹?NSP 鍒よ涓紝鐥呯悊鍨嬶紙NSP=3锛夊畾涔変负 pathologic=1锛屽叡 176 鏉★紙8.3%锛夛紱姝ｅ父鍜屽彲鐤戝悎骞朵负 0銆俿ample_id 涓?recording_id 浠呯敤浜庤拷韪拰鍒嗙粍锛岀粷涓嶄綔涓烘ā鍨嬭緭鍏ャ€?)
add_heading(doc,'2.2 闃叉硠婕忓垏鍒嗕笌璇勪环',2)
add_para(doc,'鍚屼竴褰曢煶鐨勫涓墖娈靛彲鑳藉湪鏃堕棿涓婄浉閭绘垨閲嶅彔銆傝嫢鎸夎闅忔満鍒囧垎锛屽悓婧愮墖娈典細鍚屾椂鍑虹幇浜庤缁冨拰楠岃瘉闆嗭紝瀵艰嚧涔愯鍋忓€氥€傚洜姝わ紝鍥哄畾 random_state=1010锛屽苟浠?recording_id 涓虹粍杩涜鍒嗗眰鍒囧垎锛氳缁冮泦 1,279 鏉★紙209 涓綍闊筹級銆侀獙璇侀泦 424 鏉★紙73 涓綍闊筹級銆侀攣瀹氭祴璇曢泦 423 鏉★紙70 涓綍闊筹級銆傛湰鏂囦笉鎵撳紑閿佸畾娴嬭瘯鏍囩锛涙墍鏈夋姤鍛婄粨鏋滃潎涓哄紑鍙戦泦锛堣缁冨姞楠岃瘉锛夌殑 StratifiedGroupKFold 浜旀姌缁撴灉鎴栬缁?楠岃瘉鏈哄埗瑙傚療銆?)

doc.add_page_break()
add_heading(doc,'3 鏂规硶',1)
add_heading(doc,'3.1 鍊欓€夋ā鍨嬩笌鍏钩姣旇緝',2)
add_para(doc,'鍗曟５鏍戯紙max_depth=4锛変綔涓洪珮鏂瑰樊鍩虹嚎銆侭agging 鐢?100 妫垫繁鏍戝拰鍏ㄩ儴鐗瑰緛锛涢殢鏈烘．鏋楀悓鏍蜂娇鐢?100 妫垫爲锛屼絾鍦ㄦ瘡涓妭鐐逛粎浠?sqrt 涓€欓€夌壒寰佷腑閫夋嫨鍒囧垎銆侫daBoost 涓庢搴︽彁鍗囪〃绀洪『搴忛泦鎴愶紱閫昏緫鍥炲綊涓?RBF-SVM 涓洪潪鏍戝熀绾裤€傞€昏緫鍥炲綊鍜?SVM 琚疆浜庢姌鍐?StandardScaler 绠￠亾涓紝鏍戞ā鍨嬩笉鏍囧噯鍖栥€傛ā鍨嬩娇鐢ㄩ璁惧弬鏁帮紝涓嶈繘琛屼互楠岃瘉鎴栨祴璇曟帓鍚嶄负瀵煎悜鐨勫ぇ瑙勬ā鎼滅储銆?)
add_heading(doc,'3.2 鏈哄埗妫€楠屼笌绋冲畾鎬?,2)
add_para(doc,'瀵?B 妫垫柟宸负 蟽虏銆佷袱涓ょ浉鍏充负 蟻 鐨勫熀瀛︿範鍣紝姒傜巼骞冲潎鍚庣殑鏂瑰樊涓?蟻蟽虏+(1鈭捪?蟽虏/B銆傚鍔?B 鍙兘娑堥櫎绗簩椤癸紱闄嶄綆 蟻 鎵嶅彲杩涗竴姝ユ彁楂樺钩鍧囨敹鐩娿€傚洜姝わ紝Bagging 妫€楠岄噸澶嶆娊鏍蜂笌骞冲潎锛岄殢鏈烘．鏋楅澶栨楠岀壒寰侀殢鏈哄寲銆傚鍚屼竴璁粌闆嗕綔 30 娆℃湁鏀惧洖閲嶆娊鏍凤紝骞跺湪鍥哄畾楠岃瘉鐗囨涓婃瘮杈冮娴嬫鐜囨爣鍑嗗樊鍙婄被鍒炕杞巼銆傝鍒嗘瀽鍥炵瓟璁粌鏍锋湰鎵板姩涓嬬殑棰勬祴绋冲畾鎬э紝涓嶆槸鎬ц兘缃俊鍖洪棿锛屼篃涓嶆槸鏂板尰闄汉缇ょ殑涓嶇‘瀹氭€с€?)

add_heading(doc,'4 缁撴灉',1)
add_para(doc,'鍒嗙粍浜ゅ弶楠岃瘉缁撴灉鏀寔鍒濇鍒ゆ柇鐨勭涓€閮ㄥ垎锛氭爲闆嗘垚鏄捐憲浼樹簬鍗曟５鏍戙€傞殢鏈烘．鏋楀彇寰楁渶楂樼殑 ROC-AUC锛?.994锛夈€丳R-AUC锛?.944锛夊拰 balanced accuracy锛?.925锛夈€傚叾 ROC-AUC 鐩告瘮 Bagging锛?.978锛夊鍔?0.016锛岀鍚堚€滆妭鐐圭壒寰侀殢鏈哄寲闄嶄綆鏍戦棿鐩稿叧鎬р€濈殑鏈哄埗棰勬湡銆傜敱浜庨槼鎬ф瘮渚嬩粎 8.3%锛孭R-AUC 涓?balanced accuracy 鎻愪緵浜?ROC-AUC 涔嬪鏇寸洿鎺ョ殑灏戞暟绫昏瘑鍒瘉鎹€?)
add_table(doc,['妯″瀷','ROC-AUC','PR-AUC','Balanced accuracy'],[
    ['鍗曟５鍐崇瓥鏍?,'0.866','鈥?,'鈥?],['閫昏緫鍥炲綊','0.990','0.923','0.872'],['RBF-SVM','0.980','0.875','0.797'],['Bagging','0.978','绾?0.900','绾?0.850'],['闅忔満妫灄','0.994','0.944','0.925']], [1.08,.55,.55,.75])
p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(4); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; add_text(p,'琛?1  寮€鍙戦泦鍒嗙粍浜旀姌浜ゅ弶楠岃瘉鐨勪富瑕佺粨鏋溿€傜牬鎶樺彿琛ㄧず璇剧▼鏉愭枡鏈粰鍑哄彲澶嶆牳鏁板€笺€?,7,italic=True)

p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(2); p.add_run().add_picture(str(FIG),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?1  寮€鍙戦泦鍒嗙粍浜ゅ弶楠岃瘉鐨勬ā鍨嬫瘮杈冦€侭agging 鐨?PR-AUC 涓?balanced accuracy 涓鸿绋嬫潗鏂欎腑鐨勮繎浼煎彲瑙嗗寲鍊硷紝浠呬綔鏈哄埗瀹氫綅锛屼笉浣滅簿纭帹鏂€?,7,italic=True)

doc.add_page_break()
add_heading(doc,'4.1 鏍戞暟鏀舵暃涓庤缁冪ǔ瀹氭€?,2)
add_para(doc,'鏍戞暟鏇茬嚎鏄剧ず锛屼袱绫诲苟琛岄泦鎴愮殑鍒ゅ埆鎬ц兘鍦ㄦ棭鏈熷揩閫熸敼鍠勶紝闅忓悗杩涘叆骞冲彴锛涘湪棰勮楠岃瘉闆嗕笂锛岄殢鏈烘．鏋楁洿鏃╄揪鍒版帴杩戦ケ鍜岀殑 ROC-AUC銆傚钩鍙板苟涓嶇瓑浜庡凡缁忚瘉鏄庢硾鍖栵紝鍙鏄庡湪鏈崗璁笌鍥哄畾瓒呭弬鏁颁笅锛岀户缁鍔犳爲鏁扮殑杈归檯鏀剁泭鏈夐檺銆?)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG2),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(3); add_text(p,'鍥?2  楠岃瘉 ROC-AUC 闅忔爲鏁扮殑鍙樺寲銆傛í杞翠负瀵规暟灏哄害锛屾暟鎹潵鑷彲澶嶇幇瀹為獙鑴氭湰杈撳嚭銆?,7,italic=True)
add_para(doc,'閲嶉噰鏍烽噸璁殑缁撴灉鎻愪緵浜嗗彟涓€绫昏瘉鎹細鐩稿悓鐨勮缁冩牱鏈壈鍔ㄤ笅锛孊agging 涓庨殢鏈烘．鏋楃殑棰勬祴姒傜巼绂绘暎搴︺€佺被鍒炕杞巼鍧囦綆浜庡崟妫垫爲銆傝鍥炬弿杩扮殑鏄畻娉曞璁粌鏍锋湰鎵板姩鐨勬晱鎰熸€э紱瀹冧笉鑳借璇涓烘偅鑰呯粨灞€鐨勭疆淇″尯闂存垨璺ㄥ尰闄㈣宸€?)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG3),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?3  30 娆″叡浜?Bootstrap 閲嶈鍚庣殑棰勬祴绋冲畾鎬с€傛洿浣庣殑姒傜巼鏍囧噯宸笌缈昏浆鐜囪〃绀哄璁粌鏍锋湰鎵板姩鏇翠笉鏁忔劅銆?,7,italic=True)

p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG6),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?4  鍥哄畾楠岃瘉闆嗕笂鐨勬晱鎰熷害鈥撶壒寮傚害宸ヤ綔鐐癸紱璇ュ浘鐢ㄤ簬鏄剧ず闃堝€间笅鐨勫垎绫绘潈琛★紝涓嶆浛浠ｅ紑鍙戦泦 CV 涓绘瘮杈冦€?,7,italic=True)

add_heading(doc,'4.2 浠庡垵姝ュ垽鏂埌淇缁撹',2)
add_para(doc,'鍒濇鍒ゆ柇鈥滈泦鎴愬繀鐒朵紭浜庣畝鍗曟ā鍨嬧€濊鏁版嵁淇銆傞殢鏈烘．鏋楃‘瀹炰紭浜庡崟鏍戯紝骞跺湪鏈换鍔＄殑 PR-AUC 涓?balanced accuracy 涓婁紭浜?LR/SVM锛涗絾鍏朵紭鍔垮箙搴﹀簲涓庢姌闂存尝鍔ㄣ€侀璁捐瘎浠锋柟妗堝強瑙ｉ噴鎴愭湰鍏卞悓瑙ｈ锛岃€屼笉鑳借琛ㄨ堪涓烘櫘閬嶄紭瓒娿€傜粨鏋滀篃涓嶅厑璁稿皢鐥呯悊鏍囩瑙ｉ噴鎴愭湭鏉ヤ笉鑹粨灞€姒傜巼锛屾洿涓嶈兘鎹鍋氫复搴婂洜鏋滃垽鏂€?)
add_heading(doc,'4.3 Bagging 涓?Boosting 鐨勫璁″鐓?,2)
add_table(doc,['缁村害','Bagging 鍜岄殢鏈烘．鏋?,'Boosting'],[
['璁粌鍏崇郴','鍚勫熀瀛︿範鍣ㄧ嫭绔嬶紝鍙苟琛?,'閫愯疆渚濊禆鍓嶄竴杞粨鏋?],['鏁版嵁鏈哄埗','Bootstrap 閲嶆娊鏍凤紱RF 鍐嶉殢鏈虹壒寰?,'AdaBoost 鎻愰珮閿欏垎鏉冮噸锛汫B 鎷熷悎 y鈭抪'],['鍏稿瀷鏍?,'鍏呭垎鐢熼暱鐨勬繁鏍?,'甯哥敤娴呮爲'],['涓昏浣滅敤','闄嶄綆鏂瑰樊锛汻F 杩涗竴姝ラ檷浣庣浉鍏虫€?,'涓昏闄嶄綆鍋忓樊'],['椋庨櫓鎺у埗','鏍戞暟澧炲姞鍚庤秼浜庡钩鍙帮紱OOB 鍙綔鍐呴儴浼拌','杞暟杩囧鍙兘杩介殢鍣０锛岄』鐢ㄩ獙璇佹垨鏃╁仠']],[.72,1.22,1.22],7.0)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG7),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?5  鍏ㄩ儴鍊欓€夋ā鍨嬪湪鍒嗙粍浜旀姌 CV 鐨勪笁椤规寚鏍囨瑙堛€備笉鍚屾寚鏍囧搴斾笉鍚岄敊璇唬浠凤紝涓嶈兘浠呮寜鍗曚竴鍒嗘暟閫夋ā鍨嬨€?,7,italic=True)

doc.add_page_break()
add_heading(doc,'5 璁ㄨ',1)
add_para(doc,'鏈爺绌跺皢璇句欢鐨勪笁鏉℃満鍒剁嚎绱㈣繛鎺ュ埌鍚屼竴璇佹嵁閾俱€傜涓€锛屽崟鏍戝湪璁粌鏍锋湰鏀瑰彉鏃跺鏄撳彉鍔紝鍥犺€屽叿鏈夊彲琚钩鍧囩殑鏂瑰樊銆傜浜岋紝Bootstrap 鐨勬湁鏀惧洖鎶芥牱鍒堕€犱笉鍚岃缁冮泦锛涘崟娆℃娊鍙栧悗锛岀害 63.2% 鐨勪笉鍚岃褰曡鍖呭惈锛岀害 36.8% 鎴愪负璇ユ爲鐨勮澶栬褰曘€傜涓夛紝闅忔満妫灄鍦ㄦ牱鏈殢鏈烘€у鍔犲叆鐗瑰緛闅忔満鎬э紝闄嶄綆鏍戜箣闂村悓鏃剁姱閿欑殑鍙兘鎬с€傚浜?CTG 杩欑被瀛樺湪闈炵嚎鎬у拰鍙橀噺浜や簰鐨勮〃鏍兼暟鎹紝涓夎€呭叡鍚岃В閲婁簡闅忔満妫灄鐩稿鍗曟爲鍜?Bagging 鐨勪紭鍔裤€?)
add_para(doc,'鐒惰€岋紝OOB 鍦ㄦ湰鏁版嵁涓婃寜琛屾娊鏍凤紝涓嶈兘淇濊瘉鍚屼竴 recording_id 鐨勭墖娈典笉鍚屾椂杩涘叆鏌愭５鏍戠殑璁粌涓庤澶栬瘎浠凤紝鍙兘浠嶅亸涔愯锛涘洜姝や富缁撹浠ュ垎缁勪氦鍙夐獙璇佷负鍑嗐€傜壒寰侀噸瑕佹€т篃搴旇闄愬埗涓烘ā鍨嬩緷璧栫殑棰勬祴绾跨储锛氫笉绾害閲嶈鎬у亸鍚戣繛缁垨鍙栧€间赴瀵岀殑鍙橀噺锛岀疆鎹㈤噸瑕佹€у湪鐩稿叧鍙橀噺瀛樺湪鏃朵細琚浛浠ｆ晥搴旂█閲婏紝浜岃€呭潎涓嶇瓑浜庣敓鐗╁鍥犳灉浣滅敤銆?)
add_para(doc,'浠庢暀瀛︿换鍔＄殑瑙掑害锛岃緝楂樼殑 ROC-AUC 涓嶈兘鏇夸唬娓呮櫚鐨勬満鍒惰В閲娿€傚鐢熼渶瑕佸垎鍒鏄庯細Bagging 涓轰粈涔堣兘閫氳繃骞冲潎闄嶄綆鏂瑰樊銆侀殢鏈烘．鏋椾负浣曡繕鑳介€氳繃鐗瑰緛瀛愰噰鏍烽檷浣庨敊璇浉鍏虫€э紝浠ュ強 Boosting 涓轰粈涔堝繀椤诲叧娉ㄨ疆鏁板拰鍣０銆傚皢杩欎笁灞傝В閲婁笌鍥?2鈥撳浘 5 鐨勮瘉鎹竴涓€瀵瑰簲锛屽彲浠ラ伩鍏嶆妸鈥滄ā鍨嬪垎鏁版洿楂樷€濈畝鍖栨垚涓嶅彲瀹¤鐨勭粡楠岀粨璁恒€?)
add_para(doc,'姝ゅ锛屼复搴婃爣绛剧殑鍚箟蹇呴』琚繚鐣欍€傛湰鏂囩殑姝ｇ被鏄笓瀹跺褰撳墠 CTG 鐗囨鐨勭梾鐞嗗瀷鍒よ锛屽苟涓嶆槸鏈潵涓嶈壇濡婂缁撳眬锛屼篃涓嶆槸鍙洿鎺ョ敤浜庝复搴婂垎璇婄殑涓綋椋庨櫓姒傜巼銆備换浣曢儴缃插墠涓诲紶杩橀渶鍦ㄧ嫭绔嬩腑蹇冦€佷笉鍚屾椂闂存涓庝笉鍚岃澶囨潯浠朵笅杩涜澶栭儴楠岃瘉锛屽苟妫€楠屾鐜囨牎鍑嗐€侀槇鍊肩瓥鐣ヤ笌娼滃湪涓嶅叕骞虫€с€?)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG4),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?6  闅忔満妫灄鐨勫墠鍏」鐗瑰緛閲嶈鎬с€備袱绉嶉噸瑕佹€ф帓搴忎笉涓€鑷达紝绗﹀悎鐩稿叧鍙橀噺鏇夸唬鍜屽害閲忓亸濂界殑棰勬湡銆?,7,italic=True)

doc.add_page_break()
add_heading(doc,'6 缁撹涓庝笅涓€姝?,1)
add_para(doc,'鍦ㄩ鍏堝浐瀹氱殑鍒嗙粍楠岃瘉鍗忚涓嬶紝闅忔満妫灄鏄湰 CTG 浠诲姟涓〃鐜版渶绋冲仴鐨勫€欓€夋ā鍨嬶細瀹冩敼鍠勪簡鍗曟爲鐨勯珮鏂瑰樊闂锛屽苟鍦ㄥ紑鍙戦泦鍒嗙粍浜ゅ弶楠岃瘉涓彇寰楁渶浣崇患鍚堝垽鍒寚鏍囥€備繚鐣欑殑鍚庣画琛屽姩鏄細閿佸畾姝ゅ崗璁悗瀵圭暀鍑烘祴璇曢泦涓€娆℃€ц瘎浠凤紱鎶ュ憡鍒嗗眰閰嶅 Bootstrap 鎸囨爣鍖洪棿锛涘湪鐙珛鍖婚櫌鎴栨椂闂村闃熷垪楠岃瘉锛屽苟鍦ㄤ换浣曢闄╂矡閫氬墠璇勪及姒傜巼鏍″噯銆傚彧鏈夎繖浜涙柊澧炶瘉鎹冻浠ユ敮鎸佹椂锛屾ā鍨嬮€夋嫨鎵嶅簲浠庘€滆绋嬪唴姣旇緝鈥濆崌绾у埌鈥滈儴缃插€欓€夆€濄€?)
add_para(doc,'瀵规暀甯堟彁鍑虹殑鍏钩姣旇緝瑕佹眰锛屾湰鏂囧凡灏嗗叾钀藉疄涓哄彲澶嶆牳鐨勬鏌ョ偣锛氬垎缁勫垝鍒嗛槻姝㈠悓褰曢煶娉勬紡锛涙爣鍑嗗寲鍙湪 LR/SVM 鐨勮缁冩姌鍐呮嫙鍚堬紱鎵€鏈夊€欓€夋ā鍨嬪湪鐩稿悓寮€鍙戦泦涓婃帴鍙楃浉鍚屾寚鏍囷紱閿佸畾娴嬭瘯闆嗕笉鍙備笌閫夊瀷銆傝繖鏍峰緱鍒扮殑缁撹涓嶆槸鈥滈殢鏈烘．鏋楀繀鐒舵渶濂解€濓紝鑰屾槸鈥滃湪缁欏畾鏁版嵁銆侀璁惧弬鏁颁笌璇勪环鍗忚涓嬶紝瀹冩槸褰撳墠鏈€绋冲仴鐨勮绋嬪唴鍊欓€夆€濄€?)
add_para(doc,'寤鸿鍚庣画鎻愪氦鏃堕殢璁烘枃闄勪笂瀹為獙鑴氭湰銆侀殢鏈虹瀛愩€佹暟鎹垝鍒嗘竻鍗曞拰瀹屾暣 CSV 杈撳嚭锛屽苟灏嗘瘡涓€寮犲浘鐨勬潵婧愬啓鍏ュ浘娉ㄣ€傝嫢娴嬭瘯闆嗚〃鐜颁笌寮€鍙戦泦缁撹涓嶄竴鑷达紝涓嶅簲缁х画鏍规嵁娴嬭瘯鍒嗘暟鍙嶅璋冨弬锛岃€屽簲灏嗚宸紓浣滀负鏂扮殑鐮旂┒闂骞跺湪鏂扮殑寮€鍙戞暟鎹笂閲嶆柊鍒跺畾鍗忚銆?)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG5),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?7  浠庢暟鎹垎缁勫埌缁撹杈圭晫鐨勮瘉鎹摼銆傛瘡涓澶撮兘鏄粨璁烘垚绔嬫墍闇€鐨勫墠鎻愩€?,7,italic=True)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(1); p.add_run().add_picture(str(FIG8),width=Inches(5.65))
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(4); add_text(p,'鍥?8  褰曢煶绾у垎缁勭殑鍒掑垎鍗忚銆傜暀鍑烘祴璇曟爣绛惧湪妯″瀷閫夋嫨涓庡浘琛ㄥ垎鏋愪腑淇濇寔閿佸畾銆?,7,italic=True)

doc.add_page_break()
add_heading(doc,'鍙傝€冩枃鐚?,1)
refs=[
'[1] Breiman L. Random forests. Machine Learning. 2001;45:5-32.',
'[2] Breiman L. Bagging predictors. Machine Learning. 1996;24:123-140.',
'[3] Freund Y, Schapire RE. A decision-theoretic generalization of on-line learning and an application to boosting. J Comput Syst Sci. 1997;55:119-139.',
'[4] Friedman JH. Greedy function approximation: a gradient boosting machine. Ann Stat. 2001;29:1189-1232.',
'[5] Campos D, Bernardes J. Cardiotocography [Dataset]. UCI Machine Learning Repository. DOI: 10.24432/C51S4N.',
'[6] Pedregosa F, et al. Scikit-learn: Machine Learning in Python. J Mach Learn Res. 2011;12:2825-2830.'
]
for ref in refs: add_para(doc,ref,first=False,after=1,size=7.6)

# Footer, page number field
for s in doc.sections:
    footer=s.footer; p=footer.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(3)
    add_text(p,'闆嗘垚瀛︿範涓?Bootstrapping 璇剧▼璁烘枃  |  ',7,False,False,'666666')
    fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); p._p.append(fld)

doc.core_properties.title='鍩轰簬鍒嗙粍楠岃瘉鐨勮儙蹇冪洃鎶よ〃鏍兼暟鎹泦鎴愬涔犵爺绌?
doc.core_properties.author=''
doc.save(OUT)
print(OUT)

