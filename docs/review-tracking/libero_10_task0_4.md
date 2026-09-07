# Libero 10, Task 0~4 多轮审核记录

## Suite 信息

- manifest 条目数：430
- 基础任务数：10
- 默认 seed/init：`143/0`
- 当前状态：已按模板导入 huang 负责范围 `task0-task4` 的三轮审核结果；R004（0902rollout）与 R005（0906rollout）定向复审记录已追加在本文末尾；`task5-task9` 见 [`libero_10_task5_9.md`](libero_10_task5_9.md)。

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

正式导入时按 huang 负责范围 `task0-task4` 展开 430 条记录。三轮列只记录审核判定，策略结果和触发状态单独保留。

| Review Key | Case | R1 | R2 | R3 | 连续 PASS | 当前状态 | 最新策略结果 | 最新触发状态 | 最后审核 Commit | 证据 | 未解决问题 |
|---|---|---|---|---|---:|---|---|---|---|---|---|
| `libero_10/task0/BASE/seed142/init0` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_BASE_seed142_init0.mp4` | - |
| `libero_10/task0/BASE/seed143/init1` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_BASE_seed143_init1.mp4` | - |
| `libero_10/task0/D01/seed142/init0` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D01_seed142_init0.mp4` | - |
| `libero_10/task0/D01/seed143/init1` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D01_seed143_init1.mp4` | - |
| `libero_10/task0/D02/seed142/init0` | `D02` | `PASS` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D02_seed142_init0.mp4` | 没抓到，没有触发 |
| `libero_10/task0/D02/seed143/init1` | `D02` | `ISSUE` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D02_seed143_init1.mp4` | 没抓到，没有触发 |
| `libero_10/task0/D03/seed142/init0` | `D03` | `ISSUE` | `PENDING` | `PENDING` | 0 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_D03_seed142_init0.mp4` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 |
| `libero_10/task0/D03/seed143/init1` | `D03` | `ISSUE` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D03_seed143_init1.mp4` | 没抓到，没有触发 |
| `libero_10/task0/D04/seed142/init0` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D04_seed142_init0.mp4` | - |
| `libero_10/task0/D04/seed143/init1` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D04_seed143_init1.mp4` | - |
| `libero_10/task0/D05/seed142/init0` | `D05` | `PASS` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D05_seed142_init0.mp4` | 没抓到，没有触发 |
| `libero_10/task0/D05/seed143/init1` | `D05` | `ISSUE` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D05_seed143_init1.mp4` | 穿模 |
| `libero_10/task0/D06/seed142/init0` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D06_seed142_init0.mp4` | - |
| `libero_10/task0/D06/seed143/init1` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D06_seed143_init1.mp4` | - |
| `libero_10/task0/D07/seed142/init0` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D07_seed142_init0.mp4` | - |
| `libero_10/task0/D07/seed143/init1` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D07_seed143_init1.mp4` | - |
| `libero_10/task0/D08/seed142/init0` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D08_seed142_init0.mp4` | - |
| `libero_10/task0/D08/seed143/init1` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D08_seed143_init1.mp4` | - |
| `libero_10/task0/D09/seed142/init0` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_D09_seed142_init0.mp4` | - |
| `libero_10/task0/D09/seed143/init1` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D09_seed143_init1.mp4` | - |
| `libero_10/task0/D10/seed142/init0` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D10_seed142_init0.mp4` | - |
| `libero_10/task0/D10/seed143/init1` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D10_seed143_init1.mp4` | - |
| `libero_10/task0/D11/seed142/init0` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D11_seed142_init0.mp4` | - |
| `libero_10/task0/D11/seed143/init1` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D11_seed143_init1.mp4` | - |
| `libero_10/task0/D12/seed142/init0` | `D12` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_D12_seed142_init0.mp4` | 这个肉眼看不出来 |
| `libero_10/task0/D12/seed143/init1` | `D12` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D12_seed143_init1.mp4` | 这个肉眼看不出来 |
| `libero_10/task0/D13/seed142/init0` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D13_seed142_init0.mp4` | - |
| `libero_10/task0/D13/seed143/init1` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D13_seed143_init1.mp4` | - |
| `libero_10/task0/D14/seed142/init0` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D14_seed142_init0.mp4` | - |
| `libero_10/task0/D14/seed143/init1` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D14_seed143_init1.mp4` | - |
| `libero_10/task0/D15/seed142/init0` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D15_seed142_init0.mp4` | - |
| `libero_10/task0/D15/seed143/init1` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D15_seed143_init1.mp4` | - |
| `libero_10/task0/D16/seed142/init0` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_D16_seed142_init0.mp4` | - |
| `libero_10/task0/D16/seed143/init1` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D16_seed143_init1.mp4` | - |
| `libero_10/task0/D17/seed142/init0` | `D17` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D17_seed142_init0.mp4` | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 |
| `libero_10/task0/D17/seed143/init1` | `D17` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D17_seed143_init1.mp4` | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 |
| `libero_10/task0/D18/seed142/init0` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D18_seed142_init0.mp4` | - |
| `libero_10/task0/D18/seed143/init1` | `D18` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D18_seed143_init1.mp4` | 第一个物体没抓到，然后第二个物体抓到了，但是没有触发扰动。 |
| `libero_10/task0/D20/seed142/init0` | `D20` | `-` | `PENDING` | `PENDING` | 0 | `ISSUE_OPEN` | `FAILURE` | `PENDING` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D20_seed142_init0.mp4` | 看不太出来 |
| `libero_10/task0/D20/seed143/init1` | `D20` | `-` | `PENDING` | `PENDING` | 0 | `ISSUE_OPEN` | `FAILURE` | `PENDING` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D20_seed143_init1.mp4` | 看不太出来 |
| `libero_10/task0/D21/seed142/init0` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D21_seed142_init0.mp4` | - |
| `libero_10/task0/D21/seed143/init1` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_D21_seed143_init1.mp4` | - |
| `libero_10/task0/S01/seed142/init0` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S01_seed142_init0.mp4` | - |
| `libero_10/task0/S01/seed143/init1` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S01_seed143_init1.mp4` | - |
| `libero_10/task0/S02/seed142/init0` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S02_seed142_init0.mp4` | - |
| `libero_10/task0/S02/seed143/init1` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S02_seed143_init1.mp4` | - |
| `libero_10/task0/S03/seed142/init0` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S03_seed142_init0.mp4` | - |
| `libero_10/task0/S03/seed143/init1` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S03_seed143_init1.mp4` | - |
| `libero_10/task0/S04/seed142/init0` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S04_seed142_init0.mp4` | - |
| `libero_10/task0/S04/seed143/init1` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S04_seed143_init1.mp4` | - |
| `libero_10/task0/S05/seed142/init0` | `S05` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S05_seed142_init0.mp4` | 限制不是很明显 |
| `libero_10/task0/S05/seed143/init1` | `S05` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S05_seed143_init1.mp4` | 限制不是很明显 |
| `libero_10/task0/S06/seed142/init0` | `S06` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S06_seed142_init0.mp4` | 替换的物品难度过大了 大于夹爪的最大限度了 |
| `libero_10/task0/S06/seed143/init1` | `S06` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S06_seed143_init1.mp4` | 替换的物品难度过大了 大于夹爪的最大限度了 |
| `libero_10/task0/S07/seed142/init0` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S07_seed142_init0.mp4` | - |
| `libero_10/task0/S07/seed143/init1` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S07_seed143_init1.mp4` | - |
| `libero_10/task0/S08/seed142/init0` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S08_seed142_init0.mp4` | - |
| `libero_10/task0/S08/seed143/init1` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S08_seed143_init1.mp4` | - |
| `libero_10/task0/S09/seed142/init0` | `S09` | `ISSUE` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S09_seed142_init0.mp4` | 成功了，但是判定失败了 |
| `libero_10/task0/S09/seed143/init1` | `S09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S09_seed143_init1.mp4` | - |
| `libero_10/task0/S10/seed142/init0` | `S10` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S10_seed142_init0.mp4` | 未增加无关杂物 |
| `libero_10/task0/S10/seed143/init1` | `S10` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S10_seed143_init1.mp4` | 未增加无关杂物 |
| `libero_10/task0/S11/seed142/init0` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S11_seed142_init0.mp4` | - |
| `libero_10/task0/S11/seed143/init1` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S11_seed143_init1.mp4` | - |
| `libero_10/task0/S12/seed142/init0` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S12_seed142_init0.mp4` | - |
| `libero_10/task0/S12/seed143/init1` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S12_seed143_init1.mp4` | - |
| `libero_10/task0/S13/seed142/init0` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S13_seed142_init0.mp4` | - |
| `libero_10/task0/S13/seed143/init1` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S13_seed143_init1.mp4` | - |
| `libero_10/task0/S14/seed142/init0` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S14_seed142_init0.mp4` | - |
| `libero_10/task0/S14/seed143/init1` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S14_seed143_init1.mp4` | - |
| `libero_10/task0/S15/seed142/init0` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S15_seed142_init0.mp4` | - |
| `libero_10/task0/S15/seed143/init1` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S15_seed143_init1.mp4` | - |
| `libero_10/task0/S16/seed142/init0` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S16_seed142_init0.mp4` | - |
| `libero_10/task0/S16/seed143/init1` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S16_seed143_init1.mp4` | - |
| `libero_10/task0/S17/seed142/init0` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S17_seed142_init0.mp4` | - |
| `libero_10/task0/S17/seed143/init1` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S17_seed143_init1.mp4` | - |
| `libero_10/task0/S18/seed142/init0` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S18_seed142_init0.mp4` | - |
| `libero_10/task0/S18/seed143/init1` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S18_seed143_init1.mp4` | - |
| `libero_10/task0/S19/seed142/init0` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S19_seed142_init0.mp4` | - |
| `libero_10/task0/S19/seed143/init1` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S19_seed143_init1.mp4` | - |
| `libero_10/task0/S20/seed142/init0` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S20_seed142_init0.mp4` | - |
| `libero_10/task0/S20/seed143/init1` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S20_seed143_init1.mp4` | - |
| `libero_10/task0/S21/seed142/init0` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S21_seed142_init0.mp4` | - |
| `libero_10/task0/S21/seed143/init1` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task0_S21_seed143_init1.mp4` | - |
| `libero_10/task0/S22/seed142/init0` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S22_seed142_init0.mp4` | - |
| `libero_10/task0/S22/seed143/init1` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task0_S22_seed143_init1.mp4` | - |
| `libero_10/task1/BASE/seed142/init0` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_BASE_seed142_init0.mp4` | - |
| `libero_10/task1/BASE/seed143/init1` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_BASE_seed143_init1.mp4` | - |
| `libero_10/task1/D01/seed142/init0` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D01_seed142_init0.mp4` | - |
| `libero_10/task1/D01/seed143/init1` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D01_seed143_init1.mp4` | - |
| `libero_10/task1/D02/seed142/init0` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D02_seed142_init0.mp4` | - |
| `libero_10/task1/D02/seed143/init1` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D02_seed143_init1.mp4` | - |
| `libero_10/task1/D03/seed142/init0` | `D03` | `ISSUE` | `ISSUE` | `PENDING` | 0 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D03_seed142_init0.mp4` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 |
| `libero_10/task1/D03/seed143/init1` | `D03` | `ISSUE` | `ISSUE` | `PENDING` | 0 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D03_seed143_init1.mp4` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 |
| `libero_10/task1/D04/seed142/init0` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D04_seed142_init0.mp4` | - |
| `libero_10/task1/D04/seed143/init1` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D04_seed143_init1.mp4` | - |
| `libero_10/task1/D05/seed142/init0` | `D05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D05_seed142_init0.mp4` | - |
| `libero_10/task1/D05/seed143/init1` | `D05` | `PASS` | `PASS` | `PENDING` | 0 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D05_seed143_init1.mp4` | 第二个的障碍物放置位置不太合理，没有在运输路径上面 |
| `libero_10/task1/D06/seed142/init0` | `D06` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D06_seed142_init0.mp4` | 没有触发 |
| `libero_10/task1/D06/seed143/init1` | `D06` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D06_seed143_init1.mp4` | 没有触发 |
| `libero_10/task1/D07/seed142/init0` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D07_seed142_init0.mp4` | - |
| `libero_10/task1/D07/seed143/init1` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D07_seed143_init1.mp4` | - |
| `libero_10/task1/D08/seed142/init0` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D08_seed142_init0.mp4` | - |
| `libero_10/task1/D08/seed143/init1` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D08_seed143_init1.mp4` | - |
| `libero_10/task1/D09/seed142/init0` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D09_seed142_init0.mp4` | - |
| `libero_10/task1/D09/seed143/init1` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D09_seed143_init1.mp4` | - |
| `libero_10/task1/D10/seed142/init0` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D10_seed142_init0.mp4` | - |
| `libero_10/task1/D10/seed143/init1` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D10_seed143_init1.mp4` | - |
| `libero_10/task1/D11/seed142/init0` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D11_seed142_init0.mp4` | - |
| `libero_10/task1/D11/seed143/init1` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D11_seed143_init1.mp4` | - |
| `libero_10/task1/D12/seed142/init0` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D12_seed142_init0.mp4` | - |
| `libero_10/task1/D12/seed143/init1` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D12_seed143_init1.mp4` | - |
| `libero_10/task1/D13/seed142/init0` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D13_seed142_init0.mp4` | - |
| `libero_10/task1/D13/seed143/init1` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D13_seed143_init1.mp4` | - |
| `libero_10/task1/D14/seed142/init0` | `D14` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D14_seed142_init0.mp4` | 看不出来 |
| `libero_10/task1/D14/seed143/init1` | `D14` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D14_seed143_init1.mp4` | 看不出来 |
| `libero_10/task1/D15/seed142/init0` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D15_seed142_init0.mp4` | - |
| `libero_10/task1/D15/seed143/init1` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D15_seed143_init1.mp4` | - |
| `libero_10/task1/D16/seed142/init0` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_D16_seed142_init0.mp4` | - |
| `libero_10/task1/D16/seed143/init1` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D16_seed143_init1.mp4` | - |
| `libero_10/task1/D17/seed142/init0` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D17_seed142_init0.mp4` | - |
| `libero_10/task1/D17/seed143/init1` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D17_seed143_init1.mp4` | - |
| `libero_10/task1/D18/seed142/init0` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D18_seed142_init0.mp4` | - |
| `libero_10/task1/D18/seed143/init1` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D18_seed143_init1.mp4` | - |
| `libero_10/task1/D20/seed142/init0` | `D20` | `-` | `PENDING` | `PENDING` | 0 | `ISSUE_OPEN` | `FAILURE` | `PENDING` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D20_seed142_init0.mp4` | 肉眼看不出来 |
| `libero_10/task1/D20/seed143/init1` | `D20` | `-` | `PENDING` | `PENDING` | 0 | `ISSUE_OPEN` | `FAILURE` | `PENDING` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D20_seed143_init1.mp4` | 肉眼看不出来 |
| `libero_10/task1/D21/seed142/init0` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D21_seed142_init0.mp4` | - |
| `libero_10/task1/D21/seed143/init1` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_D21_seed143_init1.mp4` | - |
| `libero_10/task1/S01/seed142/init0` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S01_seed142_init0.mp4` | - |
| `libero_10/task1/S01/seed143/init1` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S01_seed143_init1.mp4` | - |
| `libero_10/task1/S02/seed142/init0` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S02_seed142_init0.mp4` | - |
| `libero_10/task1/S02/seed143/init1` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S02_seed143_init1.mp4` | - |
| `libero_10/task1/S03/seed142/init0` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S03_seed142_init0.mp4` | - |
| `libero_10/task1/S03/seed143/init1` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S03_seed143_init1.mp4` | - |
| `libero_10/task1/S04/seed142/init0` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S04_seed142_init0.mp4` | - |
| `libero_10/task1/S04/seed143/init1` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S04_seed143_init1.mp4` | - |
| `libero_10/task1/S05/seed142/init0` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S05_seed142_init0.mp4` | - |
| `libero_10/task1/S05/seed143/init1` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S05_seed143_init1.mp4` | - |
| `libero_10/task1/S06/seed142/init0` | `S06` | `PASS` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S06_seed142_init0.mp4` | 目标直接消失了 |
| `libero_10/task1/S06/seed143/init1` | `S06` | `ISSUE` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S06_seed143_init1.mp4` | 目标变大了，这不太合理，不可能抓的到 |
| `libero_10/task1/S07/seed142/init0` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S07_seed142_init0.mp4` | - |
| `libero_10/task1/S07/seed143/init1` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S07_seed143_init1.mp4` | - |
| `libero_10/task1/S08/seed142/init0` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S08_seed142_init0.mp4` | - |
| `libero_10/task1/S08/seed143/init1` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S08_seed143_init1.mp4` | - |
| `libero_10/task1/S09/seed142/init0` | `S09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S09_seed142_init0.mp4` | - |
| `libero_10/task1/S09/seed143/init1` | `S09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S09_seed143_init1.mp4` | - |
| `libero_10/task1/S10/seed142/init0` | `S10` | `PASS` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S10_seed142_init0.mp4` | 没有出现应有的杂物 |
| `libero_10/task1/S10/seed143/init1` | `S10` | `PASS` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S10_seed143_init1.mp4` | 没有出现应有的杂物 |
| `libero_10/task1/S11/seed142/init0` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S11_seed142_init0.mp4` | - |
| `libero_10/task1/S11/seed143/init1` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S11_seed143_init1.mp4` | - |
| `libero_10/task1/S12/seed142/init0` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S12_seed142_init0.mp4` | - |
| `libero_10/task1/S12/seed143/init1` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S12_seed143_init1.mp4` | - |
| `libero_10/task1/S13/seed142/init0` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S13_seed142_init0.mp4` | - |
| `libero_10/task1/S13/seed143/init1` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S13_seed143_init1.mp4` | - |
| `libero_10/task1/S14/seed142/init0` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S14_seed142_init0.mp4` | - |
| `libero_10/task1/S14/seed143/init1` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S14_seed143_init1.mp4` | - |
| `libero_10/task1/S15/seed142/init0` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S15_seed142_init0.mp4` | - |
| `libero_10/task1/S15/seed143/init1` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S15_seed143_init1.mp4` | - |
| `libero_10/task1/S16/seed142/init0` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S16_seed142_init0.mp4` | - |
| `libero_10/task1/S16/seed143/init1` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S16_seed143_init1.mp4` | - |
| `libero_10/task1/S17/seed142/init0` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S17_seed142_init0.mp4` | - |
| `libero_10/task1/S17/seed143/init1` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S17_seed143_init1.mp4` | - |
| `libero_10/task1/S18/seed142/init0` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S18_seed142_init0.mp4` | - |
| `libero_10/task1/S18/seed143/init1` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S18_seed143_init1.mp4` | - |
| `libero_10/task1/S19/seed142/init0` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S19_seed142_init0.mp4` | - |
| `libero_10/task1/S19/seed143/init1` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S19_seed143_init1.mp4` | - |
| `libero_10/task1/S20/seed142/init0` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S20_seed142_init0.mp4` | - |
| `libero_10/task1/S20/seed143/init1` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S20_seed143_init1.mp4` | - |
| `libero_10/task1/S21/seed142/init0` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S21_seed142_init0.mp4` | - |
| `libero_10/task1/S21/seed143/init1` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task1_S21_seed143_init1.mp4` | - |
| `libero_10/task1/S22/seed142/init0` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S22_seed142_init0.mp4` | - |
| `libero_10/task1/S22/seed143/init1` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task1_S22_seed143_init1.mp4` | - |
| `libero_10/task2/BASE/seed142/init0` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_BASE_seed142_init0.mp4` | - |
| `libero_10/task2/BASE/seed143/init1` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_BASE_seed143_init1.mp4` | - |
| `libero_10/task2/D01/seed142/init0` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D01_seed142_init0.mp4` | - |
| `libero_10/task2/D01/seed143/init1` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D01_seed143_init1.mp4` | - |
| `libero_10/task2/D02/seed142/init0` | `D02` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D02_seed142_init0.mp4` | 扰动没有发生 |
| `libero_10/task2/D02/seed143/init1` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D02_seed143_init1.mp4` | - |
| `libero_10/task2/D03/seed142/init0` | `D03` | `ISSUE` | `ISSUE` | `ISSUE` | 0 | `ISSUE_OPEN` | `SUCCESS` | `NOT_TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D03_seed142_init0.mp4` | 抓到物体了，但是扰动没有发生 |
| `libero_10/task2/D03/seed143/init1` | `D03` | `ISSUE` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D03_seed143_init1.mp4` | 没有触发扰动 |
| `libero_10/task2/D04/seed142/init0` | `D04` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D04_seed142_init0.mp4` | 遮挡物没什么用处 |
| `libero_10/task2/D04/seed143/init1` | `D04` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D04_seed143_init1.mp4` | 遮挡物没什么用处 |
| `libero_10/task2/D05/seed142/init0` | `D05` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D05_seed142_init0.mp4` | 没抓到，扰动没有触发 |
| `libero_10/task2/D05/seed143/init1` | `D05` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D05_seed143_init1.mp4` | 没抓到，扰动没有触发 |
| `libero_10/task2/D06/seed142/init0` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D06_seed142_init0.mp4` | - |
| `libero_10/task2/D06/seed143/init1` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D06_seed143_init1.mp4` | - |
| `libero_10/task2/D07/seed142/init0` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D07_seed142_init0.mp4` | - |
| `libero_10/task2/D07/seed143/init1` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D07_seed143_init1.mp4` | - |
| `libero_10/task2/D08/seed142/init0` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D08_seed142_init0.mp4` | - |
| `libero_10/task2/D08/seed143/init1` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D08_seed143_init1.mp4` | - |
| `libero_10/task2/D09/seed142/init0` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D09_seed142_init0.mp4` | - |
| `libero_10/task2/D09/seed143/init1` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D09_seed143_init1.mp4` | - |
| `libero_10/task2/D10/seed142/init0` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D10_seed142_init0.mp4` | - |
| `libero_10/task2/D10/seed143/init1` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D10_seed143_init1.mp4` | - |
| `libero_10/task2/D11/seed142/init0` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D11_seed142_init0.mp4` | - |
| `libero_10/task2/D11/seed143/init1` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D11_seed143_init1.mp4` | - |
| `libero_10/task2/D12/seed142/init0` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D12_seed142_init0.mp4` | - |
| `libero_10/task2/D12/seed143/init1` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D12_seed143_init1.mp4` | - |
| `libero_10/task2/D13/seed142/init0` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D13_seed142_init0.mp4` | - |
| `libero_10/task2/D13/seed143/init1` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D13_seed143_init1.mp4` | - |
| `libero_10/task2/D14/seed142/init0` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D14_seed142_init0.mp4` | - |
| `libero_10/task2/D14/seed143/init1` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D14_seed143_init1.mp4` | - |
| `libero_10/task2/D15/seed142/init0` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D15_seed142_init0.mp4` | - |
| `libero_10/task2/D15/seed143/init1` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D15_seed143_init1.mp4` | - |
| `libero_10/task2/D16/seed142/init0` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D16_seed142_init0.mp4` | - |
| `libero_10/task2/D16/seed143/init1` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D16_seed143_init1.mp4` | - |
| `libero_10/task2/D17/seed142/init0` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D17_seed142_init0.mp4` | - |
| `libero_10/task2/D17/seed143/init1` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D17_seed143_init1.mp4` | - |
| `libero_10/task2/D18/seed142/init0` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D18_seed142_init0.mp4` | - |
| `libero_10/task2/D18/seed143/init1` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D18_seed143_init1.mp4` | - |
| `libero_10/task2/D20/seed142/init0` | `D20` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_D20_seed142_init0.mp4` | - |
| `libero_10/task2/D20/seed143/init1` | `D20` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D20_seed143_init1.mp4` | - |
| `libero_10/task2/D21/seed142/init0` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D21_seed142_init0.mp4` | - |
| `libero_10/task2/D21/seed143/init1` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_D21_seed143_init1.mp4` | - |
| `libero_10/task2/S01/seed142/init0` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S01_seed142_init0.mp4` | - |
| `libero_10/task2/S01/seed143/init1` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S01_seed143_init1.mp4` | - |
| `libero_10/task2/S02/seed142/init0` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S02_seed142_init0.mp4` | - |
| `libero_10/task2/S02/seed143/init1` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S02_seed143_init1.mp4` | - |
| `libero_10/task2/S03/seed142/init0` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S03_seed142_init0.mp4` | - |
| `libero_10/task2/S03/seed143/init1` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S03_seed143_init1.mp4` | - |
| `libero_10/task2/S04/seed142/init0` | `S04` | `PASS` | `-` | `PASS` | 1 | `RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `pi0_libero_10_task2_S04_seed142_init0.mp4` | - |
| `libero_10/task2/S04/seed143/init1` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S04_seed143_init1.mp4` | - |
| `libero_10/task2/S05/seed142/init0` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S05_seed142_init0.mp4` | - |
| `libero_10/task2/S05/seed143/init1` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S05_seed143_init1.mp4` | - |
| `libero_10/task2/S06/seed142/init0` | `S06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S06_seed142_init0.mp4` | - |
| `libero_10/task2/S06/seed143/init1` | `S06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S06_seed143_init1.mp4` | - |
| `libero_10/task2/S07/seed142/init0` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S07_seed142_init0.mp4` | - |
| `libero_10/task2/S07/seed143/init1` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S07_seed143_init1.mp4` | - |
| `libero_10/task2/S08/seed142/init0` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S08_seed142_init0.mp4` | - |
| `libero_10/task2/S08/seed143/init1` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S08_seed143_init1.mp4` | - |
| `libero_10/task2/S09/seed142/init0` | `S09` | `PASS` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S09_seed142_init0.mp4` | 场景生成之后物体还在运动，太诡异了 |
| `libero_10/task2/S09/seed143/init1` | `S09` | `PASS` | `PASS` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S09_seed143_init1.mp4` | 场景生成之后物体还在运动，太诡异了 |
| `libero_10/task2/S10/seed142/init0` | `S10` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S10_seed142_init0.mp4` | 应该是成功了，但是扰动没有触发 |
| `libero_10/task2/S10/seed143/init1` | `S10` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S10_seed143_init1.mp4` | 应该是成功了，但是扰动没有触发 |
| `libero_10/task2/S11/seed142/init0` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S11_seed142_init0.mp4` | - |
| `libero_10/task2/S11/seed143/init1` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S11_seed143_init1.mp4` | - |
| `libero_10/task2/S12/seed142/init0` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S12_seed142_init0.mp4` | - |
| `libero_10/task2/S12/seed143/init1` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S12_seed143_init1.mp4` | - |
| `libero_10/task2/S13/seed142/init0` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S13_seed142_init0.mp4` | - |
| `libero_10/task2/S13/seed143/init1` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S13_seed143_init1.mp4` | - |
| `libero_10/task2/S14/seed142/init0` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S14_seed142_init0.mp4` | - |
| `libero_10/task2/S14/seed143/init1` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S14_seed143_init1.mp4` | - |
| `libero_10/task2/S15/seed142/init0` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S15_seed142_init0.mp4` | - |
| `libero_10/task2/S15/seed143/init1` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S15_seed143_init1.mp4` | - |
| `libero_10/task2/S16/seed142/init0` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S16_seed142_init0.mp4` | - |
| `libero_10/task2/S16/seed143/init1` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S16_seed143_init1.mp4` | - |
| `libero_10/task2/S17/seed142/init0` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S17_seed142_init0.mp4` | - |
| `libero_10/task2/S17/seed143/init1` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S17_seed143_init1.mp4` | - |
| `libero_10/task2/S18/seed142/init0` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S18_seed142_init0.mp4` | - |
| `libero_10/task2/S18/seed143/init1` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S18_seed143_init1.mp4` | - |
| `libero_10/task2/S19/seed142/init0` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S19_seed142_init0.mp4` | - |
| `libero_10/task2/S19/seed143/init1` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S19_seed143_init1.mp4` | - |
| `libero_10/task2/S20/seed142/init0` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S20_seed142_init0.mp4` | - |
| `libero_10/task2/S20/seed143/init1` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S20_seed143_init1.mp4` | - |
| `libero_10/task2/S21/seed142/init0` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S21_seed142_init0.mp4` | - |
| `libero_10/task2/S21/seed143/init1` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task2_S21_seed143_init1.mp4` | - |
| `libero_10/task2/S22/seed142/init0` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S22_seed142_init0.mp4` | - |
| `libero_10/task2/S22/seed143/init1` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task2_S22_seed143_init1.mp4` | - |
| `libero_10/task3/BASE/seed142/init0` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_BASE_seed142_init0.mp4` | - |
| `libero_10/task3/BASE/seed143/init1` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_BASE_seed143_init1.mp4` | - |
| `libero_10/task3/D01/seed142/init0` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D01_seed142_init0.mp4` | - |
| `libero_10/task3/D01/seed143/init1` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D01_seed143_init1.mp4` | - |
| `libero_10/task3/D02/seed142/init0` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D02_seed142_init0.mp4` | - |
| `libero_10/task3/D02/seed143/init1` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D02_seed143_init1.mp4` | - |
| `libero_10/task3/D03/seed142/init0` | `D03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D03_seed142_init0.mp4` | - |
| `libero_10/task3/D03/seed143/init1` | `D03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D03_seed143_init1.mp4` | - |
| `libero_10/task3/D04/seed142/init0` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D04_seed142_init0.mp4` | - |
| `libero_10/task3/D04/seed143/init1` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D04_seed143_init1.mp4` | - |
| `libero_10/task3/D05/seed142/init0` | `D05` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D05_seed142_init0.mp4` | 没有触发 |
| `libero_10/task3/D05/seed143/init1` | `D05` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D05_seed143_init1.mp4` | 没有触发 |
| `libero_10/task3/D06/seed142/init0` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D06_seed142_init0.mp4` | - |
| `libero_10/task3/D06/seed143/init1` | `D06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D06_seed143_init1.mp4` | - |
| `libero_10/task3/D07/seed142/init0` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D07_seed142_init0.mp4` | - |
| `libero_10/task3/D07/seed143/init1` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D07_seed143_init1.mp4` | - |
| `libero_10/task3/D08/seed142/init0` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D08_seed142_init0.mp4` | - |
| `libero_10/task3/D08/seed143/init1` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D08_seed143_init1.mp4` | - |
| `libero_10/task3/D09/seed142/init0` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D09_seed142_init0.mp4` | - |
| `libero_10/task3/D09/seed143/init1` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D09_seed143_init1.mp4` | - |
| `libero_10/task3/D10/seed142/init0` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D10_seed142_init0.mp4` | - |
| `libero_10/task3/D10/seed143/init1` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D10_seed143_init1.mp4` | - |
| `libero_10/task3/D11/seed142/init0` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D11_seed142_init0.mp4` | - |
| `libero_10/task3/D11/seed143/init1` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D11_seed143_init1.mp4` | - |
| `libero_10/task3/D12/seed142/init0` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D12_seed142_init0.mp4` | - |
| `libero_10/task3/D12/seed143/init1` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D12_seed143_init1.mp4` | - |
| `libero_10/task3/D13/seed142/init0` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D13_seed142_init0.mp4` | - |
| `libero_10/task3/D13/seed143/init1` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D13_seed143_init1.mp4` | - |
| `libero_10/task3/D14/seed142/init0` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D14_seed142_init0.mp4` | - |
| `libero_10/task3/D14/seed143/init1` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D14_seed143_init1.mp4` | - |
| `libero_10/task3/D15/seed142/init0` | `D15` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D15_seed142_init0.mp4` | 看不出来 |
| `libero_10/task3/D15/seed143/init1` | `D15` | `PENDING` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D15_seed143_init1.mp4` | 看不出来 |
| `libero_10/task3/D16/seed142/init0` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D16_seed142_init0.mp4` | - |
| `libero_10/task3/D16/seed143/init1` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D16_seed143_init1.mp4` | - |
| `libero_10/task3/D17/seed142/init0` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D17_seed142_init0.mp4` | - |
| `libero_10/task3/D17/seed143/init1` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D17_seed143_init1.mp4` | - |
| `libero_10/task3/D18/seed142/init0` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D18_seed142_init0.mp4` | - |
| `libero_10/task3/D18/seed143/init1` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D18_seed143_init1.mp4` | - |
| `libero_10/task3/D20/seed142/init0` | `D20` | `-` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D20_seed142_init0.mp4` | 没有触发扰动 |
| `libero_10/task3/D20/seed143/init1` | `D20` | `-` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D20_seed143_init1.mp4` | 没有触发扰动 |
| `libero_10/task3/D21/seed142/init0` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_D21_seed142_init0.mp4` | - |
| `libero_10/task3/D21/seed143/init1` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_D21_seed143_init1.mp4` | - |
| `libero_10/task3/S01/seed142/init0` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S01_seed142_init0.mp4` | - |
| `libero_10/task3/S01/seed143/init1` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S01_seed143_init1.mp4` | - |
| `libero_10/task3/S02/seed142/init0` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S02_seed142_init0.mp4` | - |
| `libero_10/task3/S02/seed143/init1` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S02_seed143_init1.mp4` | - |
| `libero_10/task3/S03/seed142/init0` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S03_seed142_init0.mp4` | - |
| `libero_10/task3/S03/seed143/init1` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S03_seed143_init1.mp4` | - |
| `libero_10/task3/S04/seed142/init0` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S04_seed142_init0.mp4` | - |
| `libero_10/task3/S04/seed143/init1` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S04_seed143_init1.mp4` | - |
| `libero_10/task3/S05/seed142/init0` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S05_seed142_init0.mp4` | - |
| `libero_10/task3/S05/seed143/init1` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S05_seed143_init1.mp4` | - |
| `libero_10/task3/S06/seed142/init0` | `S06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S06_seed142_init0.mp4` | - |
| `libero_10/task3/S06/seed143/init1` | `S06` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S06_seed143_init1.mp4` | - |
| `libero_10/task3/S07/seed142/init0` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S07_seed142_init0.mp4` | - |
| `libero_10/task3/S07/seed143/init1` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S07_seed143_init1.mp4` | - |
| `libero_10/task3/S08/seed142/init0` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S08_seed142_init0.mp4` | - |
| `libero_10/task3/S08/seed143/init1` | `S08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S08_seed143_init1.mp4` | - |
| `libero_10/task3/S09/seed142/init0` | `S09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S09_seed142_init0.mp4` | - |
| `libero_10/task3/S09/seed143/init1` | `S09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S09_seed143_init1.mp4` | - |
| `libero_10/task3/S10/seed142/init0` | `S10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S10_seed142_init0.mp4` | - |
| `libero_10/task3/S10/seed143/init1` | `S10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S10_seed143_init1.mp4` | - |
| `libero_10/task3/S11/seed142/init0` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S11_seed142_init0.mp4` | - |
| `libero_10/task3/S11/seed143/init1` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S11_seed143_init1.mp4` | - |
| `libero_10/task3/S12/seed142/init0` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S12_seed142_init0.mp4` | - |
| `libero_10/task3/S12/seed143/init1` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S12_seed143_init1.mp4` | - |
| `libero_10/task3/S13/seed142/init0` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S13_seed142_init0.mp4` | - |
| `libero_10/task3/S13/seed143/init1` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S13_seed143_init1.mp4` | - |
| `libero_10/task3/S14/seed142/init0` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S14_seed142_init0.mp4` | - |
| `libero_10/task3/S14/seed143/init1` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S14_seed143_init1.mp4` | - |
| `libero_10/task3/S15/seed142/init0` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S15_seed142_init0.mp4` | - |
| `libero_10/task3/S15/seed143/init1` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S15_seed143_init1.mp4` | - |
| `libero_10/task3/S16/seed142/init0` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S16_seed142_init0.mp4` | - |
| `libero_10/task3/S16/seed143/init1` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S16_seed143_init1.mp4` | - |
| `libero_10/task3/S17/seed142/init0` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S17_seed142_init0.mp4` | - |
| `libero_10/task3/S17/seed143/init1` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S17_seed143_init1.mp4` | - |
| `libero_10/task3/S18/seed142/init0` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S18_seed142_init0.mp4` | - |
| `libero_10/task3/S18/seed143/init1` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S18_seed143_init1.mp4` | - |
| `libero_10/task3/S19/seed142/init0` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S19_seed142_init0.mp4` | - |
| `libero_10/task3/S19/seed143/init1` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S19_seed143_init1.mp4` | - |
| `libero_10/task3/S20/seed142/init0` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S20_seed142_init0.mp4` | - |
| `libero_10/task3/S20/seed143/init1` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S20_seed143_init1.mp4` | - |
| `libero_10/task3/S21/seed142/init0` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S21_seed142_init0.mp4` | - |
| `libero_10/task3/S21/seed143/init1` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S21_seed143_init1.mp4` | - |
| `libero_10/task3/S22/seed142/init0` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task3_S22_seed142_init0.mp4` | - |
| `libero_10/task3/S22/seed143/init1` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `SUCCESS` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/success/pi0_libero_10_task3_S22_seed143_init1.mp4` | - |
| `libero_10/task4/BASE/seed142/init0` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_BASE_seed142_init0.mp4` | - |
| `libero_10/task4/BASE/seed143/init1` | `BASE` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_BASE_seed143_init1.mp4` | - |
| `libero_10/task4/D01/seed142/init0` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D01_seed142_init0.mp4` | - |
| `libero_10/task4/D01/seed143/init1` | `D01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D01_seed143_init1.mp4` | - |
| `libero_10/task4/D02/seed142/init0` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D02_seed142_init0.mp4` | - |
| `libero_10/task4/D02/seed143/init1` | `D02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D02_seed143_init1.mp4` | - |
| `libero_10/task4/D03/seed142/init0` | `D03` | `PENDING` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D03_seed142_init0.mp4` | 被占用之后，物体消失了 |
| `libero_10/task4/D03/seed143/init1` | `D03` | `PENDING` | `ISSUE` | `ISSUE` | 0 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D03_seed143_init1.mp4` | 占用的物品放错位置了 |
| `libero_10/task4/D04/seed142/init0` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D04_seed142_init0.mp4` | - |
| `libero_10/task4/D04/seed143/init1` | `D04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D04_seed143_init1.mp4` | - |
| `libero_10/task4/D05/seed142/init0` | `D05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D05_seed142_init0.mp4` | - |
| `libero_10/task4/D05/seed143/init1` | `D05` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D05_seed143_init1.mp4` | 没有抓到物体，但是干扰的出现了 |
| `libero_10/task4/D06/seed142/init0` | `D06` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D06_seed142_init0.mp4` | 扰动没有出现 |
| `libero_10/task4/D06/seed143/init1` | `D06` | `PASS` | `ISSUE` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D06_seed143_init1.mp4` | 扰动没有出现 |
| `libero_10/task4/D07/seed142/init0` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D07_seed142_init0.mp4` | - |
| `libero_10/task4/D07/seed143/init1` | `D07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D07_seed143_init1.mp4` | - |
| `libero_10/task4/D08/seed142/init0` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D08_seed142_init0.mp4` | - |
| `libero_10/task4/D08/seed143/init1` | `D08` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D08_seed143_init1.mp4` | - |
| `libero_10/task4/D09/seed142/init0` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D09_seed142_init0.mp4` | - |
| `libero_10/task4/D09/seed143/init1` | `D09` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D09_seed143_init1.mp4` | - |
| `libero_10/task4/D10/seed142/init0` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D10_seed142_init0.mp4` | - |
| `libero_10/task4/D10/seed143/init1` | `D10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D10_seed143_init1.mp4` | - |
| `libero_10/task4/D11/seed142/init0` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D11_seed142_init0.mp4` | - |
| `libero_10/task4/D11/seed143/init1` | `D11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D11_seed143_init1.mp4` | - |
| `libero_10/task4/D12/seed142/init0` | `D12` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D12_seed142_init0.mp4` | 成功了，标签错误 |
| `libero_10/task4/D12/seed143/init1` | `D12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D12_seed143_init1.mp4` | - |
| `libero_10/task4/D13/seed142/init0` | `D13` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D13_seed142_init0.mp4` | 成功 了，标签错误 |
| `libero_10/task4/D13/seed143/init1` | `D13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D13_seed143_init1.mp4` | - |
| `libero_10/task4/D14/seed142/init0` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D14_seed142_init0.mp4` | - |
| `libero_10/task4/D14/seed143/init1` | `D14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D14_seed143_init1.mp4` | - |
| `libero_10/task4/D15/seed142/init0` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D15_seed142_init0.mp4` | - |
| `libero_10/task4/D15/seed143/init1` | `D15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D15_seed143_init1.mp4` | - |
| `libero_10/task4/D16/seed142/init0` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D16_seed142_init0.mp4` | - |
| `libero_10/task4/D16/seed143/init1` | `D16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D16_seed143_init1.mp4` | - |
| `libero_10/task4/D17/seed142/init0` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D17_seed142_init0.mp4` | - |
| `libero_10/task4/D17/seed143/init1` | `D17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D17_seed143_init1.mp4` | - |
| `libero_10/task4/D18/seed142/init0` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D18_seed142_init0.mp4` | - |
| `libero_10/task4/D18/seed143/init1` | `D18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D18_seed143_init1.mp4` | - |
| `libero_10/task4/D20/seed142/init0` | `D20` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D20_seed142_init0.mp4` | - |
| `libero_10/task4/D20/seed143/init1` | `D20` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D20_seed143_init1.mp4` | - |
| `libero_10/task4/D21/seed142/init0` | `D21` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D21_seed142_init0.mp4` | 成功了，标签错误 |
| `libero_10/task4/D21/seed143/init1` | `D21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `TRIGGERED` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_D21_seed143_init1.mp4` | - |
| `libero_10/task4/S01/seed142/init0` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S01_seed142_init0.mp4` | - |
| `libero_10/task4/S01/seed143/init1` | `S01` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S01_seed143_init1.mp4` | - |
| `libero_10/task4/S02/seed142/init0` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S02_seed142_init0.mp4` | - |
| `libero_10/task4/S02/seed143/init1` | `S02` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S02_seed143_init1.mp4` | - |
| `libero_10/task4/S03/seed142/init0` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S03_seed142_init0.mp4` | - |
| `libero_10/task4/S03/seed143/init1` | `S03` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S03_seed143_init1.mp4` | - |
| `libero_10/task4/S04/seed142/init0` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S04_seed142_init0.mp4` | - |
| `libero_10/task4/S04/seed143/init1` | `S04` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S04_seed143_init1.mp4` | - |
| `libero_10/task4/S05/seed142/init0` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S05_seed142_init0.mp4` | - |
| `libero_10/task4/S05/seed143/init1` | `S05` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S05_seed143_init1.mp4` | - |
| `libero_10/task4/S06/seed142/init0` | `S06` | `ISSUE` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S06_seed142_init0.mp4` | 目标物体消失了 |
| `libero_10/task4/S06/seed143/init1` | `S06` | `ISSUE` | `PENDING` | `PASS` | 1 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S06_seed143_init1.mp4` | 目标物体消失了 |
| `libero_10/task4/S07/seed142/init0` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S07_seed142_init0.mp4` | - |
| `libero_10/task4/S07/seed143/init1` | `S07` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S07_seed143_init1.mp4` | - |
| `libero_10/task4/S08/seed142/init0` | `S08` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S08_seed142_init0.mp4` | 成功了，标签错误 |
| `libero_10/task4/S08/seed143/init1` | `S08` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S08_seed143_init1.mp4` | 成功了，标签错误 |
| `libero_10/task4/S09/seed142/init0` | `S09` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S09_seed142_init0.mp4` | 应该是抓到了，穿模了 |
| `libero_10/task4/S09/seed143/init1` | `S09` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S09_seed143_init1.mp4` | 应该是抓到了，穿模了 |
| `libero_10/task4/S10/seed142/init0` | `S10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S10_seed142_init0.mp4` | - |
| `libero_10/task4/S10/seed143/init1` | `S10` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S10_seed143_init1.mp4` | - |
| `libero_10/task4/S11/seed142/init0` | `S11` | `ISSUE` | `PASS` | `PASS` | 2 | `ISSUE_OPEN` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S11_seed142_init0.mp4` | 成功了，标签错误 |
| `libero_10/task4/S11/seed143/init1` | `S11` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S11_seed143_init1.mp4` | - |
| `libero_10/task4/S12/seed142/init0` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S12_seed142_init0.mp4` | - |
| `libero_10/task4/S12/seed143/init1` | `S12` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S12_seed143_init1.mp4` | - |
| `libero_10/task4/S13/seed142/init0` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S13_seed142_init0.mp4` | - |
| `libero_10/task4/S13/seed143/init1` | `S13` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S13_seed143_init1.mp4` | - |
| `libero_10/task4/S14/seed142/init0` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S14_seed142_init0.mp4` | - |
| `libero_10/task4/S14/seed143/init1` | `S14` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S14_seed143_init1.mp4` | - |
| `libero_10/task4/S15/seed142/init0` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S15_seed142_init0.mp4` | - |
| `libero_10/task4/S15/seed143/init1` | `S15` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S15_seed143_init1.mp4` | - |
| `libero_10/task4/S16/seed142/init0` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S16_seed142_init0.mp4` | - |
| `libero_10/task4/S16/seed143/init1` | `S16` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S16_seed143_init1.mp4` | - |
| `libero_10/task4/S17/seed142/init0` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S17_seed142_init0.mp4` | - |
| `libero_10/task4/S17/seed143/init1` | `S17` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S17_seed143_init1.mp4` | - |
| `libero_10/task4/S18/seed142/init0` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S18_seed142_init0.mp4` | - |
| `libero_10/task4/S18/seed143/init1` | `S18` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S18_seed143_init1.mp4` | - |
| `libero_10/task4/S19/seed142/init0` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S19_seed142_init0.mp4` | - |
| `libero_10/task4/S19/seed143/init1` | `S19` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S19_seed143_init1.mp4` | - |
| `libero_10/task4/S20/seed142/init0` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S20_seed142_init0.mp4` | - |
| `libero_10/task4/S20/seed143/init1` | `S20` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S20_seed143_init1.mp4` | - |
| `libero_10/task4/S21/seed142/init0` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S21_seed142_init0.mp4` | - |
| `libero_10/task4/S21/seed143/init1` | `S21` | `PASS` | `PASS` | `PASS` | 3 | `STABLE_3_NO_RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S21_seed143_init1.mp4` | - |
| `libero_10/task4/S22/seed142/init0` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S22_seed142_init0.mp4` | - |
| `libero_10/task4/S22/seed143/init1` | `S22` | `-` | `PASS` | `PASS` | 2 | `RETEST` | `FAILURE` | `NOT_APPLICABLE` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `data/videos_0831/failure/pi0_libero_10_task4_S22_seed143_init1.mp4` | - |

## 逐轮审核日志

| Round ID | 日期 | 审核人 | Review Key | Commit | BDDL SHA-256 | 策略结果 | 触发状态 | 审核判定 | 问题类型 | 问题说明 | 视频/证据 | 修复 Commit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D02/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 机器人未成功抓到目标物，接收器全程未移动。 | `data/videos/failure/pi0_libero_10_task0_D02_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D03/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 机器人未成功抓到目标物，没有触发 | `data/videos/failure/pi0_libero_10_task0_D03_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D03/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 机器人抓到目标物，扰动没有触发 | `data/videos/failure/pi0_libero_10_task0_D03_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D05/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 第一次没抓到，第二个抓到了，障碍物没出现<br> | `data/videos/failure/pi0_libero_10_task0_D05_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D12/seed142/init0` | `-` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 这个肉眼看不出来 | `data/videos/failure/pi0_libero_10_task0_D12_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D12/seed143/init1` | `-` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 这个肉眼看不出来 | `data/videos/failure/pi0_libero_10_task0_D12_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D17/seed142/init0` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `placement_or_path_issue` | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 | `data/videos/failure/pi0_libero_10_task0_D17_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D17/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `placement_or_path_issue` | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 | `data/videos/failure/pi0_libero_10_task0_D17_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/D18/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 第一个物体没抓到，然后第二个物体抓到了，但是没有触发扰动。 | `data/videos/failure/pi0_libero_10_task0_D18_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/S06/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 替换的物品难度过大了 大于夹爪的最大限度了 | `data/videos/failure/pi0_libero_10_task0_S06_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/S06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 替换的物品难度过大了 大于夹爪的最大限度了 | `data/videos/failure/pi0_libero_10_task0_S06_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/S09/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 实际上成功了 | `data/videos/failure/pi0_libero_10_task0_S09_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/S10/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 未增加无关杂物 | `data/videos/failure/pi0_libero_10_task0_S10_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task0/S10/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 未增加无关杂物 | `data/videos/failure/pi0_libero_10_task0_S10_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D03/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 第一个没抓到，第二个抓到放进去了扰动没有触发 | `data/videos/failure/pi0_libero_10_task1_D03_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D03/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 第一个没抓到，第二个抓到放进去了扰动没有触发 | `data/videos/failure/pi0_libero_10_task1_D03_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D06/seed142/init0` | `-` | `-` | `SUCCESS` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没有触发 | `data/videos/success/pi0_libero_10_task1_D06_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没有触发 | `data/videos/failure/pi0_libero_10_task1_D06_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D14/seed142/init0` | `-` | `-` | `SUCCESS` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不出来 | `data/videos/success/pi0_libero_10_task1_D14_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/D14/seed143/init1` | `-` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不出来<br> | `data/videos/failure/pi0_libero_10_task1_D14_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task1/S06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 实例直接没掉了 | `data/videos/failure/pi0_libero_10_task1_S06_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D03/seed142/init0` | `-` | `-` | `SUCCESS` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 扰动没有发生<br> | `data/videos/success/pi0_libero_10_task2_D03_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D03/seed143/init1` | `-` | `-` | `SUCCESS` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 扰动没有发生 | `data/videos/success/pi0_libero_10_task2_D03_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D04/seed142/init0` | `-` | `-` | `SUCCESS` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 遮挡物没什么用处 | `data/videos/success/pi0_libero_10_task2_D04_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D04/seed143/init1` | `-` | `-` | `SUCCESS` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 遮挡物没什么用处 | `data/videos/success/pi0_libero_10_task2_D04_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D05/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没抓到，扰动没有触发 | `data/videos/failure/pi0_libero_10_task2_D05_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/D05/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没抓到，扰动没有触发 | `data/videos/failure/pi0_libero_10_task2_D05_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/S10/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `not_triggered_or_not_visible` | 应该是成功了，但是扰动没有触发 | `data/videos/failure/pi0_libero_10_task2_S10_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task2/S10/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `not_triggered_or_not_visible` | 应该是成功了，但是扰动没有触发 | `data/videos/failure/pi0_libero_10_task2_S10_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task3/D05/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发 | `data/videos/failure/pi0_libero_10_task3_D05_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task3/D05/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发 | `data/videos/failure/pi0_libero_10_task3_D05_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task3/D15/seed142/init0` | `-` | `-` | `SUCCESS` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不出来 | `data/videos/success/pi0_libero_10_task3_D15_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task3/D15/seed143/init1` | `-` | `-` | `SUCCESS` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不出来 | `data/videos/success/pi0_libero_10_task3_D15_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/D03/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 第二次没有触发 | `data/videos/failure/pi0_libero_10_task4_D03_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/D03/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 第二次没有触发 | `data/videos/failure/pi0_libero_10_task4_D03_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/D12/seed142/init0` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 成功了，标签错误 | `data/videos/failure/pi0_libero_10_task4_D12_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/D13/seed142/init0` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 成功 了，标签错误 | `data/videos/failure/pi0_libero_10_task4_D13_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/D21/seed142/init0` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 成功了，标签错误 | `data/videos/failure/pi0_libero_10_task4_D21_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S06/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `placement_or_path_issue` | 扰动不合理 | `data/videos/failure/pi0_libero_10_task4_S06_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `placement_or_path_issue` | 扰动不合理 | `data/videos/failure/pi0_libero_10_task4_S06_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S08/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 成功了，标签错误 | `data/videos/failure/pi0_libero_10_task4_S08_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S08/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 成功了，标签错误 | `data/videos/failure/pi0_libero_10_task4_S08_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S09/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 应该是抓到了，穿模了 | `data/videos/failure/pi0_libero_10_task4_S09_seed142_init0.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S09/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 应该是抓到了，穿模了 | `data/videos/failure/pi0_libero_10_task4_S09_seed143_init1.mp4` | `-` |
| `R001` | `2026-08-17` | `huang` | `libero_10/task4/S11/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 成功了，标签错误 | `data/videos/failure/pi0_libero_10_task4_S11_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D02/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没抓到，没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D02_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D02/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没抓到，没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D02_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D03/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没抓到，没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D03_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D03/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没抓到，没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D03_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D05/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没抓到，没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D05_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D05/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 穿模 | `data/videos_0825/failure/pi0_libero_10_task0_D05_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D20/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发<br> | `data/videos_0825/failure/pi0_libero_10_task0_D20_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/D20/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发 | `data/videos_0825/failure/pi0_libero_10_task0_D20_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/S05/seed142/init0` | `-` | `-` | `SUCCESS` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 限制不是很明显 | `data/videos_0825/success/pi0_libero_10_task0_S05_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/S05/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 限制不是很明显 | `data/videos_0825/failure/pi0_libero_10_task0_S05_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task0/S09/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `implementation_issue` | 成功了，但是判定失败了 | `data/videos_0825/failure/pi0_libero_10_task0_S09_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task1/D03/seed142/init0` | `-` | `-` | `SUCCESS` | `TRIGGERED` | `ISSUE` | `scene_or_asset_anomaly` | 被占用之后，两个物体都消失了 | `data/videos_0825/success/pi0_libero_10_task1_D03_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task1/D03/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `scene_or_asset_anomaly` | 被占用之后，两个物体都消失了  | `data/videos_0825/failure/pi0_libero_10_task1_D03_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task1/D20/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发 | `data/videos_0825/failure/pi0_libero_10_task1_D20_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task1/D20/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发 | `data/videos_0825/failure/pi0_libero_10_task1_D20_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task2/D02/seed142/init0` | `-` | `-` | `SUCCESS` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 扰动没有发生 | `data/videos_0825/success/pi0_libero_10_task2_D02_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task2/D03/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没有触发扰动 | `data/videos_0825/failure/pi0_libero_10_task2_D03_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task2/D03/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 没有触发扰动 | `data/videos_0825/failure/pi0_libero_10_task2_D03_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task3/D20/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发扰动 | `data/videos_0825/failure/pi0_libero_10_task3_D20_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task3/D20/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `PENDING` | `not_triggered_or_not_visible` | 没有触发扰动 | `data/videos_0825/failure/pi0_libero_10_task3_D20_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/D03/seed142/init0` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `scene_or_asset_anomaly` | 被占用之后，物体消失了  | `data/videos_0825/failure/pi0_libero_10_task4_D03_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/D03/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 没放进去，但是占用的物体出现了 | `data/videos_0825/failure/pi0_libero_10_task4_D03_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/D05/seed143/init1` | `-` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `implementation_issue` | 没有抓到物体，但是干扰的出现了 | `data/videos_0825/failure/pi0_libero_10_task4_D05_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/D06/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 扰动没有出现 | `data/videos_0825/failure/pi0_libero_10_task4_D06_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/D06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 扰动没有出现 | `data/videos_0825/failure/pi0_libero_10_task4_D06_seed143_init1.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/S06/seed142/init0` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `PENDING` | `scene_or_asset_anomaly` | 目标物体消失了 | `data/videos_0825/failure/pi0_libero_10_task4_S06_seed142_init0.mp4` | `-` |
| `R002` | `2026-08-25` | `huang` | `libero_10/task4/S06/seed143/init1` | `-` | `-` | `FAILURE` | `NOT_APPLICABLE` | `PENDING` | `scene_or_asset_anomaly` | 目标物体消失了 | `data/videos_0825/failure/pi0_libero_10_task4_S06_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task0/D03/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `SUCCESS` | `TRIGGERED` | `PENDING` | `scene_or_asset_anomaly` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `data/videos_0831/success/pi0_libero_10_task0_D03_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task0/D20/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不太出来 | `data/videos_0831/failure/pi0_libero_10_task0_D20_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task0/D20/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 看不太出来 | `data/videos_0831/failure/pi0_libero_10_task0_D20_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/D03/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `SUCCESS` | `TRIGGERED` | `PENDING` | `scene_or_asset_anomaly` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `data/videos_0831/success/pi0_libero_10_task1_D03_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/D03/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `SUCCESS` | `TRIGGERED` | `PENDING` | `scene_or_asset_anomaly` | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `data/videos_0831/success/pi0_libero_10_task1_D03_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/D05/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `TRIGGERED` | `PENDING` | `placement_or_path_issue` | 第二个的障碍物放置位置不太合理，没有在运输路径上面<br> | `data/videos_0831/failure/pi0_libero_10_task1_D05_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/D20/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 肉眼看不出来 | `data/videos_0831/failure/pi0_libero_10_task1_D20_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/D20/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `PENDING` | `PENDING` | `definition_or_visibility_unclear` | 肉眼看不出来 | `data/videos_0831/failure/pi0_libero_10_task1_D20_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/S06/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `scene_or_asset_anomaly` | 目标直接消失了 | `data/videos_0831/failure/pi0_libero_10_task1_S06_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/S06/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `scene_or_asset_anomaly` | 目标变大了，这不太合理，不可能抓的到 | `data/videos_0831/failure/pi0_libero_10_task1_S06_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/S10/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `not_triggered_or_not_visible` | 没有出现应有的杂物 | `data/videos_0831/failure/pi0_libero_10_task1_S10_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task1/S10/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `not_triggered_or_not_visible` | 没有出现应有的杂物 | `data/videos_0831/failure/pi0_libero_10_task1_S10_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task2/D03/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `SUCCESS` | `NOT_TRIGGERED` | `ISSUE` | `not_triggered_or_not_visible` | 抓到物体了，但是扰动没有发生 | `data/videos_0831/success/pi0_libero_10_task2_D03_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task2/S09/seed142/init0` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `scene_or_asset_anomaly` | 场景生成之后物体还在运动，太诡异了 | `data/videos_0831/failure/pi0_libero_10_task2_S09_seed142_init0.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task2/S09/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `scene_or_asset_anomaly` | 场景生成之后物体还在运动，太诡异了 | `data/videos_0831/failure/pi0_libero_10_task2_S09_seed143_init1.mp4` | `-` |
| `R003` | `2026-08-31` | `huang` | `libero_10/task4/D03/seed143/init1` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` | `-` | `FAILURE` | `TRIGGERED` | `ISSUE` | `placement_or_path_issue` | 占用的物品放错位置了<br> | `data/videos_0831/failure/pi0_libero_10_task4_D03_seed143_init1.mp4` | `-` |

## 状态失效记录

| 日期 | Review Key | 原状态 | 失效原因 | 相关文件或 Commit | 新状态 |
|---|---|---|---|---|---|
| `YYYY-MM-DD` | `<key>` | `STABLE_3_NO_RETEST` | `<BDDL/Runtime/asset/feedback change>` | `<path/sha>` | `INVALIDATED_RETEST` |

## 待复测队列

| 优先级 | Review Key | 当前连续 PASS | 复测原因 | 目标轮次 | 负责人 |
|---:|---|---:|---|---|---|
| `P0` | `libero_10/task0/D02/seed142/init0` | 1 | 没抓到，没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task0/D02/seed143/init1` | 1 | 没抓到，没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task0/D03/seed142/init0` | 0 | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `R004` | `huang` |
| `P0` | `libero_10/task0/D03/seed143/init1` | 1 | 没抓到，没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task0/D05/seed142/init0` | 1 | 没抓到，没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task0/D05/seed143/init1` | 1 | 穿模 | `R004` | `huang` |
| `P0` | `libero_10/task0/D12/seed142/init0` | 2 | 这个肉眼看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task0/D12/seed143/init1` | 2 | 这个肉眼看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task0/D17/seed142/init0` | 2 | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 | `R004` | `huang` |
| `P0` | `libero_10/task0/D17/seed143/init1` | 2 | 机械臂已到达目标位置时夹爪未闭合，抬起离开目标后才闭合，未形成有效抓取接触。 | `R004` | `huang` |
| `P0` | `libero_10/task0/D18/seed143/init1` | 2 | 第一个物体没抓到，然后第二个物体抓到了，但是没有触发扰动。 | `R004` | `huang` |
| `P0` | `libero_10/task0/D20/seed142/init0` | 0 | 看不太出来 | `R004` | `huang` |
| `P0` | `libero_10/task0/D20/seed143/init1` | 0 | 看不太出来 | `R004` | `huang` |
| `P0` | `libero_10/task0/S05/seed142/init0` | 1 | 限制不是很明显 | `R004` | `huang` |
| `P0` | `libero_10/task0/S05/seed143/init1` | 1 | 限制不是很明显 | `R004` | `huang` |
| `P0` | `libero_10/task0/S06/seed142/init0` | 2 | 替换的物品难度过大了 大于夹爪的最大限度了 | `R004` | `huang` |
| `P0` | `libero_10/task0/S06/seed143/init1` | 2 | 替换的物品难度过大了 大于夹爪的最大限度了 | `R004` | `huang` |
| `P0` | `libero_10/task0/S09/seed142/init0` | 1 | 成功了，但是判定失败了 | `R004` | `huang` |
| `P0` | `libero_10/task0/S10/seed142/init0` | 2 | 未增加无关杂物 | `R004` | `huang` |
| `P0` | `libero_10/task0/S10/seed143/init1` | 2 | 未增加无关杂物 | `R004` | `huang` |
| `P2` | `libero_10/task0/S22/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task0/S22/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task1/D03/seed142/init0` | 0 | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `R004` | `huang` |
| `P0` | `libero_10/task1/D03/seed143/init1` | 0 | 占用的物体消失后，任务还是可以完成，但是这个扰动的名字就叫临时占用，不知道占用的物体是否应该长期存在 | `R004` | `huang` |
| `P0` | `libero_10/task1/D05/seed143/init1` | 0 | 第二个的障碍物放置位置不太合理，没有在运输路径上面 | `R004` | `huang` |
| `P0` | `libero_10/task1/D06/seed142/init0` | 2 | 没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task1/D06/seed143/init1` | 2 | 没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task1/D14/seed142/init0` | 2 | 看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task1/D14/seed143/init1` | 2 | 看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task1/D20/seed142/init0` | 0 | 肉眼看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task1/D20/seed143/init1` | 0 | 肉眼看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task1/S06/seed142/init0` | 0 | 目标直接消失了 | `R004` | `huang` |
| `P0` | `libero_10/task1/S06/seed143/init1` | 0 | 目标变大了，这不太合理，不可能抓的到 | `R004` | `huang` |
| `P0` | `libero_10/task1/S10/seed142/init0` | 0 | 没有出现应有的杂物 | `R004` | `huang` |
| `P0` | `libero_10/task1/S10/seed143/init1` | 0 | 没有出现应有的杂物 | `R004` | `huang` |
| `P2` | `libero_10/task1/S22/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task1/S22/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task2/D02/seed142/init0` | 1 | 扰动没有发生 | `R004` | `huang` |
| `P0` | `libero_10/task2/D03/seed142/init0` | 0 | 抓到物体了，但是扰动没有发生 | `R004` | `huang` |
| `P0` | `libero_10/task2/D03/seed143/init1` | 1 | 没有触发扰动 | `R004` | `huang` |
| `P0` | `libero_10/task2/D04/seed142/init0` | 2 | 遮挡物没什么用处 | `R004` | `huang` |
| `P0` | `libero_10/task2/D04/seed143/init1` | 2 | 遮挡物没什么用处 | `R004` | `huang` |
| `P0` | `libero_10/task2/D05/seed142/init0` | 2 | 没抓到，扰动没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task2/D05/seed143/init1` | 2 | 没抓到，扰动没有触发 | `R004` | `huang` |
| `P2` | `libero_10/task2/D20/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task2/D20/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task2/S04/seed142/init0` | 1 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task2/S09/seed142/init0` | 0 | 场景生成之后物体还在运动，太诡异了 | `R004` | `huang` |
| `P0` | `libero_10/task2/S09/seed143/init1` | 0 | 场景生成之后物体还在运动，太诡异了 | `R004` | `huang` |
| `P0` | `libero_10/task2/S10/seed142/init0` | 2 | 应该是成功了，但是扰动没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task2/S10/seed143/init1` | 2 | 应该是成功了，但是扰动没有触发 | `R004` | `huang` |
| `P2` | `libero_10/task2/S22/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task2/S22/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task3/D05/seed142/init0` | 2 | 没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task3/D05/seed143/init1` | 2 | 没有触发 | `R004` | `huang` |
| `P0` | `libero_10/task3/D15/seed142/init0` | 2 | 看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task3/D15/seed143/init1` | 2 | 看不出来 | `R004` | `huang` |
| `P0` | `libero_10/task3/D20/seed142/init0` | 1 | 没有触发扰动 | `R004` | `huang` |
| `P0` | `libero_10/task3/D20/seed143/init1` | 1 | 没有触发扰动 | `R004` | `huang` |
| `P2` | `libero_10/task3/S22/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task3/S22/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task4/D03/seed142/init0` | 1 | 被占用之后，物体消失了 | `R004` | `huang` |
| `P0` | `libero_10/task4/D03/seed143/init1` | 0 | 占用的物品放错位置了 | `R004` | `huang` |
| `P0` | `libero_10/task4/D05/seed143/init1` | 1 | 没有抓到物体，但是干扰的出现了 | `R004` | `huang` |
| `P0` | `libero_10/task4/D06/seed142/init0` | 1 | 扰动没有出现 | `R004` | `huang` |
| `P0` | `libero_10/task4/D06/seed143/init1` | 1 | 扰动没有出现 | `R004` | `huang` |
| `P0` | `libero_10/task4/D12/seed142/init0` | 2 | 成功了，标签错误 | `R004` | `huang` |
| `P0` | `libero_10/task4/D13/seed142/init0` | 2 | 成功 了，标签错误 | `R004` | `huang` |
| `P2` | `libero_10/task4/D20/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task4/D20/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P0` | `libero_10/task4/D21/seed142/init0` | 2 | 成功了，标签错误 | `R004` | `huang` |
| `P0` | `libero_10/task4/S06/seed142/init0` | 1 | 目标物体消失了 | `R004` | `huang` |
| `P0` | `libero_10/task4/S06/seed143/init1` | 1 | 目标物体消失了 | `R004` | `huang` |
| `P0` | `libero_10/task4/S08/seed142/init0` | 2 | 成功了，标签错误 | `R004` | `huang` |
| `P0` | `libero_10/task4/S08/seed143/init1` | 2 | 成功了，标签错误 | `R004` | `huang` |
| `P0` | `libero_10/task4/S09/seed142/init0` | 2 | 应该是抓到了，穿模了 | `R004` | `huang` |
| `P0` | `libero_10/task4/S09/seed143/init1` | 2 | 应该是抓到了，穿模了 | `R004` | `huang` |
| `P0` | `libero_10/task4/S11/seed142/init0` | 2 | 成功了，标签错误 | `R004` | `huang` |
| `P2` | `libero_10/task4/S22/seed142/init0` | 2 | 未满连续三轮 PASS | `R004` | `huang` |
| `P2` | `libero_10/task4/S22/seed143/init1` | 2 | 未满连续三轮 PASS | `R004` | `huang` |

---

## R004 定向复审记录

> 负责人：huang<br>
> 审核日期：2026-09-04<br>
> 数据批次：`0902rollout` / `pi0-review-final-20260902-51bb70b`<br>
> rollout commit：`51bb70b8f32dde58b61f53b4afe65bd18985f348`

### 范围与证据

本轮是问题项定向复审，不是全量审核。覆盖 `libero_10/task0-task4` 共 44 个 task/case 组、88 个独立 rollout；每组包含 seed142/init0 与 seed143/init1 两次尝试。未出现在本批次中的稳定项不视为漏审，也不新增审核结论。

- 结果文件 SHA-256：`4b41b621167970c2283b43e5186d4834efc2779f0722f9851cc193cd864ee9c5`
- 原始结果：`human_review_results 0902.csv`
- 视频与 rollout 对应：同批次 `0902rollout/index.tsv`

### 审核结果汇总

| 结论 | 数量 | 占比 |
|---|---:|---:|
| 认可 | 74 | 84.1% |
| 错误 | 5 | 5.7% |
| 存疑 | 9 | 10.2% |
| 异常 | 0 | 0.0% |
| 合计 | 88 | 100.0% |

| Task | 组数 | PASS | ISSUE | PENDING |
|---:|---:|---:|---:|---:|
| 0 | 12 | 21 | 1 | 2 |
| 1 | 8 | 12 | 2 | 2 |
| 2 | 7 | 8 | 1 | 5 |
| 3 | 6 | 12 | 0 | 0 |
| 4 | 11 | 21 | 1 | 0 |

### R004 逐 rollout 记录

| Review Key | 策略结果 | 触发状态 | 审核判定 | Episode ID | 视频证据 | 备注 |
|---|---|---|---|---|---|---|
| `libero_10/task0/D02/seed142/init0` | `FAILURE` | `TRIGGERED` | `ISSUE` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D02_seed142_init0.mp4` | 扰动没有触发 |
| `libero_10/task0/D02/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D02_seed143_init1.mp4` | - |
| `libero_10/task0/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D03_seed142_init0.mp4` | 第一次没有抓到，没有触发占用的这个扰动 |
| `libero_10/task0/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D03_seed143_init1.mp4` | 第一次没有抓到，没有触发占用的这个扰动 |
| `libero_10/task0/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D05_seed142_init0.mp4` | - |
| `libero_10/task0/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D05_seed143_init1.mp4` | - |
| `libero_10/task0/D12/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D12_seed142_init0.mp4` | - |
| `libero_10/task0/D12/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D12_seed143_init1.mp4` | - |
| `libero_10/task0/D17/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D17_seed142_init0.mp4` | - |
| `libero_10/task0/D17/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D17_seed143_init1.mp4` | - |
| `libero_10/task0/D18/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D18_seed142_init0.mp4` | - |
| `libero_10/task0/D18/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D18_seed143_init1.mp4` | - |
| `libero_10/task0/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_D20_seed142_init0.mp4` | - |
| `libero_10/task0/D20/seed143/init1` | `SUCCESS` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task0_D20_seed143_init1.mp4` | - |
| `libero_10/task0/S05/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S05_seed142_init0.mp4` | - |
| `libero_10/task0/S05/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S05_seed143_init1.mp4` | - |
| `libero_10/task0/S06/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task0_S06_seed142_init0.mp4` | - |
| `libero_10/task0/S06/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S06_seed143_init1.mp4` | - |
| `libero_10/task0/S09/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S09_seed142_init0.mp4` | - |
| `libero_10/task0/S09/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S09_seed143_init1.mp4` | - |
| `libero_10/task0/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S10_seed142_init0.mp4` | - |
| `libero_10/task0/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S10_seed143_init1.mp4` | - |
| `libero_10/task0/S11/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task0_S11_seed142_init0.mp4` | - |
| `libero_10/task0/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task0_S11_seed143_init1.mp4` | - |
| `libero_10/task1/D03/seed142/init0` | `SUCCESS` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task1_D03_seed142_init0.mp4` | - |
| `libero_10/task1/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D03_seed143_init1.mp4` | - |
| `libero_10/task1/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D05_seed142_init0.mp4` | - |
| `libero_10/task1/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D05_seed143_init1.mp4` | - |
| `libero_10/task1/D06/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D06_seed142_init0.mp4` | - |
| `libero_10/task1/D06/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D06_seed143_init1.mp4` | - |
| `libero_10/task1/D14/seed142/init0` | `SUCCESS` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/success/pi0_libero_10_task1_D14_seed142_init0.mp4` | 肉眼看不太出来 |
| `libero_10/task1/D14/seed143/init1` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D14_seed143_init1.mp4` | 肉眼看不太出来 |
| `libero_10/task1/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D20_seed142_init0.mp4` | - |
| `libero_10/task1/D20/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_D20_seed143_init1.mp4` | - |
| `libero_10/task1/S06/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_S06_seed142_init0.mp4` | 替换的这个同类型实例大于机械臂夹爪的最大限度，任务不可能成功，不太合理，应该替换个大小差不多的吧 |
| `libero_10/task1/S06/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_S06_seed143_init1.mp4` | 替换的这个同类型实例大于机械臂夹爪的最大限度，任务不可能成功，不太合理，应该替换个大小差不多的吧 |
| `libero_10/task1/S10/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task1_S10_seed142_init0.mp4` | - |
| `libero_10/task1/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_S10_seed143_init1.mp4` | - |
| `libero_10/task1/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_S11_seed142_init0.mp4` | - |
| `libero_10/task1/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task1_S11_seed143_init1.mp4` | - |
| `libero_10/task2/D02/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D02_seed142_init0.mp4` | - |
| `libero_10/task2/D02/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D02_seed143_init1.mp4` | - |
| `libero_10/task2/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D03_seed142_init0.mp4` | 没抓到，没有触发扰动 |
| `libero_10/task2/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `ISSUE` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D03_seed143_init1.mp4` | 没抓到但是触发扰动，推测是这个摩卡壶倒在这个电磁炉的范围之内了，然后就判定应该出现临时占用物体 |
| `libero_10/task2/D04/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D04_seed142_init0.mp4` | - |
| `libero_10/task2/D04/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D04_seed143_init1.mp4` | - |
| `libero_10/task2/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D05_seed142_init0.mp4` | 没有找到，未触发扰动 |
| `libero_10/task2/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_D05_seed143_init1.mp4` | 没有找到，未触发扰动 |
| `libero_10/task2/S09/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task2_S09_seed142_init0.mp4` | - |
| `libero_10/task2/S09/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task2_S09_seed143_init1.mp4` | - |
| `libero_10/task2/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_S10_seed142_init0.mp4` | - |
| `libero_10/task2/S10/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task2_S10_seed143_init1.mp4` | - |
| `libero_10/task2/S11/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PENDING` | `-` | `data/videos_0902/success/pi0_libero_10_task2_S11_seed142_init0.mp4` | 感觉这个干扰物不是算同类或视觉相似的 |
| `libero_10/task2/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PENDING` | `-` | `data/videos_0902/failure/pi0_libero_10_task2_S11_seed143_init1.mp4` | 感觉这个干扰物不是算同类或视觉相似的 |
| `libero_10/task3/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D03_seed142_init0.mp4` | - |
| `libero_10/task3/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D03_seed143_init1.mp4` | - |
| `libero_10/task3/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D05_seed142_init0.mp4` | - |
| `libero_10/task3/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D05_seed143_init1.mp4` | - |
| `libero_10/task3/D15/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D15_seed142_init0.mp4` | - |
| `libero_10/task3/D15/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D15_seed143_init1.mp4` | - |
| `libero_10/task3/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D20_seed142_init0.mp4` | - |
| `libero_10/task3/D20/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_D20_seed143_init1.mp4` | - |
| `libero_10/task3/S10/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task3_S10_seed142_init0.mp4` | - |
| `libero_10/task3/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_S10_seed143_init1.mp4` | - |
| `libero_10/task3/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_S11_seed142_init0.mp4` | - |
| `libero_10/task3/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task3_S11_seed143_init1.mp4` | - |
| `libero_10/task4/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `ISSUE` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D03_seed142_init0.mp4` | 第二个杯子放到接收区域了，但是没有出现临时占用的物体 |
| `libero_10/task4/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D03_seed143_init1.mp4` | - |
| `libero_10/task4/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D05_seed142_init0.mp4` | - |
| `libero_10/task4/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D05_seed143_init1.mp4` | - |
| `libero_10/task4/D06/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D06_seed142_init0.mp4` | - |
| `libero_10/task4/D06/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D06_seed143_init1.mp4` | - |
| `libero_10/task4/D12/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D12_seed142_init0.mp4` | - |
| `libero_10/task4/D12/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D12_seed143_init1.mp4` | - |
| `libero_10/task4/D13/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D13_seed142_init0.mp4` | - |
| `libero_10/task4/D13/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D13_seed143_init1.mp4` | - |
| `libero_10/task4/D21/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D21_seed142_init0.mp4` | - |
| `libero_10/task4/D21/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_D21_seed143_init1.mp4` | - |
| `libero_10/task4/S06/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S06_seed142_init0.mp4` | - |
| `libero_10/task4/S06/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S06_seed143_init1.mp4` | - |
| `libero_10/task4/S08/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S08_seed142_init0.mp4` | - |
| `libero_10/task4/S08/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/success/pi0_libero_10_task4_S08_seed143_init1.mp4` | - |
| `libero_10/task4/S09/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S09_seed142_init0.mp4` | - |
| `libero_10/task4/S09/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S09_seed143_init1.mp4` | - |
| `libero_10/task4/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S10_seed142_init0.mp4` | - |
| `libero_10/task4/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S10_seed143_init1.mp4` | - |
| `libero_10/task4/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S11_seed142_init0.mp4` | - |
| `libero_10/task4/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `-` | `data/videos_0902/failure/pi0_libero_10_task4_S11_seed143_init1.mp4` | - |

### 下一轮必须重新 rollout

下列组在 R004 中至少有一次 `ISSUE` 或 `PENDING`。下一轮应整组重跑两次尝试，不能只补其中一条；动态扰动需保证事件实际触发并提供可观察证据。

| 优先级 | Task | Case | 本轮结论 | 需要修复或验证的问题 | 下一轮目标 |
|---|---:|---|---|---|---|
| `P0` | 0 | `D02` | 错误/认可 | 扰动没有触发 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 0 | `D03` | 存疑/存疑 | 第一次没有抓到，没有触发占用的这个扰动 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 1 | `D14` | 存疑/存疑 | 肉眼看不太出来 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 1 | `S06` | 错误/错误 | 替换的这个同类型实例大于机械臂夹爪的最大限度，任务不可能成功，不太合理，应该替换个大小差不多的吧 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 2 | `D03` | 存疑/错误 | 没抓到，没有触发扰动；没抓到但是触发扰动，推测是这个摩卡壶倒在这个电磁炉的范围之内了，然后就判定应该出现临时占用物体 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 2 | `D05` | 存疑/存疑 | 没有找到，未触发扰动 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 2 | `S11` | 存疑/存疑 | 感觉这个干扰物不是算同类或视觉相似的 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 4 | `D03` | 错误/认可 | 第二个杯子放到接收区域了，但是没有出现临时占用的物体 | 修复后 R005，两次 rollout 均需 PASS |

#### R005 精确 key 清单

- `libero_10/task0/D02/seed142/init0`；`libero_10/task0/D02/seed143/init1`。
- `libero_10/task0/D03/seed142/init0`；`libero_10/task0/D03/seed143/init1`。
- `libero_10/task1/D14/seed142/init0`；`libero_10/task1/D14/seed143/init1`。
- `libero_10/task1/S06/seed142/init0`；`libero_10/task1/S06/seed143/init1`。
- `libero_10/task2/D03/seed142/init0`；`libero_10/task2/D03/seed143/init1`。
- `libero_10/task2/D05/seed142/init0`；`libero_10/task2/D05/seed143/init1`。
- `libero_10/task2/S11/seed142/init0`；`libero_10/task2/S11/seed143/init1`。
- `libero_10/task4/D03/seed142/init0`；`libero_10/task4/D03/seed143/init1`。

### 本轮问题归纳

- `D03`：task0、task2、task4 仍有未触发、误触发或接收区域占用不正确的问题。
- `S06`：task1 替换物体过大，超出夹爪合理抓取范围。
- `D05`：task2 两次都未观察到运输路径障碍物扰动。
- `D14`：task1 动作丢失/重复现象肉眼不明显，保留存疑。
- `S11`：task2 新增干扰物与目标不够同类或视觉相似，保留存疑。
- `D02`：task0 有一次未观察到接收器移动扰动。
---

## R005 定向复审记录

> 负责人：huang<br>
> 审核日期：2026-09-06<br>
> 数据批次：`0906rollout` / `pi0-review-final-20260905-e9c8d10`<br>
> rollout commit：`e9c8d10677e102f6ec12fb7257d4a6e29225e2f6`

### 范围与证据

本轮覆盖 `libero_10/task0-task4` 中源批次实际提供的 44 个 task/case 组、88 个独立 rollout，每组包含 seed142/init0 与 seed143/init1 两次尝试。未出现在本批次中的稳定项不视为漏审。

- 结果文件 SHA-256：`275ba3705cdc8c7b411cdd6025e307f58cc1a8101b0e88b05c6991f8fa73b3d3`
- 原始结果：`human_review_results 0906.csv`
- 视频与 rollout 对应：同批次 `0906rollout/index.tsv`

### 审核结果汇总

| 结论 | 数量 | 占比 |
|---|---:|---:|
| 认可 | 80 | 90.9% |
| 错误 | 2 | 2.3% |
| 存疑 | 6 | 6.8% |
| 异常 | 0 | 0.0% |
| 合计 | 88 | 100.0% |

| Task | 组数 | PASS | ISSUE | PENDING | 本轮状态 |
|---:|---:|---:|---:|---:|---|
| 0 | 12 | 20 | 0 | 4 | D03、D18 存疑，其余通过 |
| 1 | 8 | 14 | 2 | 0 | S06 错误，其余通过 |
| 2 | 7 | 12 | 0 | 2 | D03 存疑，其余通过 |
| 3 | 6 | 12 | 0 | 0 | 全部通过 |
| 4 | 11 | 22 | 0 | 0 | 全部通过 |

### 非认可项与处置

| Task | Case | 尝试 | 策略结果 | 审核判定 | 备注 | 视频证据 | 后续处置 |
|---:|---|---:|---|---|---|---|---|
| 0 | `D03` | 1 | `FAILURE` | `PENDING` | 没有抓到，没有触发扰动 | `data/videos_0906/failure/pi0_libero_10_task0_D03_seed142_init0.mp4` | 需先保证抓取成功，再验证动态扰动是否触发 |
| 0 | `D03` | 2 | `FAILURE` | `PENDING` | 没有抓到，没有触发扰动 | `data/videos_0906/failure/pi0_libero_10_task0_D03_seed143_init1.mp4` | 需先保证抓取成功，再验证动态扰动是否触发 |
| 0 | `D18` | 1 | `FAILURE` | `PENDING` | 没有抓到，没有触发扰动 | `data/videos_0906/failure/pi0_libero_10_task0_D18_seed142_init0.mp4` | 需先保证抓取成功，再验证掉落恢复扰动是否触发 |
| 0 | `D18` | 2 | `FAILURE` | `PENDING` | 没有抓到，没有触发扰动 | `data/videos_0906/failure/pi0_libero_10_task0_D18_seed143_init1.mp4` | 需先保证抓取成功，再验证掉落恢复扰动是否触发 |
| 1 | `S06` | 1 | `FAILURE` | `ISSUE` | 替换的新实例太大了，大于夹抓的最大限度，不可能抓到的 | `data/videos_0906/failure/pi0_libero_10_task1_S06_seed142_init0.mp4` | 修复替换资产尺寸后进入 R006 复测 |
| 1 | `S06` | 2 | `FAILURE` | `ISSUE` | 替换的新实例太大了，大于夹抓的最大限度，不可能抓到的 | `data/videos_0906/failure/pi0_libero_10_task1_S06_seed143_init1.mp4` | 修复替换资产尺寸后进入 R006 复测 |
| 2 | `D03` | 1 | `FAILURE` | `PENDING` | 没有抓到，未触发扰动 | `data/videos_0906/failure/pi0_libero_10_task2_D03_seed142_init0.mp4` | 需先保证抓取成功，再验证动态扰动是否触发 |
| 2 | `D03` | 2 | `FAILURE` | `PENDING` | 没有抓到，未触发扰动 | `data/videos_0906/failure/pi0_libero_10_task2_D03_seed143_init1.mp4` | 需先保证抓取成功，再验证动态扰动是否触发 |

### R004 问题项关闭情况

| Task/Case | R005 结论 | 后续 |
|---|---|---|
| `task0/D02` | 两次均通过 | 关闭 |
| `task0/D03` | attempt1 存疑；attempt2 存疑 | 未关闭，R006 继续复测 |
| `task1/D14` | 两次均通过 | 关闭 |
| `task1/S06` | attempt1 错误；attempt2 错误 | 未关闭，修复替换资产尺寸后 R006 复测 |
| `task2/D03` | attempt1 存疑；attempt2 存疑 | 未关闭，R006 继续复测 |
| `task2/D05` | 两次均通过 | 关闭 |
| `task2/S11` | 两次均通过 | 关闭 |
| `task4/D03` | 两次均通过 | 关闭 |

### R006 精确复测清单

下列组在 R005 中至少有一次 `ISSUE` 或 `PENDING`。下一轮应整组重跑两次尝试，不能只补其中一条。

| 优先级 | Task | Case | 本轮结论 | 需要修复或验证的问题 | 下一轮目标 |
|---|---:|---|---|---|---|
| `P1` | 0 | `D03` | 存疑/存疑 | 没有抓到，没有触发扰动 | 修复后 R006，两次 rollout 均需 PASS |
| `P1` | 0 | `D18` | 存疑/存疑 | 没有抓到，没有触发扰动 | 修复后 R006，两次 rollout 均需 PASS |
| `P0` | 1 | `S06` | 错误/错误 | 替换的新实例太大了，大于夹抓的最大限度，不可能抓到的 | 修复后 R006，两次 rollout 均需 PASS |
| `P1` | 2 | `D03` | 存疑/存疑 | 没有抓到，未触发扰动 | 修复后 R006，两次 rollout 均需 PASS |

#### R006 精确 key 清单

- `libero_10/task0/D03/seed142/init0`；`libero_10/task0/D03/seed143/init1`。
- `libero_10/task0/D18/seed142/init0`；`libero_10/task0/D18/seed143/init1`。
- `libero_10/task1/S06/seed142/init0`；`libero_10/task1/S06/seed143/init1`。
- `libero_10/task2/D03/seed142/init0`；`libero_10/task2/D03/seed143/init1`。

### 本轮问题归纳

- `D03`：task0、task2 仍因未抓到目标导致动态占用扰动未触发，保留存疑。
- `D18`：task0 新增存疑，两次均未先抓到目标，因此运输中掉落恢复扰动没有触发机会。
- `S06`：task1 替换实例仍过大，超出夹爪合理抓取范围，问题未解决。
- R004 中的 `D02`、`D14`、`D05`、`S11`、`task4/D03` 本轮已通过，可关闭。
