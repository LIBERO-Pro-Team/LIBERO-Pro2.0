# 测试指南

## 分组式评测

运行分组计划、CLI 和 scheduler 回归测试：

```bash
python -m pytest -q \
  tests/test_grouped_benchmark.py \
  tests/test_grouped_eval_script.py \
  tests/test_consolidated_catalogue.py \
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
- 版本化 train/test 划分按 `suite + base_task_id` 隔离，并保留任务下全部扰动。
- 只使用任务目录实际发布的组合。
- seed/init-state 配对、广播和显式矩阵展开。
- 非法或重复参数在提交前失败。
- 一个 adapter 实例连续执行完整计划。
- 已有 run 的 spec 校验与断点恢复。
- 总体以及 suite/variant/group/seed 汇总。
- JSON、JSONL 和 CSV 结果导出。

完整测试要求 Python 3.11 或 3.12，并安装 `.[server,dev]`。Python 3.8 环境无法导入测试套件使用的
标准库 `tomllib`。

## 合并后的任务与运行时验证

`tests/test_consolidated_catalogue.py` 校验发布清单哈希、42类扰动的 split 元数据、
1349/339训练测试边界，以及计划中各suite的默认步数上限。
维护用反馈调参测试使用临时TSV测试数据，不依赖个人桌面文件。

```bash
python -m pytest -q tests
python -m mypy libero_remote --python-version 3.12
```

完整仿真测试另需已安装 LIBERO 的 robosuite、MuJoCo 等运行时依赖：

```bash
python -m pytest -q simulator-source/tests
```

历史运行时单元测试使用 `simulator-source/tests/fixtures/runtime_bddls/` 中固定的
BDDL输入，来源见 `SOURCE.json`；这些夹具不进入发布任务清单。

Windows部署脚本测试需要WSL；真实GPU/EGL和模型rollout仍须在目标服务器另行验收。
