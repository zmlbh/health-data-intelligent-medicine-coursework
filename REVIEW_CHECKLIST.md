# 仓库验收清单

| 维度 | 当前实现 | 状态 |
| --- | --- | --- |
| 可复现 | `python tools/audit_repository.py` 可生成 `outputs/repository-audit.csv`；各课入口见 `REPRODUCIBILITY.md` | 达标，逐课完整重跑仍待完成 |
| 可追溯 | `EVIDENCE_MAP.md` 连接最终作业、数据说明、代码和输出 | 达标 |
| 可审阅 | 使用统一课次目录；`.gitignore` 排除环境、缓存、密钥类文件和临时目录 | 达标 |
| 版本化 | 至少 3 个 commit 分别记录初始整理、证据链说明和自动验收 | 达标 |
| 边界诚实 | `LIMITATIONS.md` 说明未提交课次、AI 对话缺失、复现范围和结论边界 | 达标 |

建议提交前再次执行：

```bash
python tools/audit_repository.py
git status
git log --oneline -3
```
