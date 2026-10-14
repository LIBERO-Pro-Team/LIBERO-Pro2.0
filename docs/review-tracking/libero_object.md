# libero_object 多轮审核记录

## Suite 信息

- manifest 条目数：430
- 基础任务数：10
- 默认 seed/init：`143/0`
- 当前状态：已录入第 3 轮 suite 级人工审核反馈，并在本文件末尾合并第 4 轮（0902rollout）200 条审核结果；R3 的 case 级反馈不据此推测展开到具体 task/seed。

## 基础任务索引

| Task ID | Task Name |
|---:|---|
| 0 | `pick_up_the_alphabet_soup_and_place_it_in_the_basket` |
| 1 | `pick_up_the_cream_cheese_and_place_it_in_the_basket` |
| 2 | `pick_up_the_salad_dressing_and_place_it_in_the_basket` |
| 3 | `pick_up_the_bbq_sauce_and_place_it_in_the_basket` |
| 4 | `pick_up_the_ketchup_and_place_it_in_the_basket` |
| 5 | `pick_up_the_tomato_sauce_and_place_it_in_the_basket` |
| 6 | `pick_up_the_butter_and_place_it_in_the_basket` |
| 7 | `pick_up_the_milk_and_place_it_in_the_basket` |
| 8 | `pick_up_the_chocolate_pudding_and_place_it_in_the_basket` |
| 9 | `pick_up_the_orange_juice_and_place_it_in_the_basket` |

## 第 3 轮 Suite 级审核反馈

- 日期：`2026-09-02`
- 审核人：`ShiinaMahiruOvO`
- 审核范围：`libero_object` 第 3 轮 rollout 视频
- 记录原则：以下内容是跨视频观察到的 case 级共性问题。由于原始反馈未绑定具体 task、seed/init 和视频路径，本节只建立问题与复测范围，不把结论推测写入某个 Review Key。

| 优先级 | Case | 审核判定 | 问题类型 | 问题说明 | 建议复测条件 |
|---:|---|---|---|---|---|
| `P0` | `D02` | `ISSUE` | `not_triggered` | “抓取后接收器突然移动”依赖策略先完成抓取；部分任务未成功抓取，因此无法观察或验证扰动。 | 动态事件必须实际触发，并提供接收器移动前后的事件日志或画面证据。未触发的 rollout 不计为 PASS。 |
| `P0` | `D03` | `ISSUE` | `duration_and_collision` | 临时占用障碍物持续时间不足；障碍物消失后策略仍能完成任务，扰动约束不充分。部分任务还存在障碍物穿模。 | 延长占用时间，确保扰动覆盖关键放置阶段；验证障碍物与接收器、目标物和机器人均无穿透。 |
| `P1` | `S02` | `ISSUE` | `weak_magnitude` | 对较小目标物，接收器或固定装置的位姿偏移过小；策略即使不适应变化也可能照常成功。 | 按接收器尺度设置具有区分度的偏移，同时验证可达、无碰撞且任务仍可完成。 |
| `P1` | `S05` | `ISSUE` | `ineffective_occlusion` | 用于限制接近方向或运输路径的遮挡物没有产生有效遮挡或路径约束。 | 调整遮挡物尺寸和位置，确认其确实限制原路径，同时至少保留一条安全可达路径。 |
| `P1` | `D10` | `PENDING` | `temporal_artifact` | 视频表现为短暂卡顿，下一帧目标物立即出现在机械臂上，时间连续性异常；无法确认这是预期丢帧/重复帧/冻结帧，还是录制或状态同步问题。 | 同步提供送入策略的帧序列、扰动起止帧和原始状态日志，确认物体状态没有被跳变或错误回放。 |
| `P1` | `D14` | `PENDING` | `not_observable_from_video` | 动作命令丢失或重复从普通 rollout 视频中无法可靠辨识。 | 叠加动作序号、丢失/重复事件及触发窗口，或提供对应动作日志后复核。 |
| `P1` | `D15` | `PENDING` | `not_observable_from_video` | 过期动作块或重规划中断从普通 rollout 视频中无法可靠辨识。 | 提供 action chunk ID、chunk 生成时间、执行时间和重规划事件日志后复核。 |
| `P1` | `D20` | `PENDING` | `definition_and_visibility` | D20 的实现定义为：机器人运动过程中，施加一次满足关节限位、无新增碰撞且仍可达的关节位移，用于模拟碰撞引起的机器人姿态偏移；但当前视频中难以确认该位移是否触发及其幅度。 | 在视频中标出触发时刻，并记录扰动前后关节角、末端位姿和位移量；未提供证据时保持 PENDING。 |

### 第 3 轮复测范围

| 优先级 | 范围 | 复测原因 | 目标轮次 | 负责人 |
|---:|---|---|---|---|
| `P0` | `libero_object/*/D02` | 必须成功进入抓取后阶段并确认接收器移动实际触发 | `R004` | `-` |
| `P0` | `libero_object/*/D03` | 延长障碍物持续时间并消除穿模 | `R004` | `-` |
| `P1` | `libero_object/*/S02` | 增大对小物体任务有实际影响的接收器位姿偏移 | `R004` | `-` |
| `P1` | `libero_object/*/S05` | 验证遮挡物形成有效但可恢复的路径约束 | `R004` | `-` |
| `P1` | `libero_object/*/D10` | 排查卡顿后物体状态跳变，并补充输入帧证据 | `R004` | `-` |
| `P1` | `libero_object/*/D14` | 补充动作丢失/重复日志和触发标记 | `R004` | `-` |
| `P1` | `libero_object/*/D15` | 补充过期 action chunk 和重规划日志 | `R004` | `-` |
| `P1` | `libero_object/*/D20` | 补充关节位移及末端位姿变化证据 | `R004` | `-` |

---

## R004 审核结果（0902rollout）

### 审核信息

- 日期：`2026-09-03`
- 审核人：`ShiinaMahiruOvO`
- 审核范围：`0902rollout` 中的 `libero_object`
- 审核视频：`200`
- 覆盖任务：`task0`–`task9`
- 覆盖 case：`D02、D03、D10、D14、D15、D20、S02、S05、S10、S11`
- 原始审核结果：`human_review_results.csv`
- CSV SHA-256：`8e0ef48d916f565e78a9f7d59656426d1a29fa77954794e2df6f971438b1902a`

### 结果汇总

| 统计项 | 数量 |
|---|---:|
| 已审核 | 200 |
| 认可（correct） | 143 |
| 存疑（unsure） | 57 |
| 错误（wrong） | 0 |
| 视频异常（video_issue） | 0 |
| 带备注 | 57 |

### Case 汇总

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

### 存疑记录

以下记录均来自 CSV 中 `human_decision=unsure` 的条目；路径为本轮审核所使用的视频证据。

#### D02：扰动未触发

- task0 / attempt2：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task0_D02_seed143_init1.mp4`
- task1 / attempt2：没有触发扰动 — `0902rollout/failure/pi0_libero_object_task1_D02_seed143_init1.mp4`

#### D03：占用或遮挡无效

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

#### D10：时间连续性异常

以下 8 条（task0、task1、task4、task5 的两次 attempt）备注相同：视频效果为“卡一下，然后下一帧物体立刻出现在机械臂上面，有点奇怪似乎”。

- `task0/{attempt1,attempt2}`
- `task1/{attempt1,attempt2}`
- `task4/{attempt1,attempt2}`
- `task5/{attempt1,attempt2}`

对应视频路径分别为 `0902rollout/{success|failure}/pi0_libero_object_task{0,1,4,5}_D10_seed{142,143}_init{0,1}.mp4`，具体 success/failure 以 CSV 为准。

#### D14：视频不可确认

- task0–task9 的 attempt1、attempt2 共 20 条：这个似乎从视频上面看不出来。

#### D15：视频不可确认

- task6 / attempt1：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task6_D15_seed142_init0.mp4`
- task6 / attempt2：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task6_D15_seed143_init1.mp4`
- task7 / attempt2：这个似乎从视频上面看不出来 — `0902rollout/success/pi0_libero_object_task7_D15_seed143_init1.mp4`

#### S05：遮挡效果不足

- task3 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task4 / attempt1、attempt2：这个似乎从视频上面看不出来。
- task5 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task6 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task7 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task8 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。
- task9 / attempt1、attempt2：遮挡物体没有产生有效的遮挡效果。

### 后续建议

- `D02`：确保策略先成功抓取，再触发接收器移动；未触发的样本不能计为 PASS。
- `D03`：延长障碍物占用时间，确保遮挡物实际出现并覆盖关键放置阶段，同时检查碰撞几何和穿模。
- `D10`：补充输入帧序列或状态日志，区分丢帧/冻结帧与物体状态跳变。
- `D14`、`D15`：补充动作序号、action chunk 和重规划日志，不能只凭视频判定。
- `S05`：重新调整遮挡物位置和尺寸，确认能产生有效遮挡且仍保留安全可达路径。
