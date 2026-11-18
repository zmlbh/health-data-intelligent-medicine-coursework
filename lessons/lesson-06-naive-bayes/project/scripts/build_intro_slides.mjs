import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

// Formal teaching source. All previews, candidates and validation stay in .tmp.
const repo=path.resolve(import.meta.dirname,'../../../..');
const base=path.resolve(import.meta.dirname,'..');
const runtime=process.env.CODEX_ARTIFACT_RUNTIME||'C:/Users/rongs/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const skill='C:/Users/rongs/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const build=repo+'/.tmp/naive-bayes/intro-slides';
await fs.mkdir(build,{recursive:true});
await fs.mkdir(base+'/slides',{recursive:true});
const font='Microsoft YaHei';
const ink='#193638',teal='#087C77',muted='#52686A',paper='#FAFBF8';
const slides=[
 {title:'机器学习基础\n与朴素贝叶斯',cover:true,lead:'六项症状怎样成为一个预测模型？',body:'第 7 讲  实验导入\n概念、数据、问题与设计理由'},
 {title:'本次实验的七个问题',lead:'用同一个症状预测任务，连接七项核心知识',list:[
  '什么是数据模型？模型从数据里学到了什么？',
  '训练、预测和泛化分别发生在什么时候？',
  '为什么训练集、验证集和测试集承担不同职责？',
  '损失函数衡量什么？',
  '如何评价一个分类模型？',
  '朴素贝叶斯如何用 Bayes theorem 进行预测？',
  '为什么医学诊断模型不能只看 accuracy？']},
 {title:'样本、特征、标签与数据模型',lead:'先明确观察对象、输入和预测目标',rows:[
  ['样本 sample','表中的一条记录。本课记录不能自动等同于独立患者。'],
  ['特征 feature','供模型使用的输入变量，本课为六项二元症状。'],
  ['标签 label','已知记录的目标值，本课为膀胱炎症状态 0 / 1。'],
  ['数据模型 model','用输入与输出之间的关系作预测，参数可由已有数据估计。']]},
 {title:'参数、概率与类别',lead:'模型输出概率，阈值把概率变成类别',rows:[
  ['参数 parameter','由训练数据估计的量，如类别比例和类内症状概率。'],
  ['概率 probability','p 表示模型给出的阳性概率，表达预测的程度。'],
  ['阈值 threshold','预先选定的判定界值 t，p ≥ t 时预测阳性。'],
  ['类别 class','最终的 0 / 1 判定。改变阈值可以改变类别，而不改变 p。']],note:'模型概率需要评价其可靠性，不能直接当作已经验证的真实临床风险。'},
 {title:'训练、预测与泛化',lead:'学习关系、应用关系、检验关系能否适用于未见数据',rows:[
  ['训练 training','用已知输入和标签估计参数，重新训练可能改变参数。'],
  ['预测 prediction','固定参数，对新输入计算概率或类别，无需提前知道其标签。'],
  ['泛化 generalization','模型在未参与拟合和选择的数据上仍能有效预测。'],
  ['过拟合 overfitting','模型过度适应训练数据的特有模式，在未见数据上表现下降。']]},
 {title:'三类数据与信息泄漏',lead:'估计参数、选择方案和最终评价是不同的工作',rows:[
  ['训练集 train','估计模型参数。'],
  ['验证集 validation','比较候选方案，本课主要用于选择分类阈值。'],
  ['测试集 test','所有选择固定后，对保留记录作最终评价。'],
  ['信息泄漏 leakage','用评价数据或预测时不可获得的信息建模，使评价过于乐观。']]},
 {title:'Bayes theorem 与朴素贝叶斯',lead:'用类别内的症状信息，更新类别概率',rows:[
  ['先验 prior','看这条记录的症状之前，对类别的概率判断。'],
  ['似然 likelihood','假定类别已知，观察到这组症状的概率。'],
  ['后验 posterior','结合先验和症状信息，得到更新后的类别概率。'],
  ['朴素贝叶斯 NB','给定类别后假定输入条件独立，以症状概率的乘积计算似然。']],note:'Bayes theorem: P(Y|x)=P(x|Y)P(Y)/P(x)。条件独立指给定类别后的独立，不是总体上症状互不相关。'},
 {title:'Bernoulli、平滑与损失函数',lead:'二元输入适合计数估参，概率预测仍需要评价',rows:[
  ['Bernoulli','取值为 0 或 1 的变量。本课有症状与无症状都提供信息。'],
  ['平滑 smoothing','给计数加入小量，避免未观察到的情况得到零概率。'],
  ['损失函数 loss','把预测误差变成数值，平均损失概括一组预测的误差。'],
  ['对数损失 log loss','评价概率预测，越小越好，对非常自信的错误惩罚较大。']],note:'本课 BernoulliNB(alpha=1, binarize=None) 按计数估参。fit 不表示通过梯度下降最小化验证集 log loss。具体公式和计算留给工作单任务5。'},
 {title:'混淆矩阵与分类评价',lead:'先区分四种结果，再解释指标的分母',table:[
  ['真实类别 / 预测类别','预测阴性','预测阳性'],
  ['真实阴性','TN：正确排除','FP：误报'],
  ['真实阳性','FN：漏诊','TP：正确检出']],after:'混淆矩阵（confusion matrix）汇总分类结果。\n同样的正确率，可能对应不同数量的漏诊和误报。'},
 {title:'评价指标分别回答什么',lead:'类别判定和概率质量需要分别描述',rows:[
  ['Accuracy 正确率','全部记录中，预测类别正确的比例。'],
  ['Sensitivity / recall','真实阳性中检出的比例，即敏感度 / 召回率。'],
  ['Specificity 特异度','真实阴性中正确排除的比例。'],
  ['Precision 精确率','预测阳性中真正阳性的比例。'],
  ['F1 与概率可靠性','F1 综合精确率与召回率。可靠性比较预测概率与观察频率。']],note:'F1 为 precision 和 recall 的调和平均。分母为零时指标可能未定义。准确分类不等同于概率校准良好，log loss 也不是只衡量校准。'},
 {title:'本次实验的数据',lead:'UCI Acute Inflammations：120 条专家构造记录',rows:[
  ['来源与用途','Jacek Czerniak 创建，供专家系统测试。许可：CC BY 4.0。'],
  ['原始内容','摄氏体温、五项 yes / no 症状，以及两个疾病标签。'],
  ['主预测目标','bladder_inflammation：膀胱炎症状态，1 为阳性，0 为阴性。'],
  ['适用范围','适合学习模型流程与手算，内部表现不能直接说明临床效果。']],bottom:'数据 DOI：10.24432/C5V59S',source:'data/README.md；https://doi.org/10.24432/C5V59S'},
 {title:'六项输入如何得到',lead:'把体温转成发热指示，得到统一的 0 / 1 输入',table:[
  ['输入','输入','共同编码'],
  ['发热：体温 ≥ 38°C','恶心','1 出现，0 未出现'],
  ['腰痛','尿急','1 出现，0 未出现'],
  ['排尿痛','尿道灼痛','1 出现，0 未出现']],after:'ID 用于关联记录，体温原值用于审计。\nID、体温原值和两个疾病标签均不进入六输入模型。',source:'data/README.md'},
 {title:'两类数据各自服务什么学习',lead:'手算例子帮助看清机制，UCI 记录连接完整流程',rows:[
  ['教学小例子','工作单中的少量记录与预测，专为手算设计，不与 UCI 数据合并。'],
  ['UCI 实验数据','用于训练六输入模型、与基线比较、选阈值和完成保留评价。'],
  ['需要观察的结构','检查类别比例、ID 及重复症状组合。ID 不同也可能具有相同输入。'],
  ['泛化问题','新的一行、未见症状组合、另一家医院的数据，提出不同的评价要求。']],note:'不要提前给出症状组合数或跨集合重叠数，让学生在 Notebook A 中观察。'},
 {title:'实验路线与设计理由',lead:'每一步引入一个知识需要，学生用计算和观察回答',table:[
  ['阶段','工作单','为什么安排这一阶段'],
  ['定义与学习','任务 1–2','分清输入、参数和预测'],
  ['分工与推断','任务 3–4','明确数据职责及 Bayes 更新'],
  ['误差与比较','任务 5–6','区分概率误差与类别错误'],
  ['保留评价','任务 7','结合错误类型说明结论范围']],note:'按工作单开展活动，不在导入中演示逐项计算或展示实验答案。'},
 {title:'设计一：先提出办法，再从计数学习',lead:'问题：一张症状表怎样变成可重复使用的预测规则？',rows:[
  ['学生先尝试','提出一种预测办法，明确它需要从已有记录中统计什么。'],
  ['简化任务','先用单症状教学数据，观察加一条记录并重训会改变什么。'],
  ['设计理由','减少同时处理的信息，让训练和预测的差异可以直接观察。'],
  ['需要回答','模型学到哪些参数？固定模型预测时，哪些量保持不变？']],bottom:'对应工作单 1–2'},
 {title:'设计二：三份数据的分工',lead:'问题：怎样既能选择方案，又能保留一次未参与选择的评价？',table:[
  ['数据部分','记录数','本次用途'],
  ['Train','72','估计类别比例与类内症状概率'],
  ['Validation','24','比较表现，选择阈值'],
  ['Test','24','固定方案后评价']],after:'按主标签分层，让三份数据保留近似的类别比例。\n测试结果一旦参与修改方案，就不再承担原来的独立评价职责。',note:'固定原有两步分层 random_state=7。主模型只在原72条训练记录上拟合，不合并验证集重训。',bottom:'对应工作单 3、7.3'},
 {title:'设计三：用 Bayes 连接症状与疾病',lead:'问题：知道“疾病内的症状概率”，怎样预测“症状下的疾病概率”？',rows:[
  ['学习顺序','从单症状 Bayes 开始，再扩展到六输入 Bernoulli NB。'],
  ['核对方式','学生先手算一个输入，再与程序输出核对，解释计算差异。'],
  ['假设实验','额外复制同一症状列，观察预测概率怎样变化。'],
  ['设计理由','让学生检查概率更新和独立假设怎样进入预测过程。']],bottom:'对应工作单 4；Notebook A2、C',note:'复制症状没有增加新测量信息。保留数据划分和主模型设置；副本模型仅用于理解假设，不预设性能一定下降。平滑系数 alpha=1。'},
 {title:'设计四：概率误差与基线对照',lead:'问题：类别都预测正确，是否意味着预测同样好？',rows:[
  ['概率对照','比较类别相同、概率不同的预测，用 log loss 描述差别。'],
  ['基线 baseline','Prior-only 对所有输入都输出训练集阳性比例，不使用症状。'],
  ['公平比较','两种模型使用同一训练来源和验证记录，比较类别与概率。'],
  ['设计理由','判断症状带来多少预测信息，避免只看一个模型的孤立分数。']],bottom:'对应工作单 5；Notebook B',note:'比较训练与验证损失，但不预设本数据一定出现明显过拟合或验证损失一定更高。'},
 {title:'设计五：固定概率，改变阈值',lead:'问题：更重视减少漏诊时，评价方式需要怎样改变？',rows:[
  ['学生先预想','降低阈值后，哪些记录可能改变类别？'],
  ['受控比较','模型和验证记录保持相同，只改变分类阈值，比较 FN 与 FP。'],
  ['选择依据','按工作单预设的敏感度要求和特异度规则，在验证集选择。'],
  ['设计理由','把医学关注点转成可解释的错误取舍，避免只追求 accuracy。']],bottom:'对应工作单 6；Notebook B',note:'教学规则：候选阈值中先满足 sensitivity≥0.90，再最大化 specificity，并列规则见工作单。若无可行值则报告失败。此为教学规则，不是临床标准。'},
 {title:'设计六：类别比例、概率质量与保留评价',lead:'问题：一个分数能覆盖哪些表现，又遗漏哪些信息？',rows:[
  ['改变类别比例','用少数阳性的教学例子，检查全预测阴性时各指标表达什么。'],
  ['查看概率质量','比较预测概率与观察阳性频率，关注每组记录数。'],
  ['完成保留评价','固定输入、模型和阈值，再运行 test；评价后不再据此修改。'],
  ['设计理由','把正确率、错误类型、概率和未见数据表现放在一起解释。']],bottom:'对应工作单 7；Notebook C、D',note:'维持原train模型，不合并validation重训。按工作单提交固定方案并由教师释放测试标签。测试开关属于教学流程约束。不要在导入中展示测试结果。'},
 {title:'学生完成的解释',lead:'用自己的实验，把七个概念连接成一页说明或流程图',list:[
  '模型接收什么，输出什么，哪些量由数据估计？',
  '训练、预测与评价各用哪份数据，为什么？',
  'Bayes 怎样组合先验与症状信息，依赖什么假设？',
  '类别指标和 log loss 各揭示什么差异？',
  '为什么只报告 accuracy 不足以解释医学预测表现？'],bottom:'保留初始预想，用一次计算或观察说明理解如何改变',note:'具体计算表、参数、操作顺序及提交要求均见 student-worksheet.md。两次课堂各45分钟，课间60–90分钟。选做拓展不作为核心满分要求。'}
];

const deck=Presentation.create({slideSize:{width:1280,height:720}});
deck.theme.defaultFont=font;
function text(s,str,x,y,w,h,size=30,color=ink,bold=false){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=str;
 sh.text.style={typeface:font,fontSize:size,color,bold,wrap:'square',insets:0,verticalAlignment:'top'};
}
const tables=[];
for(const [i,d] of slides.entries()){
 const s=deck.slides.add();s.background.fill=paper;
 if(d.cover){
  text(s,'生物医学数据科学',76,72,1120,48,27,teal,true);
  text(s,d.title,76,185,1130,180,65,ink,true);
  text(s,d.lead,76,410,1130,70,38,teal);
  text(s,d.body,76,540,1130,90,28,muted);
 }else{
  text(s,d.title,72,48,1140,65,44,ink,true);
  text(s,d.lead,72,136,1140,70,31,teal,true);
  if(d.rows){
   const step=d.rows.length===5?77:94;
   d.rows.forEach(([label,body],j)=>{
    text(s,label,72,244+j*step,318,66,27,teal,true);
    text(s,body,410,244+j*step,798,78,29,ink);
   });
  }else if(d.table){
   tables.push(i+1);
   const rows=d.table.length,columns=d.table[0].length;
   const tb=s.tables.add({rows,columns,left:72,top:240,width:1136,height:rows*62,values:d.table,columnWidths:[340,300,496]});
   for(let r=0;r<rows;r++)for(let c=0;c<columns;c++){
    const cell=tb.getCell(r,c);cell.fill=r===0?'#E7EFEB':'#FFFFFF';
    cell.text.style={typeface:font,fontSize:26,bold:r===0,color:r===0?teal:ink,insets:10};
   }
   if(d.after)text(s,d.after,72,240+rows*62+28,1136,108,29,muted);
  }else{
   const step=d.list.length>=6?57:75;
   d.list.forEach((line,j)=>{
    text(s,String(j+1).padStart(2,'0'),72,237+j*step,65,48,27,teal,true);
    text(s,line,157,237+j*step,1051,65,30,ink);
   });
  }
  if(d.bottom)text(s,d.bottom,72,654,1115,32,22,muted);
 }
 text(s,String(i+1).padStart(2,'0'),1216,681,40,24,16,muted);
 s.speakerNotes.text=(d.note||'先请学生提出预想，再进入工作单完成计算与实验。')+'\n配套来源：student-worksheet.md；experiment-design.md；data/README.md。\n'+(d.source||'方法参考：https://scikit-learn.org/stable/modules/naive_bayes.html ；https://scikit-learn.org/stable/modules/model_evaluation.html')+'\n数据署名：Jacek Czerniak，UCI Acute Inflammations，DOI 10.24432/C5V59S，CC BY 4.0。本课进行了温度二元化、0/1编码与固定划分。';
}
await fs.writeFile(build+'/content.json',JSON.stringify(slides,null,2));
await (await PresentationFile.exportPptx(deck)).save(build+'/candidate.pptx');
for(const [i,slide] of deck.slides.items.entries()){
 const png=await deck.export({slide,format:'png',scale:1});
 await fs.writeFile(build+`/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await png.arrayBuffer()));
}
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
await fs.mkdir(build+'/final',{recursive:true});
const validated=build+'/final/validated-'+Date.now()+'.pptx';
const result=await finalizePresentation({workspaceDir:repo,candidatePath:build+'/candidate.pptx',finalPath:validated,
 pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:tables,fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:build+'/validation-'+Date.now()+'.json'});
console.log(JSON.stringify(result));
await fs.copyFile(validated,base+'/slides/naive-bayes-experiment-intro.pptx');
console.log('Created '+slides.length+' slides.');
