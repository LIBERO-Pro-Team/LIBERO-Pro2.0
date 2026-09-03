# libero_object 第 4 轮审核结果（0902rollout）

## 审核信息

- 日期：`2026-09-03`
- 审核人：`ShiinaMahiruOvO`
- 审核范围：`0902rollout` 中的 `libero_object`
- 审核视频：`200`
- 覆盖任务：`task0`–`task9`
- 覆盖 case：`D02、D03、D10、D14、D15、D20、S02、S05、S10、S11`
- 原始审核结果：`human_review_results.csv`
- CSV SHA-256：`8e0ef48d916f565e78a9f7d59656426d1a29fa77954794e2df6f971438b1902a`

## 结果汇总

| 统计项 | 数量 |
|---|---:|
| 已审核 | 200 |
| 认可（correct） | 143 |
| 存疑（unsure） | 57 |
| 错误（wrong） | 0 |
| 视频异常（video_issue） | 0 |
| 带备注 | 57 |

## Case 汇总

| Case | 认可 | 存疑 | 主要问题 |
|---|---:|---:|---|
| `D02` | 18 | 2 | task0、task1 的 attempt 2 未触发扰动。 |
| `D03` | 10 | 10 | 未触发、障碍物未出现、遮挡物太小，任务仍可成功。 |
| `D10` | 12 | 8 | 视频短暂卡顿后物体下一帧直接出现在机械臂上，时间连续性异常。 |
| `D14` | 0 | 20 | 动作命令丢失或重复无法从视频确认。 |
| `D15` | 17 | 3 | 个别视频无法从画面确认过期动作块或重规划中断。 |
| `D20` | 20 | 0 | 本轮视频审核中未记录问题。 |
| `S02` | 20 | 0 | 本轮视频审核中未记录问题。 |
| `S05` | 6 | 14 | 多个任务中遮挡物没有产生有效遮挡；task4 两次尝试从视频也无法确认。 |
| `S10` | 20 | 0 | 本轮视频审核中未记录问题。 |
| `S11` | 20 | 0 | 本轮视频审核中未记录问题。 |

## 存疑记录

以下记录均来自 CSV 中 `human_decision=unsure` 的条目；路径为本轮审核所使用的视频证据。

### D02：扰动未触发

- task0 / attempt2：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task0_D02_seed143_init1.mp4`
- task1 / attempt2：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task1_D02_seed143_init1.mp4`

### D03：占用或遮挡无效

- task1 / attempt1：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task1_D03_seed142_init0.mp4`
- task1 / attempt2：遮挡物体太小，任务仍然能够成功 — `0902rollout/success/pi0_libero_object_task1_D03_seed143_init1.mp4`
- task3 / attempt1：障碍物没有出现 — `0902rollout/success/pi0_libero_object_task3_D03_seed142_init0.mp4`
- task3 / attempt2：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task3_D03_seed143_init1.mp4`
- task6 / attempt1：遮挡物体太小，任务仍然能够成功 — `0902rollout/success/pi0_libero_object_task6_D03_seed142_init0.mp4`
- task6 / attempt2：遮挡物体太小，任务仍然能够成功 — `0902rollout/success/pi0_libero_object_task6_D03_seed143_init1.mp4`
- task7 / attempt1：没有出现遮挡物 — `0902rollout/success/pi0_libero_object_task7_D03_seed142_init0.mp4`
- task7 / attempt2：没有出现遮挡物 — `0902rollout/success/pi0_libero_object_task7_D03_seed143_init1.mp4`
- task9 / attempt1：接受物体没有被占用 — `0902rollout/success/pi0_libero_object_task9_D03_seed142_init0.mp4`
- task9 / attempt2：接受物体没有被占用 — `0902rollout/success/pi0_libero_object_task9_D03_seed143_init1.mp4`

### D10：时间连续性异常

以下 8 条（task0、task1、task4、task5 的两次 attempt）备注相同：视频效果为“卡一下，然后下一帧物体立刻出现在机械臂上面，有点奇怪似乎”。

- `task0/{attempt1,attempt2}`
- `task1/{attempt1,attempt2}`
- `task4/{attempt1,attempt2}`
- `task5/{attempt1,attempt2}`

对应视频路径分别为 `0902rollout/{success|failure}/pi0_libero_object_task{0,1,4,5}_D10_seed{142,143}_init{0,1}.mp4`，具体 success/failure 以 CSV 为准。

### D14：视频不可确认

- task0–task9 的 attempt1、attempt2 共 20 条：这个似乎从视频上面看不出来。

### D15：视频不可确认

- task6 / attempt1：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task6_D15_seed142_init0.mp4`
- task6 / attempt2：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task6_D15_seed143_init1.mp4`
- task7 / attempt2：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task7_D15_seed143_init1.mp4`

### S05：遮挡效果不足

- task3 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task4 / attempt1、attempt2：这个似乎从视频上面看不出来。
- task5 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task6 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task7 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task8 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task9 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。

## 后续建议

- `D02`：确保策略先成功抓取，再触发接收器移动；未触发的样本不能计为 PASS。
- `D03`：延长障碍物占用时间，确保遮挡物实际出现并覆盖关键放置阶段，同时检查碰撞几何和穿模。
- `D10`：补充输入帧序列或状态日志，区分丢帧/冻结帧与物体状态跳变。
- `D14`、`D15`：补充动作序号、action chunk 和重规划日志，不能只凭视频判定。
- `S05`：重新调整遮挡物位置和尺寸，确认能产生有效遮挡且仍保留安全可达路径。
