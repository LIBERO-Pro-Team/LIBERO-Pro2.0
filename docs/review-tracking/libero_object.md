# libero_object 多轮审核记录

## Suite 信息

- manifest 条目数：430
- 基础任务数：10
- 默认 seed/init：`143/0`
- 当前状态：已录入第 3 轮 suite 级人工审核反馈；由于本轮反馈按 case 汇总、未逐条提供 task/seed 证据，审核总表和逐轮日志不据此推测展开。

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
