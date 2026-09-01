# libero_goal 多轮审核记录

## Suite 信息

- manifest 条目数：417
- 基础任务数：10
- 默认 seed/init：`143/0`
- 当前状态：模板已确认，尚未导入历史审核结果。

## 基础任务索引

| Task ID | Task Name |
|---:|---|
| 0 | `open_the_middle_drawer_of_the_cabinet` |
| 1 | `put_the_bowl_on_the_stove` |
| 2 | `put_the_wine_bottle_on_top_of_the_cabinet` |
| 3 | `open_the_top_drawer_and_put_the_bowl_inside` |
| 4 | `put_the_bowl_on_top_of_the_cabinet` |
| 5 | `push_the_plate_to_the_front_of_the_stove` |
| 6 | `put_the_cream_cheese_in_the_bowl` |
| 7 | `turn_on_the_stove` |
| 8 | `put_the_bowl_on_the_plate` |
| 9 | `put_the_wine_bottle_on_the_rack` |

## 审核总表

正式导入时从 manifest 展开本 suite 的全部 417 条记录。三轮列只记录审核判定，策略结果和触发状态单独保留。

| Review Key | Case | R1 | R2 | R3 | 连续 PASS | 当前状态 | 最新策略结果 | 最新触发状态 | 最后审核 Commit | 证据 | 未解决问题 |
|---|---|---|---|---|---:|---|---|---|---|---|---|
| `libero_goal/task<id>/<case>/seed143/init0` | `<case>` | `-` | `-` | `-` | 0 | `PENDING` | `-` | `-` | `-` | `-` | `-` |

## 逐轮审核日志

| Round ID | 日期 | 审核人 | Review Key | Commit | BDDL SHA-256 | 策略结果 | 触发状态 | 审核判定 | 问题类型 | 问题说明 | 视频/证据 | 修复 Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `R001` | `YYYY-MM-DD` | `<name>` | `libero_goal/task<id>/<case>/seed143/init0` | `<sha>` | `<sha256>` | `<SUCCESS/FAILURE/...>` | `<TRIGGERED/...>` | `<PASS/ISSUE>` | `<none/type>` | `<details>` | `<path/url>` | `<sha or ->` |

## 状态失效记录

| 日期 | Review Key | 原状态 | 失效原因 | 相关文件或 Commit | 新状态 |
|---|---|---|---|---|---|
| `YYYY-MM-DD` | `<key>` | `STABLE_3_NO_RETEST` | `<BDDL/Runtime/asset/feedback change>` | `<path/sha>` | `INVALIDATED_RETEST` |

## 待复测队列

| 优先级 | Review Key | 当前连续 PASS | 复测原因 | 目标轮次 | 负责人 |
|---:|---|---:|---|---|---|
| `P0/P1/P2` | `<key>` | 0 | `<reason>` | `<Rxxx>` | `<name>` |
