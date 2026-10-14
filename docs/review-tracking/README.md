# LIBERO-Pro2.0 多轮审核记录

## 快照信息

- 仓库：`D:\LIBERO-PRO`
- 当前维护分支：`main`；以下保留原实验分支的历史审阅记录。
- 模板确认时的基线 HEAD：`2c255a89f650d9df437b0d0b94d7c41c56c474ed`
- 发布 manifest：`assets/task_manifest.json`
- 发布任务总数：1706
- 默认审核种子：143
- 默认 init state：0
- 本目录保存已确认的记录格式；历史审核结果需从原始证据导入，不得推测或补写。

## 审核单元

每条记录使用以下唯一键：

```text
suite/task_id/case_id/seed/init_state
```

示例：

```text
libero_10/task2/S04/seed143/init0
```

seed 或 init state 不同，应建立不同记录，不得合并累计。

## 必须分开的三个结论

1. **策略结果**：`SUCCESS`、`FAILURE`、`INCOMPLETE`、`ENV_CREATE_FAILED`。
2. **扰动触发**：`TRIGGERED`、`NOT_TRIGGERED`、`NOT_APPLICABLE`。
3. **审核判定**：`PASS`、`ISSUE`、`PENDING`、`N/A`。

策略失败不一定表示扰动有问题。例如扰动按设计生效并使策略失败，审核判定仍可为 `PASS`。动态扰动没有触发时，不能记为审核 `PASS`。

## 三次无问题规则

同一审核键满足以下条件时，连续无问题次数加 1：

- 环境成功创建，视频或等价证据完整；
- 动态扰动已触发，静态扰动填 `NOT_APPLICABLE`；
- 扰动强度和行为符合该 case 的要求；
- 未出现穿模、悬空、路径封死或场景崩坏；
- 审核判定为 `PASS`；
- 本轮具有独立的审核轮次编号和证据，重复引用同一视频不能重复计数。

连续达到 3 次后，状态改为 `STABLE_3_NO_RETEST`，不进入后续常规复测队列。

以下情况会把状态改为 `INVALIDATED_RETEST`，连续次数归零：

- 该任务 BDDL 或其 manifest 哈希发生变化；
- 对应 case 的 Runtime 行为发生变化；
- 该任务使用的资产发生变化；
- seed、init state 或评测协议发生变化；
- 收到与该审核键对应的新问题反馈。

与该任务无关的代码或其他任务修改，不应让稳定记录失效。

## 状态值

| 状态 | 含义 | 是否进入复测队列 |
|---|---|---|
| `PENDING` | 尚未完成首轮审核 | 是 |
| `RETEST` | 连续无问题次数为 1 或 2 | 是 |
| `ISSUE_OPEN` | 存在尚未解决或待验证的问题 | 是 |
| `STABLE_3_NO_RETEST` | 连续三轮无问题 | 否 |
| `INVALIDATED_RETEST` | 曾稳定，但相关实现已变化 | 是 |
| `N/A` | manifest 未发布或确认不适用 | 否 |

## 文件分工

| 文件 | manifest 条目数 |
|---|---:|
| `libero_10.md` | 429 |
| `libero_goal.md` | 417 |
| `libero_object.md` | 430 |
| `libero_spatial.md` | 430 |

每个 suite 文件包含：基础任务索引、审核总表、逐轮审核日志、状态失效记录和待复测队列。正式导入时，应从 manifest 展开每个已发布审核键，再依据原始审核文件、视频和提交记录写入结果。

`libero_10` 的人工审核按负责人拆分为：[`task0-task4`](libero_10_task0_4.md) 与 [`task5-task9`](libero_10_task5_9.md)。

## 2026-09-06 已上传审核进展

本表只汇总已经上传到本目录、且具有可追溯证据的审核结果。尚未上传的轮次不标记、不推测，也不据此改写复测状态。

| Suite | 发布称谓 | 本轮进展 | 仓库导入状态 | 后续动作 |
|---|---|---|---|---|
| `libero_10` | LIBERO-Long | task5-task9 已完成 R005 定向复审 | R005（0906rollout）已合并至 [`task5-task9 主记录`](libero_10_task5_9.md)；76 条通过，`task8/D06` 两条存疑 | `task8/D06` 后续舍弃、不再 rollout；其余项目全部通过，无 R006 重跑项 |
| `libero_goal` | LIBERO-Goal | 当前已上传至 R003 | R001-R003 均保留在 [`libero_goal.md`](libero_goal.md) | 按当前文件中的复测队列继续；未上传轮次不写入本表 |
| `libero_object` | LIBERO-Object | 已完成 R004 定向复审 | R004 的 200 条结果已合并至 [`libero_object.md`](libero_object.md) | 根据 R004 的 57 条存疑记录安排下一轮可观察性修复与复测 |
| `libero_spatial` | LIBERO-Spatial | 已完成 R004 定向复审 | R004 结果和精确 rollout 清单已合并至 [`libero_spatial.md`](libero_spatial.md) | 依据主记录中的 R004 rollout 清单与当前复测队列继续处理 |

> 这里的 LIBERO-Long 对应仓库中的 `libero_10` suite；不是额外新增的第五个 suite。

## 已确认规则

- [x] 以连续三轮审核 `PASS`，而不是三次策略成功，作为免复测条件。
- [x] 动态扰动 `NOT_TRIGGERED` 不计入连续无问题。
- [x] 只让相关实现变化的任务失效，不因无关提交全量重测。
- [x] 审核键固定包含 seed 和 init state。
- [x] 历史结果只能从可追溯证据导入。
