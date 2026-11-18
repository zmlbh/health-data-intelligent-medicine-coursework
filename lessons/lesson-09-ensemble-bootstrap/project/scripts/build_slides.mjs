import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const base = path.resolve(import.meta.dirname, '..');
const repo = path.resolve(base, '../../..');
const runtime = process.env.CODEX_ARTIFACT_RUNTIME || 'C:/Users/rongs/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES = runtime + '/node/node_modules';
const {Presentation, PresentationFile} = await import(pathToFileURL(runtime + '/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const font = 'Microsoft YaHei', ink='#193638', teal='#087C77', muted='#52686A', orange='#AD5726', paper='#FAFBF8', blue='#52789F', rule='#D8E1DE', tint='#EAF4F2', warm='#F6E3D7';
const SOURCES='\n数据来源：方案 A WDBC https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic ；方案 B CTG https://archive.ics.uci.edu/dataset/193/cardiotocography\n方法参考：https://scikit-learn.org/stable/modules/ensemble.html';
deck.theme.defaultFont = font;
function txt(s, text, x, y, w, h, size=28, color=ink, bold=false) {
  const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=text; sh.text.style={typeface:font,fontSize:size,color,bold,wrap:'square',insets:0,verticalAlignment:'top'}; return sh;
}
function slide(title,kicker='PBL 课程导入',note='') { const s=deck.slides.add(); s.background.fill=paper; txt(s,kicker,70,34,1100,30,20,teal,true); txt(s,title,70,86,1140,70,43,ink,true); txt(s,'第 10 讲   Ensemble learning',70,676,700,24,16,muted); txt(s,String(deck.slides.items.length).padStart(2,'0'),1170,676,50,24,16,muted); s.speakerNotes.text=note+SOURCES; return s; }
function table(s, values, left=70, top=190, width=1140, height=330, size=26, columnWidths) { const t=s.tables.add({rows:values.length,columns:values[0].length,left,top,width,height,values,...(columnWidths?{columnWidths}:{})}); t.borders.assign({fill:rule,width:.6}); for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c); cell.fill=r===0?ink:paper; cell.text.style={typeface:font,fontSize:size,color:r===0?'#FFFFFF':ink,bold:r===0,wrap:'square',insets:10,verticalAlignment:'middle'};} return t; }
function line(s,x1,y1,x2,y2,color=teal,width=5){const sh=s.shapes.add({geometry:'line',position:{left:x1,top:y1,width:x2-x1,height:y2-y1},line:{fill:color,width}});return sh;}
function box(s,text,x,y,w,h,{fill='#FFFFFF',border=ink,color=ink,size=22,bold=false,align='center'}={}) {
  const sh=s.shapes.add({geometry:'roundRect',position:{left:x,top:y,width:w,height:h},fill,line:{style:'solid',fill:border,width:1.5}});
  sh.text=text; sh.text.style={typeface:font,fontSize:size,color,bold,wrap:'square',insets:10,alignment:align,verticalAlignment:'middle'}; return sh;
}
// 1
{const s=deck.slides.add();s.background.fill=ink; txt(s,'生物医学数据科学   第 10 讲',80,82,1100,50,27,'#A5D5CA'); txt(s,'集成学习与 Bootstrapping',78,214,1120,110,70,'#FFFFFF',true); txt(s,'多个模型如何组合成更稳定的强模型？',82,380,1100,70,38,'#FFFFFF'); txt(s,'从一棵决策树到可审计的模型比较',82,535,1100,55,28,'#A5D5CA'); s.speakerNotes.text='先提出研究问题，不公布模型排名。';}
// 2
{const s=slide('本节课的研究问题','学习问题','学生需要提出有条件的选择，而不是只报一个最高分。第一个要学的知识点是决策树：后面所有集成方法都由树组成。'); table(s,[['问题','要观察的证据'],['一棵决策树怎样预测，为什么不稳定？','切分规则、叶节点比例；换一份训练样本后树是否改变'],['多个模型为何可能更好？','模型错误是否相关，聚合是否降低波动'],['bootstrap 改变了什么？','样本重抽样、袋外记录和训练多样性'],['随机森林多了什么？','每个节点的候选特征随机化'],['boosting 如何改进？','顺序更新、错分权重或负梯度'],['怎样公平比较、怎样选？','同一划分与指标；超参数、特征重要性与选型经验']],70,180,1140,420,24,[470,670]);}
// 3
{const s=slide('数据方案 A：WDBC 乳腺肿块细胞核特征','贯穿案例 · 数据方案 A','数据集说明：UCI WDBC；sklearn 离线载入。标签重编码为 malignant=1。教授在方案 A / B 中二选一，选定后删除另一张数据页。'); table(s,[['内容','课程定义'],['观察单位','一条乳腺肿块细针穿刺样本的图像特征记录'],['数据规模','569 条记录，30 个连续特征，无缺失'],['开发 / 测试','455 / 114；开发集再分 train 341、validation 114'],['输入边界','sample_id 只追踪，不进入模型'],['数据特点','近似线性可分：LR / SVM 已接近满分，集成的收益主要体现在胜过单树'],['结论边界','不解释为未来风险、因果效应或跨医院表现']],70,180,1140,420,24,[260,880]);}
// 4
{const s=slide('数据方案 B：CTG 胎心监护信号特征','贯穿案例 · 数据方案 B','UCI Cardiotocography（Ayres-de-Campos 等，2000；CC BY 4.0）。一个录音文件被切成多个分析片段，所以按 recording_id 分组划分，避免同一录音同时出现在训练和验证中。教授在方案 A / B 中二选一。'); table(s,[['内容','课程定义'],['观察单位','一段胎心监护（CTG）信号片段的自动分析特征；2126 段来自 352 个录音文件'],['数据规模','21 个连续特征（胎心基线、加速 / 减速、变异性、直方图统计），无缺失'],['标签','专家判读 NSP：病理型 pathologic=1（176 条，8.3%）；正常与可疑 = 0'],['划分','按录音文件分组：train 1279、validation 424、test 423'],['输入边界','sample_id、recording_id 不进入模型；同一录音的片段不能跨集合'],['数据特点','树集成明显胜过单树，并在 PR-AUC、balanced accuracy 上优于 LR / SVM']],70,180,1140,420,23,[260,880]);}
// 5
{const s=slide('知识点 0：一棵决策树怎样做预测','机制 0 · 决策树','先读懂一棵树，后面的 bagging、随机森林和 boosting 都建立在它上面。示例树：WDBC 训练集（341 例）上 max_depth=2 的树；CTG 的对应示例见教师参考。');
 const root=box(s,'worst perimeter ≤ 105.95 ?',270,178,360,58,{bold:true}); const L=box(s,'worst concave points ≤ 0.17 ?',70,300,330,58,{size:21}); const R=box(s,'mean concave points ≤ 0.05 ?',500,300,330,58,{size:21});
 const leaf=(t,x,m)=>box(s,t,x,430,180,86,{fill:m?warm:tint,border:m?orange:teal,size:20});
 const l1=leaf('良 198 · 恶 4\nP(恶性) = 0.02',62,false), l2=leaf('良 0 · 恶 3\nP(恶性) = 1.00',252,true), l3=leaf('良 13 · 恶 8\nP(恶性) = 0.38',466,false), l4=leaf('良 3 · 恶 112\nP(恶性) = 0.97',656,true);
 for (const [a,b] of [[root,L],[root,R],[L,l1],[L,l2],[R,l3],[R,l4]]) s.shapes.connect(a,b,{kind:'straight',fromSide:'bottom',toSide:'top',line:{style:'solid',fill:muted,width:1.5}});
 for (const [t,x,y] of [['是',318,248],['否',566,248],['是',168,376],['否',298,376],['是',584,376],['否',714,376]]) txt(s,t,x,y,30,26,18,teal,true);
 txt(s,'橙色叶节点预测为恶性；叶节点中恶性的比例就是预测概率。',62,532,780,28,18,muted);
 txt(s,'切分',880,182,330,34,25,teal,true); txt(s,'每一步选一个特征和阈值，让子节点尽量“纯”（Gini 不纯度下降最多）',880,220,330,90,20,ink);
 txt(s,'预测',880,318,330,34,25,teal,true); txt(s,'样本沿规则从根走到叶节点，读出该叶节点的类别比例。',880,356,330,60,20,ink);
 txt(s,'尺度',880,428,330,34,25,teal,true); txt(s,'只比较“≤ 阈值”的大小顺序，换单位不改变切分，所以不需要标准化',880,466,330,90,20,ink);
 txt(s,'树越深，规则越细；深到每个叶节点只剩一类时，训练集可以全对。',70,592,1140,40,25,teal,true);}
// 6
{const s=slide('单棵树的问题：容易过拟合，而且不稳定','机制 0 · 决策树','左表：WDBC train 拟合、validation 评价。右图：对 train 做 10 次 bootstrap 重抽样，各拟合一棵 max_depth=2 的树，统计根节点用了哪个特征。CTG 上单树同样不稳定：开发集五折 CV 的 AUC 标准差约 0.11。');
 table(s,[['最大深度','叶节点数','训练准确率','验证准确率'],['1','2','0.933','0.912'],['2','4','0.956','0.956'],['3','7','0.979','0.974'],['4','11','0.988','0.965'],['不限','17','1.000','0.965']],70,180,620,330,22);
 txt(s,'换一份训练样本，根节点就变了',740,180,470,36,25,teal,true); txt(s,'10 次 bootstrap 重抽样后的根节点特征：',740,226,470,30,20,ink);
 [['worst perimeter',4],['worst area',3],['worst radius',2],['mean concave points',1]].forEach(([name,n],i)=>{const y=278+i*48; txt(s,name,740,y,215,30,19,ink); s.shapes.add({geometry:'rect',position:{left:960,top:y+3,width:n*45,height:24},fill:teal,line:{fill:'none',width:0}}); txt(s,n+' 次',968+n*45,y,70,30,19,muted);});
 txt(s,'阈值也在 105.95 到 113.75 之间变动。',740,474,470,30,19,muted);
 txt(s,'单棵深树：偏差低、方差高。训练数据稍有变化，树和预测就跟着变，这正是集成要解决的问题。',70,560,1140,80,25,teal,true);}
// 7
{const s=slide('从一棵树到许多棵树','机制 1','随机森林在 sklearn 中默认把各棵树的概率取平均（软投票），再按 0.5 判类。'); txt(s,'同一批验证样本',80,205,330,45,29,teal,true); for(let i=0;i<5;i++){const x=485+i*110; txt(s,'树 '+(i+1),x,190,80,40,24,ink,true); line(s,x+40,250,x+40,365,[teal,blue,orange,teal,blue][i],4); txt(s,['0','1','0','1','1'][i],x+28,380,35,38,28,ink,true);} line(s,500,465,900,465,ink,3); txt(s,'聚合：多数票或概率平均',430,500,500,48,32,teal,true); txt(s,'前提：基模型的错误不能完全同步',80,590,1040,48,29,muted);}
// 8
{const s=slide('集成为什么有效：平均能降低方差','机制 1 · 核心原理','只要求理解式子的含义，不要求推导。σ²：单个模型预测的方差；ρ：两个模型预测之间的相关；B：模型个数。右图来自 WDBC：同一批 30 份 bootstrap 训练集分别训练三种模型，统计 114 个验证样本中预测类别会改变的比例。');
 box(s,'平均后的方差  =  ρσ²  +  (1 − ρ) σ² / B',70,180,640,90,{fill:tint,border:teal,size:32,bold:true});
 txt(s,'① B 越大，第二项越小：树越多越稳，但最多降到 ρσ²。',80,296,630,66,22,ink);
 txt(s,'② 想继续降，就要降低 ρ：让模型彼此不同，随机森林因此随机挑特征。',80,360,630,66,22,ink);
 txt(s,'③ 平均只降方差、不降偏差：适合深树（偏差低、方差高）。Boosting 反过来，用浅树逐轮修正，主要降偏差。',80,438,630,96,22,ink);
 s.charts.add('bar',{position:{left:750,top:180,width:460,height:370},title:'验证样本类别翻转率（%）',titleTextStyle:{typeface:font,fontSize:18,bold:true,fill:ink},categories:['单棵树','Bagging','随机森林'],series:[{name:'类别翻转率',values:[24.6,15.8,7.0],fill:teal,points:[{idx:0,fill:orange},{idx:1,fill:blue}]}],barOptions:{direction:'column',grouping:'clustered',gapWidth:80},hasLegend:false,dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.0',textStyle:{typeface:font,fontSize:18,fill:ink}},xAxis:{textStyle:{typeface:font,fontSize:17,fill:ink}},yAxis:{min:0,max:30,majorUnit:10,textStyle:{typeface:font,fontSize:15,fill:muted},majorGridlines:{style:'solid',fill:rule,width:1}},chartLine:{style:'solid',fill:'none',width:0}});
 txt(s,'集成的收益来自“平均掉不稳定”；前提是基模型各有不同的错误。',70,594,1140,40,25,teal,true);}
// 9
{const s=slide('Bootstrap 与 Bagging','机制 2','先让学生手算一次有放回抽样，再运行完整模拟。OOB 是 bagging / 随机森林自带的验证：sklearn 中设置 oob_score=True。'); txt(s,'一次有放回抽样（从 5 条记录中抽 5 次）：2，2，5，1，2',80,180,1100,40,27,ink,true); table(s,[['原训练索引','1','2','3','4','5'],['出现次数','1','3','0','0','1'],['是否袋外（OOB）','否','否','是','是','否']],70,240,1140,170,25,[290,170,170,170,170,170]); txt(s,'Bootstrap',80,440,250,45,31,teal,true); txt(s,'从同一训练集反复有放回抽样，制造不同训练集；每棵树用一份，可以并行训练。',300,446,900,80,24,ink); txt(s,'OOB',80,540,250,45,31,teal,true); txt(s,'平均约 36.8% 的记录不会被某棵树抽到。用这些记录给该树打分并汇总，得到 OOB 误差：不另留验证集也能估计表现。',300,546,900,90,24,ink);}
// 10
{const s=slide('随机森林增加了哪一种随机性？','机制 3','把样本重抽样和特征候选随机化分开，学生才能判断每一步的作用。sklearn 分类森林的 max_features 默认是 sqrt。'); table(s,[['方法','样本','节点候选特征','待比较问题'],['单棵决策树','一份训练集','全部','基线波动有多大？'],['Bagging','bootstrap','全部','平均多棵树能否降低波动？'],['Random forest','bootstrap','每次随机抽 sqrt 特征','额外随机化是否降低树间相关性？']],70,195,1140,310,25); txt(s,'特征随机化的目的：降低树间相关 ρ。ρ 高时，再多的树也只是重复同一种错误。',80,550,1100,80,28,teal,true);}
// 11
{const s=slide('Boosting 的顺序依赖','机制 4','教师演示 AdaBoost 权重或 Gradient Boosting 负梯度，不要求学生手写优化器。'); table(s,[['轮次','AdaBoost 关注','Gradient Boosting 更新'],['第 1 轮','初始权重相同','从当前预测开始'],['下一轮','错分样本权重上升','拟合 log-loss 的负梯度 y−p'],['继续增加','可能追随噪声','训练下降不保证验证上升']],70,200,1140,300,27); txt(s,'Bagging：并行、平均深树、主要降方差。Boosting：顺序、叠加浅树、主要降偏差。',80,550,1100,80,28,teal,true);}
// 12
{const s=slide('常用实现与关键超参数','应用 1','不要求学生安装或运行 XGBoost / LightGBM，能说明它们和 sklearn 梯度提升的关系即可。调参只在开发集内（CV 或 OOB）完成，测试集不参与。'); table(s,[['方法 / 实现','先关注的超参数','使用经验'],['随机森林\nRandomForestClassifier','n_estimators（几百棵）、max_features、min_samples_leaf','默认值通常已不错；树多不会导致过拟合，只是变慢；用 OOB 或 CV 检查'],['梯度提升\nGradientBoosting / HistGradientBoosting','learning_rate × n_estimators、max_depth（常用 3–6）、subsample','学习率越小需要越多轮；轮数要用验证集或 early stopping 决定'],['XGBoost / LightGBM','同上，另有正则化参数（如 lambda 和 min_child_weight）','本质仍是梯度提升树：加入树复杂度正则和二阶导信息，速度更快，可直接处理缺失值；表格数据研究中最常用']],70,180,1140,420,21,[330,370,440]);}
// 13
{const s=slide('特征重要性：最常用，也最容易误读','应用 2','数字来自 WDBC：300 棵树的随机森林；置换重要性在 validation 上以 ROC-AUC 计算，重复 20 次。CTG 上 ALTV、DP、ASTV 的置换重要性较明显（见教师参考）。');
 for (const [x,head,api,body] of [[70,'不纯度重要性','feature_importances_','训练时每个特征带来的不纯度下降总和。计算快；但偏向取值多的连续特征，高度相关的特征会“瓜分”重要性。'],[670,'置换重要性','permutation_importance','在验证集上打乱一个特征，看指标下降多少。更接近“预测时离不开它”；但相关特征能互相“替补”，每个都显得不重要。']]) { s.shapes.add({geometry:'roundRect',position:{left:x,top:180,width:540,height:250},fill:'#FFFFFF',line:{style:'solid',fill:rule,width:1}}); txt(s,head,x+28,200,480,36,26,teal,true); txt(s,api,x+28,240,480,28,18,muted); txt(s,body,x+28,282,484,130,21,ink); }
 txt(s,'例（WDBC）：worst perimeter、area、radius 两两 |r| > 0.9，不纯度重要性被三者分摊，各约 0.12–0.13；单独打乱其中任一个，验证 AUC 下降不到 0.002。',70,456,1140,70,21,ink);
 txt(s,'重要性说明“模型用了什么来预测”，不等于生物学因果；报告前先看特征之间的相关性。',70,560,1140,80,26,teal,true);}
// 14
{const s=slide('选型：什么时候用什么','应用 3','这些是经验规则，不是定律；最终仍以同一协议下的验证证据为准。'); table(s,[['情形','优先考虑','理由与代价'],['样本少、关系近似线性、需要解释系数','Logistic regression','稳定、可解释；先把它作为基线'],['中小样本、边界弯曲','RBF-SVM','需要标准化，并调 C、gamma'],['表格数据、非线性或交互多、想要稳健默认值','随机森林','几乎不用调参，自带 OOB；解释性下降'],['表格数据、追求最好表现、愿意调参','梯度提升（XGBoost / LightGBM）','常常最强；必须用验证集控制轮数'],['需要人能直接读懂的规则','浅决策树','易读，但单树不稳定、表现有限']],70,175,1140,390,22,[470,330,340]); txt(s,'先跑简单基线；复杂模型要在同一划分、同一指标下证明“确实更好”。',80,592,1080,45,27,teal,true);}
// 15
{const s=slide('实验协议：先锁定比较，再看结果','公平比较','协议要先于测试结果。'); table(s,[['项目','固定规则'],['模型','单树、bagging、random forest、AdaBoost、gradient boosting；LR / SVM 作基线'],['验证','train 拟合、validation 比较；开发集（train+validation）内五折 CV 作补充；预设参数，不用测试集调参'],['分组','方案 B：同一 recording_id 的片段必须在同一集合、同一折（StratifiedGroupKFold）'],['预处理','LR / SVM 在折内 StandardScaler；树模型不需要'],['指标','ROC-AUC、balanced accuracy、阳性类 sensitivity、specificity；类别不平衡时加 PR-AUC'],['测试','配置写下后一次揭示留出记录（方案 A 114 条 / 方案 B 423 条）']],70,175,1140,420,22,[200,940]);}
// 16
{const s=slide('稳定性与不确定性不是同一个问题','实验设计','学生要把结论范围写清楚。bootstrap 有两种用途：制造训练集（bagging），以及估计指标的波动范围。'); table(s,[['实验对象','能回答什么','不能回答什么'],['重复训练重抽样','训练样本扰动下预测是否变化','指标的置信区间；新人群上的表现'],['固定模型的测试索引重抽样','该组已拟合模型指标的区间','重新训练或换模型带来的变化'],['外部人群 / 新医院','真实部署环境的泛化不确定性','本课数据无法回答：没有外部队列'],['本课数据','机制与协议是否可复现','不能替代外部验证或因果研究']],70,190,1140,350,23);}
// 17
{const s=slide('学生产出：证据驱动的研究备忘录','任务','不追求唯一赢家，要求结论与证据边界一致。'); table(s,[['必须回答','最低证据'],['单树为什么不稳定','深度—训练 / 验证对照，或重抽样后树结构的变化'],['集成是否改善','与单树、LR / SVM 在同一协议下比较验证指标和混淆矩阵'],['是否更稳定','重复拟合预测 SD 或类别翻转率'],['为什么可能改善','用方差公式连接抽样、特征随机化或顺序更新'],['bagging 与 boosting','训练方式、基学习器、主要降方差还是降偏差'],['如何选择','表现、稳定性、解释成本、验证范围']],70,170,1140,390,23,[330,810]); txt(s,'最终输出：250–400 字备忘录 + 模型比较表 + bagging / boosting 对照表',80,602,1100,45,28,teal,true);}
// 18
{const s=slide('课堂工作流','活动安排'); table(s,[['阶段','学生行动','工作单'],['1 学概念','读懂一棵树；手算投票和一次 bootstrap 抽样','A–C'],['2 运行','比较单树、bagging、随机森林、boosting；看树数、OOB、特征重要性','D–E'],['3 比较','同一协议比较 LR / SVM / RF / GB，并给出选型理由','F'],['4 解释','区分预测波动与指标区间，写清结论范围','G'],['5 写作','提交研究备忘录和 bagging / boosting 对照表','H']],70,180,1140,390,24,[200,800,140]); txt(s,'工作单 A–H 与本页阶段对应',80,600,900,45,28,teal,true);}
// 19
{const s=slide('证据边界','结束讨论','把“模型在这份数据上表现如何”与“模型在真实临床中是否有用”分开。'); txt(s,'可以说',85,205,250,45,31,teal,true); txt(s,'在固定分割、指标和参数下，比较不同集成机制的表现与训练扰动稳定性',85,270,480,140,30,ink); txt(s,'不能直接说',690,205,300,45,31,orange,true); txt(s,'模型发现了因果因素、适用于所有医院，或最高测试分就是最终方案',690,270,470,140,30,ink); txt(s,'下一步：独立人群、预注册协议、外部验证与概率校准。',85,565,1070,45,30,teal,true);}
const out = base + '/slides/ensemble-pbl.pptx'; await fs.mkdir(path.dirname(out),{recursive:true}); await (await PresentationFile.exportPptx(deck)).save(out); console.log(out);
