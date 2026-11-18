# Codex 使用记录摘要

以下内容来自截至 2026-11-18 可访问的 Codex 历史，已删除私人绝对路径和逐字聊天内容。

## 按顶会风格撰写作业

- 任务：参考 7 篇 Nature Medicine 论文的图文组织，将线性模型作业整理为研究论文结构。
- Codex 协助：核对不同版本实验结果，区分 bootstrap 中位数与原始测试点估计；重组摘要、引言、结果、讨论和方法；建立 Word/PDF 构建脚本。
- 用户核查：指出 Markdown 不能作为正式交付，要求 Word/PDF、图表、图注和参考文献。
- 对应产出：`project/论文交付/线性模型比较研究.docx`、`project/论文交付/线性模型比较研究.pdf`、`project/scripts/build_article.py`。

## 评估作业的 Nature 投稿可行性

- 任务：继续改进图表、分页、引文顺序和结论边界。
- Codex 协助：新增区分能力与决策效用联合图；统一 `[1]` 式引用；删除质量不足的流程图；修正图号和页眉；逐页检查排版。
- 边界：历史记录明确指出这是论文形式的课程作业，真正投稿仍需新增研究贡献、外部验证和目标会议模板。
- 对应代码：`project/scripts/build_chinese_research_submission.py`、`project/scripts/make_chinese_submission_figures.py`。

记录类型：脱敏任务摘要，不是完整聊天导出。
