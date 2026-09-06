# libero_object 第 5 轮审核结果（0906rollout）

## 审核信息

- 审核日期：`2026-09-06`
- 记录日期：`2026-09-07`
- 审核人：`ShiinaMahiruOvO`
- 数据批次：`0906rollout`
- 源代码提交：`e9c8d10677e102f6ec12fb7257d4a6e29225e2f6`
- Manifest 版本：`libero-pro2.0-1706-v1`
- 审核范围：第 4 轮中标记为 `unsure` 的 `libero_object` 复测项
- 原始审核结果：`human_review_results.csv`
- CSV SHA-256：`6a5b0ba507fa2138eb346881644cdab448fa183f9136f5e709f962c14ce21b96`

## 结果概述

上一轮共有 57 条存疑记录。本轮生成并审核了其中 56 条视频，另有 1 条因环境创建失败未生成视频。本轮 56 条均已完成人工审核，其中 51 条认可、5 条仍存疑，无错误或视频异常记录。

| 统计项 | 数量 |
|---|---:|
| 上一轮待复测 | 57 |
| 本轮可审核视频 | 56 |
| 已审核 | 56 |
| 认可（correct） | 51 |
| 存疑（unsure） | 5 |
| 错误（wrong） | 0 |
| 视频异常（video_issue） | 0 |
| 环境创建失败 | 1 |

## Case 汇总

| Case | 本轮视频 | 认可 | 存疑 | 结论 |
|---|---:|---:|---:|---|
| `D02` | 2 | 1 | 1 | 仍有一次扰动未触发，问题未完全解决。 |
| `D03` | 9 | 5 | 4 | task1、task6 的四次复测仍被策略判定为成功，需要确认占用扰动和成功判定是否有效。另有一次环境创建失败。 |
| `D10` | 8 | 8 | 0 | 本轮复测项全部认可。 |
| `D14` | 20 | 20 | 0 | 本轮复测项全部认可。 |
| `D15` | 3 | 3 | 0 | 本轮复测项全部认可。 |
| `S05` | 14 | 14 | 0 | 本轮复测项全部认可。 |

## 仍存疑记录

| Task | Case | Attempt | 策略结果 | 审核备注 | 视频证据 |
|---:|---|---:|---|---|---|
| 1 | `D02` | 2 | `FAILURE` | 没有触发扰动。 | `0906rollout/failure/pi0_libero_object_task1_D02_seed143_init1.mp4` |
| 1 | `D03` | 1 | `SUCCESS` | 这个依然被认为是成功的。 | `0906rollout/success/pi0_libero_object_task1_D03_seed142_init0.mp4` |
| 1 | `D03` | 2 | `SUCCESS` | 这个依然被认为是成功的。 | `0906rollout/success/pi0_libero_object_task1_D03_seed143_init1.mp4` |
| 6 | `D03` | 1 | `SUCCESS` | 这个依然被认定是成功的。 | `0906rollout/success/pi0_libero_object_task6_D03_seed142_init0.mp4` |
| 6 | `D03` | 2 | `SUCCESS` | 这个依然被认定是成功的。 | `0906rollout/success/pi0_libero_object_task6_D03_seed143_init1.mp4` |

## 未生成视频

| Task | Case | Seed / Init | 状态 | 说明 |
|---:|---|---|---|---|
| 7 | `D03` | `143 / 1` | `ENVIRONMENT_CREATION_FAILED` | 环境无法初始化，未生成视频，因此本轮无法审核。 |

## 后续处理建议

- `D02`：复查 task1 / seed143 / init1 的触发条件；只有抓取后接收器移动实际发生，才可计为通过。
- `D03`：重点复查 task1 和 task6 的占用位置、持续时间及成功判定逻辑，确认障碍物存在时任务不应被错误判定为成功。
- `D03` task7：修复环境创建失败后补跑 seed143 / init1。
- `D10、D14、D15、S05`：本轮复测项均已认可，可按项目的连续多轮规则继续累计，不应仅凭本轮一次通过直接标记为稳定。
