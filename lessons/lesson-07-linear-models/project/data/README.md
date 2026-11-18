# 实验数据

`heart.csv` 含 270 条教学记录，120 条 `heart_disease_present=1`，150 条为 0。输入保留 13 个心脏病变量：age、sex、cp、trestbps、chol、fbs、restecg、thalach、exang、oldpeak、slope、ca、thal；`record_id`、`site`、`num` 和目标用于审计，不进入模型。

数据整理自项目已有的 UCI 多站点心脏病字段，按 `random_state=2026` 分层抽取并打乱，用于复现实验协议。它不是新的独立临床队列。连续变量、二元变量、名义变量和有序/计数变量混合存在，缺失值在这份教学文件中已处理为无缺失。

主协议：development/test=80%/20%，开发集内重复分层交叉验证；连续变量在训练折内标准化，分类变量在训练折内 one-hot。测试标签只能在方案冻结后使用。
