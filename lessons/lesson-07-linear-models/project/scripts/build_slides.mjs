import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const repo=path.resolve(import.meta.dirname,'../../../..');
const base=path.resolve(import.meta.dirname,'..');
const runtime=process.env.CODEX_ARTIFACT_RUNTIME||'C:/Users/rongs/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const skill='C:/Users/rongs/.codex/plugins/cache/openai-primary-runtime/presentations/26.1013.11914/skills/presentations';
const build=repo+'/.tmp/linear-models/slides'; await fs.mkdir(build,{recursive:true}); await fs.mkdir(base+'/slides',{recursive:true});
const deck=Presentation.create({slideSize:{width:1280,height:720}}); const font='Microsoft YaHei',ink='#193638',teal='#087C77',muted='#52686A',orange='#A94F1C',paper='#FAFBF8'; deck.theme.defaultFont=font;
const S=[
 ['线性模型、LDA 与 Logistic Regression','简单模型为什么仍然重要？','第 8 讲 PBL 实验导入\n从评分、概率与错误代价回到决策'],
 ['本讲的驱动问题','面对同一份小样本心脏病数据，如何理解两种方法的适用条件？','LDA 与 logistic 的建模对象、假设、优化目标和参数量不同。\n实验要追问这些差异何时改变概率、边界和错误代价，而不是只比较一个分数。'],
 ['八个核心问题','每个问题都对应一个可观察的实验产出','两种方法建模什么、假设什么、优化什么？\n参数量如何随 one-hot 和协方差增长？\n概率来源、边界、评价、阈值、稳定性与因果边界'],
 ['共同的线性评分','两种模型都比较一个形如 z = β₀ + xᵀβ 的分数','x 是输入向量；β 是权重；β₀ 是截距。\n改变权重会改变评分方向与边界。\n系数大小依赖单位、标准化、参照水平和同时进入模型的变量。'],
 ['Logistic regression','从条件概率出发，用 sigmoid 把任意评分变成 0–1','p = 1 / (1 + e⁻ᶻ)\nlogit(p) = log[p/(1−p)] = z\nβⱼ 每增加一个建模单位，odds 乘以 e^βⱼ。\nOR 不是概率倍数，也不是自动的因果效应。'],
 ['LDA','从每个类别里的特征分布出发，再用 Bayes 更新','X|Y=k ~ N(μₖ, Σ)\nμₖ：类别中心；Σ：共享的相关与尺度；πₖ：类别先验。\n给定类别的密度 × 先验，经归一化得到 posterior。'],
 ['LDA 为什么得到线性边界','共享协方差让比较两类时的二次项抵消','δₖ(x) 中的 xᵀΣ⁻¹x 对两类相同，因此比较分数只剩线性项。\n若每类使用不同协方差，通常得到二次边界。\n“能否输出概率”不是 LDA 与 logistic 的真正差异。'],
 ['数据：270 条心脏病记录','小样本、混合变量、二分类结局','13 个输入：连续、二元、名义和有序/计数变量。\n目标：heart_disease_present。\n120 阳性、150 阴性；无缺失教学文件。\n这是教学比较数据，不是独立临床队列。'],
 ['实验协议','先分工，再比较','分层 80% development / 20% locked test，random_state=2026。\n连续变量在训练折内标准化；分类变量在训练折内 one-hot。\n所有步骤放入 Pipeline，避免预处理泄漏。'],
 ['模型比较回答不同问题','比较假设、目标与参数，而不是模型排名','Gaussian NB：独立性较强的生成式基线。\nLDA：共享协方差的生成式线性边界。\nLogistic：直接建模条件概率。\n选择理由必须说明数据条件、研究目标和代价。'],
 ['评价维度','区分、概率、阈值错误和不确定性各有职责','ROC-AUC / PR-AUC：排序区分。\nBrier / log loss：概率质量。\nSensitivity / specificity / FN / FP：指定阈值下的错误。\nBootstrap：小样本结果的不确定性。'],
 ['阈值与错误代价','0.5 是默认值，不是医学结论','本案例代价：5×FN + FP。\n在 development 上选择阈值，降低阈值通常减少 FN、增加 FP。\n先冻结模型、预处理和阈值，再打开 locked test。'],
 ['系数解释与稳定性','预测稳定不等于每个系数稳定','OR 依赖建模单位、参照水平和其他变量固定。\n共线性或近重复变量可能改变系数分配，而总体预测变化较小。\n系数是条件关联，不自动是致病机制。'],
 ['实验路线','问题 → 对照 → 证据 → 边界','A：审计数据与无泄漏流程。\nB：开发集比较模型与概率。\nC：阈值、代价、系数和假设压力测试。\nD：冻结后评价 locked test，最后写 CERB。'],
 ['学生最终要回答','用自己的分析连接八个知识点','两种模型分别建模什么，参数量和假设怎样影响选择？\n概率从哪里来，假设承受了什么压力？\n漏诊与误报如何影响阈值？\n哪些结论不能升级为临床或因果结论？']
];
function text(s,str,x,y,w,h,size=30,color=ink,bold=false){const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}}); sh.text=str; sh.text.style={typeface:font,fontSize:size,color,bold,wrap:'square',insets:0,verticalAlignment:'top'};}
for(const [i,d] of S.entries()){const s=deck.slides.add();s.background.fill=paper; if(i===0){text(s,'生物医学数据科学',76,74,1120,45,27,teal,true);text(s,d[0],76,190,1120,150,62,ink,true);text(s,d[1],76,405,1120,65,38,teal);text(s,d[2],76,535,1120,80,28,muted);}else{ text(s,d[0],72,48,1136,65,44,ink,true); text(s,d[1],72,136,1136,70,32,teal,true); text(s,d[2],72,250,1136,340,31,ink); } text(s,String(i+1).padStart(2,'0'),1216,681,40,24,16,muted); s.speakerNotes.text='先请学生提出预想，再进入工作单和 Notebook。\n来源：WORKPLAN.md；student-worksheet.md；data/README.md。\n数据整理自项目已有 UCI 多站点心脏病字段，仅作教学比较，不支持临床或因果结论。';}
const candidate=build+'/candidate.pptx'; await (await PresentationFile.exportPptx(deck)).save(candidate); for(const [i,slide] of deck.slides.items.entries()){const png=await deck.export({slide,format:'png',scale:1}); await fs.writeFile(build+`/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await png.arrayBuffer()));}
const {finalizePresentation}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href); await fs.mkdir(build+'/final',{recursive:true}); const finalPath=build+'/final/linear-models-pbl-intro-'+Date.now()+'.pptx'; const result=await finalizePresentation({workspaceDir:repo,candidatePath:candidate,finalPath,pythonExecutable:runtime+'/python/python.exe',integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,receiptPath:build+'/validation-'+Date.now()+'.json'}); console.log(JSON.stringify(result)); await fs.copyFile(finalPath,base+'/slides/linear-models-pbl-intro.pptx');
