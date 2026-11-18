# 第 8 讲 线性模型、LDA 与 Logistic Regression

本讲以心脏病二分类数据为案例，比较 logistic 与 LDA 的建模对象、概率来源、假设、优化/估计目标和参数量，再分析错误代价、系数稳定性和因果边界。

课程文件：`student-worksheet.md`、`teacher-reference.md`、`experiment-design.md`、`notebooks/linear-models-lab.ipynb`、`data/heart.csv`、`slides/linear-models-pbl-intro.pptx`。

运行：在本目录安装 `requirements.txt` 后启动 Notebook。测试默认关闭；只有提交冻结方案后由教师打开。

数据由项目已有的 UCI 多站点心脏病原始字段整理为 270 条教学记录，类别固定为 120 阳性、150 阴性。数据说明、字段和限制见 `data/README.md`。数据适合教学比较，不能解释为独立临床队列。
