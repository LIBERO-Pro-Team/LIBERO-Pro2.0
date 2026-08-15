# 测试指南

## 分组式评测

运行分组计划、CLI 和 scheduler 回归测试：

```bash
python -m pytest -q \
  tests/test_grouped_benchmark.py \
  tests/test_grouped_eval_script.py \
  tests/test_scheduled_runner.py \
  tests/test_run_scheduler_roundtrip.py
```

Pi0、xVLA 和共用 MP4 writer 的录像回归测试：

```bash
python -m pytest -q \
  tests/test_agent_runner.py \
  tests/test_pi0_runner.py \
  tests/test_xvla_runner.py \
  tests/test_video_writer.py
```

重点覆盖：

- base/static/dynamic/all 与 suite/case 交集筛选。
- 只使用任务目录实际发布的组合。
- seed/init-state 配对、广播和显式矩阵展开。
- 非法或重复参数在提交前失败。
- 一个 adapter 实例连续执行完整计划。
- 已有 run 的 spec 校验与断点恢复。
- 总体以及 suite/variant/group/seed 汇总。
- JSON、JSONL 和 CSV 结果导出。

完整测试要求 Python 3.11 或 3.12，并安装 `.[server,dev]`。Python 3.8 环境无法导入测试套件使用的
标准库 `tomllib`。
