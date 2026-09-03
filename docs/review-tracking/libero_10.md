# libero_10 多轮审核记录

## Suite 信息

- manifest 条目数：429
- 基础任务数：10
- 默认 seed/init：`143/0`
- 当前状态：历史审核已按负责人拆分导入：[`task0-task4`](libero_10_task0_4.md)、[`task5-task9`](libero_10_task5_9.md)。task5-task9 的 R004（0902rollout）已合并在其主记录内。

## 基础任务索引

| Task ID | Task Name |
|---:|---|
| 0 | `LIVING_ROOM_SCENE2_put_both_the_alphabet_soup_and_the_tomato_sauce_in_the_basket` |
| 1 | `LIVING_ROOM_SCENE2_put_both_the_cream_cheese_box_and_the_butter_in_the_basket` |
| 2 | `KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it` |
| 3 | `KITCHEN_SCENE4_put_the_black_bowl_in_the_bottom_drawer_of_the_cabinet_and_close_it` |
| 4 | `LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate` |
| 5 | `STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy` |
| 6 | `LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate` |
| 7 | `LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket` |
| 8 | `KITCHEN_SCENE8_put_both_moka_pots_on_the_stove` |
| 9 | `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it` |

## 审核总表

正式导入时从 manifest 展开本 suite 的全部 429 条记录。三轮列只记录审核判定，策略结果和触发状态单独保留。

| Review Key | Case | R1 | R2 | R3 | 连续 PASS | 当前状态 | 最新策略结果 | 最新触发状态 | 最后审核 Commit | 证据 | 未解决问题 |
|---|---|---|---|---|---:|---|---|---|---|---|---|
| `libero_10/task<id>/<case>/seed143/init0` | `<case>` | `-` | `-` | `-` | 0 | `PENDING` | `-` | `-` | `-` | `-` | `-` |

## 逐轮审核日志

| Round ID | 日期 | 审核人 | Review Key | Commit | BDDL SHA-256 | 策略结果 | 触发状态 | 审核判定 | 问题类型 | 问题说明 | 视频/证据 | 修复 Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `R001` | `YYYY-MM-DD` | `<name>` | `libero_10/task<id>/<case>/seed143/init0` | `<sha>` | `<sha256>` | `<SUCCESS/FAILURE/...>` | `<TRIGGERED/...>` | `<PASS/ISSUE>` | `<none/type>` | `<details>` | `<path/url>` | `<sha or ->` |

## 状态失效记录

| 日期 | Review Key | 原状态 | 失效原因 | 相关文件或 Commit | 新状态 |
|---|---|---|---|---|---|
| `YYYY-MM-DD` | `<key>` | `STABLE_3_NO_RETEST` | `<BDDL/Runtime/asset/feedback change>` | `<path/sha>` | `INVALIDATED_RETEST` |

## 待复测队列

| 优先级 | Review Key | 当前连续 PASS | 复测原因 | 目标轮次 | 负责人 |
|---:|---|---:|---|---|---|
| `P0/P1/P2` | `<key>` | 0 | `<reason>` | `<Rxxx>` | `<name>` |
