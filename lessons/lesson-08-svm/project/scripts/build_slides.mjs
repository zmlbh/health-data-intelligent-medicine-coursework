import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const repo=path.resolve(import.meta.dirname,'../../../..');
const base=path.resolve(import.meta.dirname,'..');
const runtime=process.env.CODEX_ARTIFACT_RUNTIME||'C:/Users/rongs/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill=process.env.CODEX_PRESENTATIONS_SKILL||'C:/Users/rongs/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=runtime+'/node/node_modules';
const {Presentation,PresentationFile}=await import(pathToFileURL(runtime+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(skill+'/container_tools/artifact_tool_utils.mjs').href);
const build=repo+'/.tmp/svm/slides';
await fs.mkdir(build+'/final',{recursive:true});
await fs.mkdir(base+'/slides',{recursive:true});
const trainText=await fs.readFile(base+'/data/student/train.csv','utf8');
const lines=trainText.trim().split(/\r?\n/),headers=lines.shift().split(',');
const records=lines.map(line=>Object.fromEntries(line.split(',').map((x,i)=>[headers[i],i?Number(x):x])));
const geoText=await fs.readFile(repo+'/.tmp/svm/feasibility/geometry.csv','utf8');
const gl=geoText.trim().split(/\r?\n/),gh=gl.shift().split(',');
const geometry=gl.map(line=>Object.fromEntries(line.split(',').map((x,i)=>[gh[i],i&&x!=='True'&&x!=='False'?Number(x):x])));
const result=JSON.parse(await fs.readFile(repo+'/.tmp/svm/feasibility/summary.json','utf8'));
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const font='Microsoft YaHei',ink='#193638',teal='#087C77',muted='#52686A',orange='#AD5726',paper='#FAFBF8',blue='#52789F';
deck.theme.defaultFont=font;
const sourceData='UCI Vertebral Column, Guilherme Barreto and Ajalmar Neto. DOI: https://doi.org/10.24432/C5K89B . CC BY 4.0. Official metadata: https://archive.ics.uci.edu/dataset/212/vertebral+column . Teaching splits: seed9, two prespecified inputs.';
const sourceSVM='方法参考：https://scikit-learn.org/stable/modules/svm.html 及 /modules/generated/sklearn.svm.SVC.html 。';
const tableOwners=[],chartOwners=[];

function txt(s,str,x,y,w,h,size=30,color=ink,bold=false){
  const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=str;sh.text.style={typeface:font,fontSize:size,color,bold,wrap:'square',insets:0,verticalAlignment:'top'};
  return sh;
}
function slide(title,kicker='概念与实验',note=''){
  const s=deck.slides.add();s.background.fill=paper;
  txt(s,kicker,70,35,1100,30,20,teal,true);
  txt(s,title,70,88,1140,80,43,ink,true);
  txt(s,'第 9 讲   SVM 与 Margin',70,676,800,25,16,muted);
  txt(s,String(deck.slides.items.length).padStart(2,'0'),1170,676,50,25,16,muted);
  s.speakerNotes.text=note+'\n'+sourceSVM;
  return s;
}
function bottom(s,str){txt(s,str,74,606,1125,56,24,teal,true);}
function rows(s,items,{top=200,gap=97,labelWidth=270,size=29}={}){
  items.forEach(([label,body],i)=>{txt(s,label,75,top+i*gap,labelWidth,65,size,teal,true);txt(s,body,90+labelWidth,top+i*gap,1115-labelWidth,76,size,ink);});
}
function table(s,values,widths,{top=205,height=320,size=27,left=74,width=1130}={}){
  tableOwners.push(deck.slides.items.length);
  const t=s.tables.add({rows:values.length,columns:values[0].length,left,top,width,height,values,columnWidths:widths});
  t.borders.assign({fill:'#D8E1DE',width:.6});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?ink:paper;
    cell.text.style={typeface:font,fontSize:size,color:r===0?'#FFFFFF':ink,bold:r===0,wrap:'square',insets:12,verticalAlignment:'middle'};
  }
  return t;
}
function scatter(s,series,{left=65,top=183,width=745,height=402,xTitle='z₁',yTitle='z₂',xmin=-2.2,xmax=2.1,ymin=-1.5,ymax=2.3,legend=true}={}){
  chartOwners.push(deck.slides.items.length);
  // Use 12 significant digits for editable workbook portability; fits remain full precision.
  series=series.map(r=>({...r,xValues:r.xValues.map(v=>Number(v.toPrecision(12))),values:r.values.map(v=>Number(v.toPrecision(12)))}));
  const c=s.charts.add('scatter',{position:{left,top,width,height},series,
    scatterOptions:{style:'lineWithMarkers'},hasLegend:legend,legend:{position:'bottom',textStyle:{fontSize:18,fill:ink}},
    xAxis:{min:xmin,max:xmax,crossesAt:xmin,tickLabelPosition:'low',title:{text:xTitle,textStyle:{fontSize:18,fill:muted}},numberFormatCode:'0.0',textStyle:{fontSize:18,fill:muted},majorGridlines:null},
    yAxis:{min:ymin,max:ymax,crossesAt:ymin,tickLabelPosition:'low',title:{text:yTitle,textStyle:{fontSize:18,fill:muted}},numberFormatCode:'0.0',textStyle:{fontSize:18,fill:muted},majorGridlines:{fill:'#E0E6E3',width:.6}},
    chartFill:paper,plotAreaFill:paper,chartLine:{fill:'none',width:0}});
  applyPresentationChartFont(c,{fontFamily:font});return c;
}
function points(data,cls,x,y){return {name:cls?'AB':'NO',xValues:data.filter(r=>r.abnormal===cls).map(r=>r[x]),values:data.filter(r=>r.abnormal===cls).map(r=>r[y]),
  marker:{symbol:cls?'triangle':'circle',size:9,fill:cls?orange:teal},line:{fill:'none',width:0},fill:cls?orange:teal};}
function curve(name,xs,ys,color){return {name,xValues:xs,values:ys,marker:{symbol:'none'},line:{fill:color,width:2.5}};}
const geometricBounds={width:650,height:410,xmin:-2.5,xmax:2.3,ymin:-.9,ymax:1.9};
function boundary(name,w1,w2,b,value,color){
  // Supply only the visible segment: some renderers do not clip scatter lines.
  const {xmin,xmax,ymin,ymax}=geometricBounds,pts=[];
  for(const x of [xmin,xmax]){const y=(value-b-w1*x)/w2;if(y>=ymin&&y<=ymax)pts.push([x,y]);}
  for(const y of [ymin,ymax]){const x=(value-b-w2*y)/w1;if(x>=xmin&&x<=xmax)pts.push([x,y]);}
  return curve(name,pts.map(p=>p[0]),pts.map(p=>p[1]),color);
}

// 01
{
const s=deck.slides.add();s.background.fill=ink;
txt(s,'生物医学数据科学   第 9 讲',80,80,1100,55,27,'#A5D5CA');
txt(s,'SVM 与 Margin',78,219,1120,110,78,'#FFFFFF',true);
txt(s,'支持向量机如何确定分类边界？',82,382,1120,70,40,'#FFFFFF');
txt(s,'一个真实例子，连接几何、优化目标与方法选择',82,548,1110,64,29,'#A5D5CA');
s.speakerNotes.text='课堂导入。先讲概念与实验理由，计算和结果解释留给学生。'+sourceData;
}
// 02
{
const s=slide('本节课需要解释的问题','学习问题','学生应给出机制与条件，而非一张性能排行榜。');
rows(s,[['边界的选择','多条线都能分对，SVM增加了什么原则？'],['约束与违例','哪些点影响边界？为什么允许部分点违例？'],['方法的改变','C、kernel与gamma分别改变了什么？'],['选择的条件','尺度、重叠和任务需求怎样影响设置？']],{gap:93});
}
// 03
{
const s=slide('评分、边界与预测','核心概念 1');
txt(s,'f(z) = wᵀz + b',78,198,1120,95,58,teal,true);
rows(s,[['特征向量 z','一条记录的标准化输入；w是权重，b是截距。'],['超平面','f(z)=0的集合。二维空间中是一条直线。'],['决策分数','f的符号给出类别，大小是模型评分。']],{top:325,gap:88,labelWidth:230,size:28});
bottom(s,'decision score 没有自动的概率含义。');
}
// 04
{
const s=slide('Margin 与支持向量','核心概念 2');
rows(s,[['Margin（间隔）','可分情形关注边界离最近约束点有多远。'],['最大间隔原则','在可行线性边界中，最大化最小带标签距离。'],['Support vectors','当前SVM解中具有非零对偶权重的训练样本。'],['Hard / soft margin','硬间隔要求无违例；软间隔允许违例并付出代价。']],{gap:94,labelWidth:305,size:28});
}
// 05
{
const s=slide('贯穿案例：脊柱生物力学记录','数据与任务',sourceData+' 两个特征在协议中预先固定，用于二维几何教学，不宣称最佳。');
table(s,[['内容','本课定义'],['样本','310条真实记录，原始六个数值测量，无缺失'],['输入 x₁','pelvic_incidence：骨盆入射角'],['输入 x₂','degree_spondylolisthesis：脊椎滑脱程度'],['目标','NO正常100条；AB异常210条']],[260,870],{height:365,size:28});
bottom(s,'AB合并椎间盘突出与脊椎滑脱；标签不是未来风险。');
}
// 06
{
const s=slide('原始训练记录的完整范围','数据观察',sourceData+' 此图使用186条完整训练记录，无显示裁剪。后续局部边界图报告范围外点数，不删除拟合数据。');
scatter(s,[points(records,0,'pelvic_incidence','degree_spondylolisthesis'),points(records,1,'pelvic_incidence','degree_spondylolisthesis')],
 {xTitle:'Pelvic incidence (source scale)',yTitle:'Spondylolisthesis (source scale)',xmin:20,xmax:135,ymin:-25,ymax:450});
txt(s,'一行是什么？',860,217,350,50,30,teal,true);
txt(s,'一条患者测量记录\n\n两个输入便于看清几何，\n不代表全部可用信息。',860,280,350,210,27);
bottom(s,'先观察重叠与极值，再提出问题；极值不能仅因画图不便而删除。');
}
// 07
{
const s=slide('数据划分与预处理','实验协议',sourceData+' 两次分层train_test_split，seed9。scaler放入Pipeline。单位信息不足时保留source scale。');
table(s,[['集合','NO / AB','职责'],['训练186','60 / 126','拟合scaler与SVM'],['验证62','20 / 42','参数对照与配置选择'],['测试62','20 / 42','记录配置后一次评价']],[300,250,580],{height:310,size:29});
bottom(s,'StandardScaler只拟合训练集；ID只追踪记录，不进入模型。');
}
// 08
{
const s=slide('实验B：三条都能分对的线','问题与几何',sourceData+' 八点是按明示规则有意选择的可分训练子集，仅用于几何。先不显示距离计算结果。');
const [w1,w2]=result.geometry_w,b=result.geometry_b;
scatter(s,[points(geometry,0,'z1','z2'),points(geometry,1,'z1','z2'),
 ...[-.6,0,.6].map((o,i)=>boundary(['b − 0.6','b','b + 0.6'][i],w1,w2,b+o,0,[orange,ink,blue][i]))],geometricBounds);
txt(s,'只看训练错误，\n能选出唯一边界吗？',855,215,350,105,31,teal,true);
txt(s,'比较最近点距离。\n\n固定点与法向量，\n只平移截距。',855,365,345,160,28);
bottom(s,'八点用于看清定义；整体性能回到完整训练与保留数据。');
}
// 09
{
const s=slide('点到边界的距离','几何定义','同乘正数不改变边界，但改变分数。规范化后f=±1定义参考带。软间隔下带内允许有点。'+sourceData);
const [w1,w2]=result.geometry_w,b=result.geometry_b;
scatter(s,[points(geometry,0,'z1','z2'),points(geometry,1,'z1','z2'),
 ...[-1,0,1].map((v,i)=>boundary('f = '+v,w1,w2,b,v,[blue,ink,orange][i]))],geometricBounds);
txt(s,'几何距离',855,205,350,45,30,teal,true);
txt(s,'d = |f(z)| / ||w||',855,267,350,70,32);
txt(s,'规范化参考带总宽度',855,365,350,45,27,teal,true);
txt(s,'2 / ||w||',855,421,350,55,38);
bottom(s,'思考：把w和b同乘3，分数、距离和边界分别发生什么变化？');
}
// 10
{
const s=slide('实验C：删除一个点','支持向量的作用','先预测，后运行。删除非SV V072与SV V061，固定训练scaler和大C。冗余SV删除后未必改变解，勿普遍化。');
table(s,[['干预','保持不变','观察'],['删除一个非SV','scaler、C、其余七点','w、b和原八点分数变化'],['删除一个SV','相同控制条件','相同观测量']],[350,390,390],{height:270,size:27});
txt(s,'为什么冻结scaler？',78,515,1130,60,32,teal,true);
bottom(s,'重新估计尺度会同时移动所有坐标，无法只解释“删除点”的作用。');
}
// 11
{
const s=slide('不可分数据与 Hinge loss','核心概念 3','人工复制一个坐标并给相反标签，证明硬间隔无解。此干预不进入原始数据或正式评价。核函数同样不能解决同x异y的确定性矛盾。');
const xs=Array.from({length:61},(_,i)=>-1+3*i/60);
scatter(s,[curve('hinge',xs,xs.map(x=>Math.max(0,1-x)),teal)],{xTitle:'y × f',yTitle:'Hinge loss',xmin:-1,xmax:2,ymin:0,ymax:2.2,legend:false});
txt(s,'ℓ = max(0, 1 − y f)',855,205,350,95,33,teal,true);
txt(s,'分对但yf<1，\n仍然有间隔违例。\n\n同坐标相反标签，\n硬约束不能同时满足。',855,340,350,205,27);
bottom(s,'Soft margin允许违例，赋予代价后继续优化。');
}
// 12
{
const s=slide('Soft margin 的优化目标','核心概念 4');
txt(s,'min   ½||w||²  +  C Σ hingeᵢ',78,211,1130,95,52,teal,true);
rows(s,[['½||w||²','偏好小权重范数，对应较宽的线性参考带。'],['Σ hingeᵢ','统计间隔违例程度，分错与分对但带内的点都可贡献。'],['C','违例代价相对权重；较大C更强烈惩罚训练违例。']],{top:345,gap:85,labelWidth:240,size:28});
}
// 13
{
const s=slide('实验D：只改变 C','目标与对照','精确最优条件下总hinge不增、范数不减。不要提前公布验证分数。训练0/1错误、SV数和验证指标不具备同样单调保证。');
table(s,[['设计项','安排与理由'],['改变','linear C=.01、.1、1、10、100'],['固定','训练、scaler、kernel与验证记录'],['并列观察','宽度、hinge、训练错误、SV数、验证表现']],[250,880],{height:315,size:28});
bottom(s,'需要解释：代价权衡如何变化？验证表现为什么不必同步提高？');
}
// 14
{
const s=slide('Kernel：用相似度表达更丰富的边界','核心概念 5','Kernel给出映射空间内积，避免显式展开全部坐标。核SVM f(x)=ΣαᵢyᵢK(xᵢ,x)+b，非零α对应SV。');
table(s,[['核函数','定义','表达方式'],['Linear','K(z,u)=zᵀu','原输入的线性关系'],['Polynomial','(gamma·zᵀu+coef0)^degree','包含特征组合'],['RBF','exp(−gamma ||z−u||²)','距离衰减的局部相似度']],[240,565,325],{height:315,size:25});
bottom(s,'Kernel等价于某个特征空间的内积，无需显式构造全部映射坐标。');
}
// 15
{
const s=slide('RBF 的 gamma 与局部范围','核心概念 6');
const xs=Array.from({length:61},(_,i)=>3*i/60);
scatter(s,[.1,1,10].map((g,i)=>curve('gamma = '+g,xs,xs.map(x=>Math.exp(-g*x*x)),[teal,blue,orange][i])),
 {xTitle:'Distance ||z-u||',yTitle:'RBF similarity',xmin:0,xmax:3,ymin:0,ymax:1.05});
txt(s,'gamma较大',855,220,350,55,32,teal,true);
txt(s,'相似度随距离\n衰减更快，\n单点影响更局部。',855,290,345,150,29);
bottom(s,'C改变违例的代价；gamma改变按距离定义的相似度范围。');
}
// 16
{
const s=slide('实验E：先看切片，再看联合网格','核函数与参数','网格C=.1,1,10,100，gamma=.01,.1,1,10。Polynomial只展示degree2、coef0=1、gamma=.1、C1一个配置。');
table(s,[['对照','固定','改变','目的'],['第一组','RBF，C=1','gamma','理解局部范围'],['第二组','RBF，gamma=10','C','理解违例代价'],['概念对照','C=1与同一数据','linear / poly / RBF','识别表达能力']],[240,300,310,280],{height:325,size:26});
bottom(s,'观察边界与训练/验证差距；RBF的分数轮廓不是原平面的等距线。');
}
// 17
{
const s=slide('实验F：同样信息，改变单位','尺度与距离','x1乘100后距离平方中对应分量乘10000。分别在训练集拟合scaler抵消该正比例变换。此实验考察不变性，不是各流程最佳性能比较。');
table(s,[['流程','原单位','x₁乘100'],['无标准化','RBF C=1，gamma=.1','相同参数'],['训练标准化','RBF C=1，gamma=.1','相同参数']],[350,390,390],{height:250,size:28});
txt(s,'对照目的',77,500,230,55,31,teal,true);
txt(s,'不增加任何信息，只改变数值坐标，检验距离的尺度依赖。',320,500,875,90,29);
bottom(s,'观察换单位前后的最大分数差，预测哪一对应该接近不变。');
}
// 18
{
const s=slide('验证指标分别回答什么？','评价概念');
rows(s,[['Sensitivity','AB中正确识别的比例，TP/(TP+FN)。'],['Specificity','NO中正确识别的比例，TN/(TN+FP)。'],['Balanced accuracy','上述两种比例的平均，避免多数类别掩盖另一类。'],['ROC-AUC','基于decision score排序的区分，不要求概率。']],{gap:92,labelWidth:355,size:28});
bottom(s,'训练hinge衡量拟合目标，验证指标衡量保留记录表现，两者职责不同。');
}
// 19
{
const s=slide('配置记录与锁定测试','保留集流程','教师已为可行性预跑测试。本课演示保留集协议，不宣称全新独立科研确认。测试仍只在原186条拟合，保持条件一致，不把验证并入训练。');
table(s,[['阶段','安排'],['验证选择','两个家族分别按balanced accuracy选配置'],['平分规则','较小C，再较小gamma'],['配置记录','输入、预处理、参数与待解释问题'],['测试评价','记录完成后打开标签，不追加搜索']],[300,830],{height:360,size:28});
bottom(s,'测试只说明有限同源留出表现，外部医院仍需独立数据。');
}
// 20
{
const s=slide('扩展G：冻结模型后加入输入扰动','稳定性实验','可选，在测试前进行。按训练SD定义独立高斯噪声，seed9，非零强度各重复100次。重复波动不是人群抽样置信区间。');
rows(s,[['干预','向验证特征加训练SD的5%、10%、20%高斯噪声。'],['保持不变','标签、已拟合模型、scaler与参数。'],['观察','预测翻转率，以及验证表现的变化。'],['解释范围','仅限此人工噪声假设，不能替代真实仪器误差研究。']],{gap:94,labelWidth:260,size:28});
}
// 21
{
const s=slide('SVM 的优势、限制与使用条件','方法选择');
table(s,[['机制带来的优势','需要核对的条件'],['最大间隔给出明确几何目标','特征表示与尺度是否合理？'],['C允许在重叠数据上作权衡','标签噪声与验证证据是否充分？'],['Kernel表达非线性关系','相似度、参数与计算成本是否适合？'],['支持向量描述当前解的约束点','能否满足解释需求？概率是否另需校准？']],[560,570],{height:360,size:26});
bottom(s,'方法选择需要任务、数据与验证条件，单一分数不足以替代这些理由。');
}
// 22
{
const s=slide('实验产出与个人解释','学生任务','不提供结果答案。学生引用两个受控实验，解释机制、优势、局限和适用条件。课件配合工作单与Notebook。');
rows(s,[['几何解释','一项手算：分数、距离与margin的区别。'],['实验解释','两项受控对照：改变什么、固定什么、为什么。'],['方法解释','用C与kernel机制说明选择某种设置需要哪些条件。'],['结果边界','区分当前拟合、同源泛化线索与外部应用证据。']],{gap:94,labelWidth:260,size:28});
bottom(s,'资料：student-worksheet.md、svm-lab.ipynb、data/README.md');
}

const candidate=build+'/candidate.pptx';
await (await PresentationFile.exportPptx(deck)).save(candidate);
for(const [i,s] of deck.slides.items.entries()){
  const png=await deck.export({slide:s,format:'png',scale:1.25});
  await fs.writeFile(build+`/slide-${String(i+1).padStart(2,'0')}.png`,new Uint8Array(await png.arrayBuffer()));
}
const stamp=Date.now(),finalPath=build+'/final/svm-pbl-intro-'+stamp+'.pptx';
const validation=await finalizePresentation({workspaceDir:repo,candidatePath:candidate,finalPath,
  pythonExecutable:runtime+'/python/python.exe',
  integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
  layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:22,requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:chartOwners,
  materializeLiteralChartWorkbooks:true,
  fontPolicy:{basis:'design',families:[font]},verifyArtifactToolImport:true,
  receiptPath:build+'/validation-'+stamp+'.json'});
console.log(JSON.stringify(validation));
await fs.copyFile(finalPath,base+'/slides/svm-pbl-intro.pptx');
console.log('Created 22 slides, '+chartOwners.length+' editable charts, '+tableOwners.length+' editable tables.');
