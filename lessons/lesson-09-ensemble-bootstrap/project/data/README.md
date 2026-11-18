# 第 10 讲数据说明

本课使用 sklearn 内置的 Breast Cancer Wisconsin (Diagnostic) 数据集（WDBC）。每一行是一个乳腺肿块细针穿刺图像提取的细胞核特征记录，共 569 条记录、30 个连续特征。课程保留 `sample_id` 仅用于追踪，不把它作为模型输入。

原始标签为 0=malignant、1=benign；课程脚本重编码为 `malignant=1`（恶性）、`malignant=0`（良性）。本课不把标签解释为患者未来风险、疾病严重程度或因果效应。数据缺少可用的患者分组与时间字段，因此不能从本表核验患者独立性，也不支持跨医院泛化结论。

`scripts/prepare_data.py` 固定 `random_state=1010`：455 条开发数据再分为 341 条 train 和 114 条 validation，另留出 114 条 test。学生获得 train、validation 和不含标签的 locked-test-features；教师保留 test 标签和完整测量表。所有模型比较使用同一分割，测试集只在协议锁定后评价一次。

来源：UCI 数据集页面 <https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic>，DOI `10.24432/C5DW2B`；课堂离线数据来自 `sklearn.datasets.load_breast_cancer`。正式使用前请按机构课程政策核对数据署名与许可。
