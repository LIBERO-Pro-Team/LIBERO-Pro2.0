# 分组式多 seed 评测

## 目标与边界

分组评测在现有模型无关 `RunScheduler` 上增加任务选择与计划展开能力，不修改服务协议、模型 adapter
契约或 LIBERO 任务。服务端 `/v1/tasks` 是有效组合的唯一来源，因此不会重新构造不存在的组合。

支持的评测组：

- `base`：所有已发布 BASE 任务。
- `static`：所有已发布静态扰动。
- `dynamic`：所有已发布动态扰动。
- `all`：所有已发布组合。

可以继续用 `--suite` 和 `--case` 取交集。例如 `--group dynamic --suite libero_goal` 只选择
`libero_goal` 中实际发布的动态组合；`--case D07` 选择所有发布 D07 的 suite。

## 生成和提交计划

先预览计划，不提交环境任务：

```bash
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  plan \
  --group dynamic \
  --suite libero_goal \
  --seeds 42 43 44 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/goal_dynamic_plan
```

确认 rollout 数量后提交：

```bash
export LIBERO_REMOTE_API_KEY="ACCOUNT_API_KEY"
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  submit \
  --group dynamic \
  --suite libero_goal \
  --seeds 42 43 44 \
  --init-state-ids 0 1 2 \
  --control-mode relative \
  --output-dir results/goal_dynamic
```

也可用连续 seed 简写：

```bash
--seed 42 --num-seeds 5
```

默认情况下，seed 与 init state 一一对应；一侧只有一个值时广播：

```text
seed 42 -> init state 0
seed 43 -> init state 1
seed 44 -> init state 2
```

显式增加 `--matrix` 后才生成 seed 与 init state 的笛卡尔积。

`submit` 只把整个计划提交给模型无关 scheduler。已经在线的通用 Agent runner 可以领取任务；增加
`--wait` 时，提交命令会等待外部 runner 完成并自动导出结果。模型加载方式不属于该命令。

## 在现有 Agent runner 中一键执行

已经构造 `AgentAdapter` 的用户代码可以直接复用同一计划：

```python
from pathlib import Path

from libero_remote import RemoteRunClient
from libero_remote.benchmark import build_benchmark_plan, run_grouped_benchmark

with RemoteRunClient(server_url, api_key=api_key) as client:
    plan = build_benchmark_plan(
        client.get_task_catalog(),
        group="static",
        suites=["libero_spatial"],
        seeds=[42, 43, 44],
        init_state_ids=[0, 1, 2],
        control_mode="relative",
    )
    result = run_grouped_benchmark(
        client,
        plan,
        adapter,
        runner_id="host-a-gpu-0",
        output_dir=Path("results/spatial_static"),
    )
```

该函数只依赖仓库现有 `AgentAdapter`，不判断模型名称。

## 断点续跑与导出

Run 和 episode 状态由服务端 SQLite 持久化。进程中断后，使用原计划和已有 `run_id` 再次调用
`run_grouped_benchmark(..., run_id=...)`，会先逐项校验 episode spec，然后只领取剩余任务。

也可以只导出已有 run：

```bash
python scripts/run_grouped_eval.py \
  --base-url http://SERVER:8000 \
  export \
  --run-id run_xxx \
  --output-dir results/recovered_run
```

输出目录包含：

```text
plan.json          任务选择、manifest 身份和完整 episode 计划
submission.json    服务端 run ID
run.json           当前 run 状态
episodes.jsonl     逐 episode 权威结果
episodes.csv       便于表格分析的扁平结果
failures.jsonl     基础设施失败项
summary.json       总体以及 suite/variant/group/seed 分组汇总
```

成功率只以服务端标记为 `completed` 的策略 episode 为分母；基础设施 `failed` 单独统计，不会被当作
模型正常失败混入成功率。
