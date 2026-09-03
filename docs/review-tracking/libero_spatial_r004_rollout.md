# libero_spatial R004 完整 rollout 执行清单

> 本文件是 R004 的唯一执行清单。请勿从 `libero_spatial.md` 的审核总表或自动复测候选表推导生成范围。

- Suite：`libero_spatial`
- Manifest：`libero-pro2.0-1706-v1`
- Task-case：`89` 组
- Episode / 视频：`178` 条
- 固定 seed/init：`142/0`、`143/1`
- D19：当前 manifest 不包含，不生成
- 0902 已出现的重合项目：仍按本清单重新生成，不做差集去重

## 执行要求

1. 严格生成下表全部 178 条，不额外读取其他候选表。
2. task6 先检查 BASE，但无论执行顺序如何，task6 的全部 42 个扰动均保留在本清单。
3. 结果包需记录 source commit、manifest version、模型/checkpoint 及 adapter 版本。
4. 打包前校验：89 个唯一 task-case，每组恰好包含两个 seed/init，且没有清单外条目。

## 范围汇总

| Case | Tasks | task-case 数 | 视频数 |
|---|---|---:|---:|
| `BASE` | `6` | 1 | 2 |
| `S01` | `3, 5, 6` | 3 | 6 |
| `S02` | `6` | 1 | 2 |
| `S03` | `0, 1, 2, 3, 4, 5, 6, 7, 8, 9` | 10 | 20 |
| `S04` | `0, 1, 2, 3, 5, 6, 7` | 7 | 14 |
| `S05` | `6` | 1 | 2 |
| `S06` | `0, 2, 3, 4, 5, 6, 7, 8, 9` | 9 | 18 |
| `S07` | `6` | 1 | 2 |
| `S08` | `6` | 1 | 2 |
| `S09` | `6` | 1 | 2 |
| `S10` | `0, 1, 2, 3, 4, 6, 7, 9` | 8 | 16 |
| `S11` | `0, 1, 3, 4, 5, 6, 7, 8, 9` | 9 | 18 |
| `S12-S22` | `6` | 11 | 22 |
| `D01` | `3, 6` | 2 | 4 |
| `D02` | `6` | 1 | 2 |
| `D03` | `0, 1, 3, 6, 8, 9` | 6 | 12 |
| `D04-D18` | `6` | 15 | 30 |
| `D20-D21` | `6` | 2 | 4 |
| **合计** |  | **89** | **178** |

## 逐条执行清单

| # | Review Key | Priority | 原因 |
|---:|---|---:|---|
| 1 | `libero_spatial/task6/BASE/seed142/init0` | `P0` | 验证 task6 基线是否恢复 |
| 2 | `libero_spatial/task6/BASE/seed143/init1` | `P0` | 验证 task6 基线是否恢复 |
| 3 | `libero_spatial/task3/S01/seed142/init0` | `P0` | 支撑关系修复；task6 全量回归 |
| 4 | `libero_spatial/task3/S01/seed143/init1` | `P0` | 支撑关系修复；task6 全量回归 |
| 5 | `libero_spatial/task5/S01/seed142/init0` | `P0` | 支撑关系修复；task6 全量回归 |
| 6 | `libero_spatial/task5/S01/seed143/init1` | `P0` | 支撑关系修复；task6 全量回归 |
| 7 | `libero_spatial/task6/S01/seed142/init0` | `P0` | 支撑关系修复；task6 全量回归 |
| 8 | `libero_spatial/task6/S01/seed143/init1` | `P0` | 支撑关系修复；task6 全量回归 |
| 9 | `libero_spatial/task6/S02/seed142/init0` | `P1` | task6 全量回归 |
| 10 | `libero_spatial/task6/S02/seed143/init1` | `P1` | task6 全量回归 |
| 11 | `libero_spatial/task0/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 12 | `libero_spatial/task0/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 13 | `libero_spatial/task1/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 14 | `libero_spatial/task1/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 15 | `libero_spatial/task2/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 16 | `libero_spatial/task2/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 17 | `libero_spatial/task3/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 18 | `libero_spatial/task3/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 19 | `libero_spatial/task4/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 20 | `libero_spatial/task4/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 21 | `libero_spatial/task5/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 22 | `libero_spatial/task5/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 23 | `libero_spatial/task6/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 24 | `libero_spatial/task6/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 25 | `libero_spatial/task7/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 26 | `libero_spatial/task7/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 27 | `libero_spatial/task8/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 28 | `libero_spatial/task8/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 29 | `libero_spatial/task9/S03/seed142/init0` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 30 | `libero_spatial/task9/S03/seed143/init1` | `P0` | 接收物垫高的遮挡、碰撞与可达性全任务复测 |
| 31 | `libero_spatial/task0/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 32 | `libero_spatial/task0/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 33 | `libero_spatial/task1/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 34 | `libero_spatial/task1/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 35 | `libero_spatial/task2/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 36 | `libero_spatial/task2/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 37 | `libero_spatial/task3/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 38 | `libero_spatial/task3/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 39 | `libero_spatial/task5/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 40 | `libero_spatial/task5/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 41 | `libero_spatial/task6/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 42 | `libero_spatial/task6/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 43 | `libero_spatial/task7/S04/seed142/init0` | `P0` | 交换/重排异常复测 |
| 44 | `libero_spatial/task7/S04/seed143/init1` | `P0` | 交换/重排异常复测 |
| 45 | `libero_spatial/task6/S05/seed142/init0` | `P1` | task6 全量回归 |
| 46 | `libero_spatial/task6/S05/seed143/init1` | `P1` | task6 全量回归 |
| 47 | `libero_spatial/task0/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 48 | `libero_spatial/task0/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 49 | `libero_spatial/task2/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 50 | `libero_spatial/task2/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 51 | `libero_spatial/task3/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 52 | `libero_spatial/task3/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 53 | `libero_spatial/task4/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 54 | `libero_spatial/task4/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 55 | `libero_spatial/task5/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 56 | `libero_spatial/task5/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 57 | `libero_spatial/task6/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 58 | `libero_spatial/task6/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 59 | `libero_spatial/task7/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 60 | `libero_spatial/task7/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 61 | `libero_spatial/task8/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 62 | `libero_spatial/task8/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 63 | `libero_spatial/task9/S06/seed142/init0` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 64 | `libero_spatial/task9/S06/seed143/init1` | `P0` | 替换实例尺寸、抓取与支撑关系复测 |
| 65 | `libero_spatial/task6/S07/seed142/init0` | `P1` | task6 全量回归 |
| 66 | `libero_spatial/task6/S07/seed143/init1` | `P1` | task6 全量回归 |
| 67 | `libero_spatial/task6/S08/seed142/init0` | `P1` | task6 全量回归 |
| 68 | `libero_spatial/task6/S08/seed143/init1` | `P1` | task6 全量回归 |
| 69 | `libero_spatial/task6/S09/seed142/init0` | `P1` | task6 全量回归 |
| 70 | `libero_spatial/task6/S09/seed143/init1` | `P1` | task6 全量回归 |
| 71 | `libero_spatial/task0/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 72 | `libero_spatial/task0/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 73 | `libero_spatial/task1/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 74 | `libero_spatial/task1/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 75 | `libero_spatial/task2/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 76 | `libero_spatial/task2/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 77 | `libero_spatial/task3/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 78 | `libero_spatial/task3/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 79 | `libero_spatial/task4/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 80 | `libero_spatial/task4/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 81 | `libero_spatial/task6/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 82 | `libero_spatial/task6/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 83 | `libero_spatial/task7/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 84 | `libero_spatial/task7/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 85 | `libero_spatial/task9/S10/seed142/init0` | `P0` | 无关杂物有效性复测 |
| 86 | `libero_spatial/task9/S10/seed143/init1` | `P0` | 无关杂物有效性复测 |
| 87 | `libero_spatial/task0/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 88 | `libero_spatial/task0/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 89 | `libero_spatial/task1/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 90 | `libero_spatial/task1/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 91 | `libero_spatial/task3/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 92 | `libero_spatial/task3/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 93 | `libero_spatial/task4/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 94 | `libero_spatial/task4/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 95 | `libero_spatial/task5/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 96 | `libero_spatial/task5/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 97 | `libero_spatial/task6/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 98 | `libero_spatial/task6/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 99 | `libero_spatial/task7/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 100 | `libero_spatial/task7/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 101 | `libero_spatial/task8/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 102 | `libero_spatial/task8/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 103 | `libero_spatial/task9/S11/seed142/init0` | `P0` | 相似物几何与放置有效性复测 |
| 104 | `libero_spatial/task9/S11/seed143/init1` | `P0` | 相似物几何与放置有效性复测 |
| 105 | `libero_spatial/task6/S12/seed142/init0` | `P1` | task6 全量回归 |
| 106 | `libero_spatial/task6/S12/seed143/init1` | `P1` | task6 全量回归 |
| 107 | `libero_spatial/task6/S13/seed142/init0` | `P1` | task6 全量回归 |
| 108 | `libero_spatial/task6/S13/seed143/init1` | `P1` | task6 全量回归 |
| 109 | `libero_spatial/task6/S14/seed142/init0` | `P1` | task6 全量回归 |
| 110 | `libero_spatial/task6/S14/seed143/init1` | `P1` | task6 全量回归 |
| 111 | `libero_spatial/task6/S15/seed142/init0` | `P1` | task6 全量回归 |
| 112 | `libero_spatial/task6/S15/seed143/init1` | `P1` | task6 全量回归 |
| 113 | `libero_spatial/task6/S16/seed142/init0` | `P1` | task6 全量回归 |
| 114 | `libero_spatial/task6/S16/seed143/init1` | `P1` | task6 全量回归 |
| 115 | `libero_spatial/task6/S17/seed142/init0` | `P1` | task6 全量回归 |
| 116 | `libero_spatial/task6/S17/seed143/init1` | `P1` | task6 全量回归 |
| 117 | `libero_spatial/task6/S18/seed142/init0` | `P1` | task6 全量回归 |
| 118 | `libero_spatial/task6/S18/seed143/init1` | `P1` | task6 全量回归 |
| 119 | `libero_spatial/task6/S19/seed142/init0` | `P1` | task6 全量回归 |
| 120 | `libero_spatial/task6/S19/seed143/init1` | `P1` | task6 全量回归 |
| 121 | `libero_spatial/task6/S20/seed142/init0` | `P1` | task6 全量回归 |
| 122 | `libero_spatial/task6/S20/seed143/init1` | `P1` | task6 全量回归 |
| 123 | `libero_spatial/task6/S21/seed142/init0` | `P1` | task6 全量回归 |
| 124 | `libero_spatial/task6/S21/seed143/init1` | `P1` | task6 全量回归 |
| 125 | `libero_spatial/task6/S22/seed142/init0` | `P1` | task6 全量回归 |
| 126 | `libero_spatial/task6/S22/seed143/init1` | `P1` | task6 全量回归 |
| 127 | `libero_spatial/task3/D01/seed142/init0` | `P0` | 支撑关系与触发验证 |
| 128 | `libero_spatial/task3/D01/seed143/init1` | `P0` | 支撑关系与触发验证 |
| 129 | `libero_spatial/task6/D01/seed142/init0` | `P0` | 支撑关系与触发验证 |
| 130 | `libero_spatial/task6/D01/seed143/init1` | `P0` | 支撑关系与触发验证 |
| 131 | `libero_spatial/task6/D02/seed142/init0` | `P1` | task6 全量回归 |
| 132 | `libero_spatial/task6/D02/seed143/init1` | `P1` | task6 全量回归 |
| 133 | `libero_spatial/task0/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 134 | `libero_spatial/task0/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 135 | `libero_spatial/task1/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 136 | `libero_spatial/task1/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 137 | `libero_spatial/task3/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 138 | `libero_spatial/task3/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 139 | `libero_spatial/task6/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 140 | `libero_spatial/task6/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 141 | `libero_spatial/task8/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 142 | `libero_spatial/task8/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 143 | `libero_spatial/task9/D03/seed142/init0` | `P0` | 占位物落点、掉落与触发验证 |
| 144 | `libero_spatial/task9/D03/seed143/init1` | `P0` | 占位物落点、掉落与触发验证 |
| 145 | `libero_spatial/task6/D04/seed142/init0` | `P1` | task6 全量回归 |
| 146 | `libero_spatial/task6/D04/seed143/init1` | `P1` | task6 全量回归 |
| 147 | `libero_spatial/task6/D05/seed142/init0` | `P1` | task6 全量回归 |
| 148 | `libero_spatial/task6/D05/seed143/init1` | `P1` | task6 全量回归 |
| 149 | `libero_spatial/task6/D06/seed142/init0` | `P1` | task6 全量回归 |
| 150 | `libero_spatial/task6/D06/seed143/init1` | `P1` | task6 全量回归 |
| 151 | `libero_spatial/task6/D07/seed142/init0` | `P1` | task6 全量回归 |
| 152 | `libero_spatial/task6/D07/seed143/init1` | `P1` | task6 全量回归 |
| 153 | `libero_spatial/task6/D08/seed142/init0` | `P1` | task6 全量回归 |
| 154 | `libero_spatial/task6/D08/seed143/init1` | `P1` | task6 全量回归 |
| 155 | `libero_spatial/task6/D09/seed142/init0` | `P1` | task6 全量回归 |
| 156 | `libero_spatial/task6/D09/seed143/init1` | `P1` | task6 全量回归 |
| 157 | `libero_spatial/task6/D10/seed142/init0` | `P1` | task6 全量回归 |
| 158 | `libero_spatial/task6/D10/seed143/init1` | `P1` | task6 全量回归 |
| 159 | `libero_spatial/task6/D11/seed142/init0` | `P1` | task6 全量回归 |
| 160 | `libero_spatial/task6/D11/seed143/init1` | `P1` | task6 全量回归 |
| 161 | `libero_spatial/task6/D12/seed142/init0` | `P1` | task6 全量回归 |
| 162 | `libero_spatial/task6/D12/seed143/init1` | `P1` | task6 全量回归 |
| 163 | `libero_spatial/task6/D13/seed142/init0` | `P1` | task6 全量回归 |
| 164 | `libero_spatial/task6/D13/seed143/init1` | `P1` | task6 全量回归 |
| 165 | `libero_spatial/task6/D14/seed142/init0` | `P1` | task6 全量回归 |
| 166 | `libero_spatial/task6/D14/seed143/init1` | `P1` | task6 全量回归 |
| 167 | `libero_spatial/task6/D15/seed142/init0` | `P1` | task6 全量回归 |
| 168 | `libero_spatial/task6/D15/seed143/init1` | `P1` | task6 全量回归 |
| 169 | `libero_spatial/task6/D16/seed142/init0` | `P1` | task6 全量回归 |
| 170 | `libero_spatial/task6/D16/seed143/init1` | `P1` | task6 全量回归 |
| 171 | `libero_spatial/task6/D17/seed142/init0` | `P1` | task6 全量回归 |
| 172 | `libero_spatial/task6/D17/seed143/init1` | `P1` | task6 全量回归 |
| 173 | `libero_spatial/task6/D18/seed142/init0` | `P1` | task6 全量回归 |
| 174 | `libero_spatial/task6/D18/seed143/init1` | `P1` | task6 全量回归 |
| 175 | `libero_spatial/task6/D20/seed142/init0` | `P1` | task6 全量回归 |
| 176 | `libero_spatial/task6/D20/seed143/init1` | `P1` | task6 全量回归 |
| 177 | `libero_spatial/task6/D21/seed142/init0` | `P1` | task6 全量回归 |
| 178 | `libero_spatial/task6/D21/seed143/init1` | `P1` | task6 全量回归 |

