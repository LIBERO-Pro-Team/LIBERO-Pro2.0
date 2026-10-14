# Libero 10, Task 5~9 多轮审核记录

> 负责人：Junhao Wu<br>
> 范围：`libero_10/task5` ~ `libero_10/task9`<br>
> 判定口径：唯一键为 `suite/task_id/case_id/seed/init_state`；`PASS`、`ISSUE`、`PENDING` 与策略执行结果分开记录。连续 3 次实际审核为 `PASS` 才进入 `STABLE_3_NO_RETEST`。某轮没有该 key 时记为 `-`，既不算通过，也不打断已有连续通过计数。

## 最新轮次

- 2026-09-06 已完成 R005 问题项定向复审：39 组、78 个 rollout。
- R005 结果为 76 条 `PASS`、2 条 `PENDING`；唯一非 PASS 项为 `task8/D06` 的两次尝试。
- `task8/D06` 经人工确认不符合干扰物语义，后续舍弃该 task/case 组合，不再安排 rollout。
- 除上述舍弃项外，本轮所有审核项均已通过；`task5-task9` 当前没有需要进入 R006 的人工复测项。

## 负责范围

| Suite | Task | Task Name | 审核范围 |
|---|---:|---|---|
| libero_10 | 5 | `STUDY_SCENE1_pick_up_the_book_and_place_it_in_the_back_compartment_of_the_caddy` | BASE, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 |
| libero_10 | 6 | `LIVING_ROOM_SCENE6_put_the_white_mug_on_the_plate_and_put_the_chocolate_pudding_to_the_right_of_the_plate` | BASE, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 |
| libero_10 | 7 | `LIVING_ROOM_SCENE1_put_both_the_alphabet_soup_and_the_cream_cheese_box_in_the_basket` | BASE, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 |
| libero_10 | 8 | `KITCHEN_SCENE8_put_both_moka_pots_on_the_stove` | BASE, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 |
| libero_10 | 9 | `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it` | BASE, S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12, D13, D14, D15, D16, D17, D18, D19, D20, D21 |

## 审核轮次与证据

| 轮次 | 日期 | 范围 | 记录数 | 结果 CSV SHA-256 | rollout commit |
|---|---|---|---:|---|---|
| R001 | 2026-08-18 | 首轮已导出审核（D20 未纳入） | 420 | `9311c85a52b54b0c67f0113a4da172ffa31965384f6430e1f20c9deda4d66f28` | `-` |
| R001-补审 | 2026-08-22 | R001 问题项补充复审，不单独占用正式轮次；未出现的 key 记为未审核（-） | 76 | `cf6d823ad7c7525ec4257febf854472c8ed35b4c4645d1ba0a34cc4afa1b3e33` | `-` |
| R002 | 2026-08-27 | 第二轮全量审核 | 440 | `88b9da5ab45030711e51a59385121f71c862049a64930e9b177ee3c5fdc1d102` | `-` |
| R003 | 2026-09-01 | 第三轮全量审核；D19 本轮没有 rollout | 430 | `c5a5f94d23d9d18583b47791b450bf130d7300733f7c1586bae191c8f3ef2adf` | `e0fc1f8fa02fa0c3465042b6f85833311eccc614` |

证据文件名分别为各轮交付目录中的 `01_审核结果/human_review_results.csv`；rollout 的 seed、init state、视频相对路径与 episode ID 由同轮 `review_manifest.csv` 对齐。R003 的 D19 未提供 rollout，因此对应 key 显示 `-`。

## 每轮每个 Task 审核情况

| 轮次 | Task | 已审核 | PASS | ISSUE | PENDING | 策略成功 | 策略失败 |
|---|---:|---:|---:|---:|---:|---:|---:|
| R001 | 5 | 84 | 66 | 6 | 12 | 40 | 44 |
| R001 | 6 | 84 | 72 | 12 | 0 | 21 | 63 |
| R001 | 7 | 84 | 70 | 10 | 4 | 13 | 71 |
| R001 | 8 | 84 | 70 | 2 | 12 | 14 | 70 |
| R001 | 9 | 84 | 70 | 5 | 9 | 16 | 68 |
| R001-补审 | 5 | 20 | 13 | 3 | 4 | 1 | 19 |
| R001-补审 | 6 | 14 | 10 | 0 | 4 | 0 | 14 |
| R001-补审 | 7 | 14 | 6 | 0 | 8 | 1 | 13 |
| R001-补审 | 8 | 14 | 10 | 0 | 4 | 0 | 14 |
| R001-补审 | 9 | 14 | 5 | 0 | 9 | 0 | 14 |
| R002 | 5 | 88 | 75 | 3 | 10 | 44 | 44 |
| R002 | 6 | 88 | 84 | 0 | 4 | 13 | 75 |
| R002 | 7 | 88 | 84 | 0 | 4 | 13 | 75 |
| R002 | 8 | 88 | 77 | 0 | 11 | 0 | 88 |
| R002 | 9 | 88 | 78 | 0 | 10 | 18 | 70 |
| R003 | 5 | 86 | 82 | 3 | 1 | 49 | 37 |
| R003 | 6 | 86 | 81 | 3 | 2 | 19 | 67 |
| R003 | 7 | 86 | 83 | 1 | 2 | 7 | 79 |
| R003 | 8 | 86 | 77 | 2 | 7 | 9 | 77 |
| R003 | 9 | 86 | 78 | 3 | 5 | 22 | 64 |

## 当前总览

- 唯一 rollout key：440
- `STABLE_3_NO_RETEST`：346
- `RETEST`：63
- `ISSUE_OPEN`：31

| Task | Key 数 | 稳定免复测 | 继续复测 | 当前问题 |
|---:|---:|---:|---:|---:|
| 5 | 88 | 67 | 15 | 6 |
| 6 | 88 | 73 | 10 | 5 |
| 7 | 88 | 72 | 13 | 3 |
| 8 | 88 | 68 | 11 | 9 |
| 9 | 88 | 66 | 14 | 8 |

## 逐 key 审核总表

| Task | Case | Seed | Init | R001 | R001-补审 | R002 | R003 | 连续 PASS | 当前状态 | 最新策略结果 | 扰动触发 | 最新轮次 | 最新证据 | 未解决问题 |
|---:|---|---:|---:|---|---|---|---|---:|---|---|---|---|---|---|
| 5 | BASE | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b2b383785e459e68087cb2cd98f0a66a (videos/success/pi0_libero_10_task5_BASE_seed142_init0.mp4) | - |
| 5 | BASE | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_66cf536f6cda099576057db9b8de2fa0 (videos/failure/pi0_libero_10_task5_BASE_seed143_init1.mp4) | - |
| 5 | S01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_babbc19051ef579ab46f41979f227b4f (videos/failure/pi0_libero_10_task5_S01_seed142_init0.mp4) | - |
| 5 | S01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f4742ee457f69e934deeda45b3bb0ced (videos/failure/pi0_libero_10_task5_S01_seed143_init1.mp4) | - |
| 5 | S02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_3ae880086ee31429a9023f6ffd5b34d4 (videos/failure/pi0_libero_10_task5_S02_seed142_init0.mp4) | - |
| 5 | S02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d85d35b45fa3663048022fdade82f981 (videos/failure/pi0_libero_10_task5_S02_seed143_init1.mp4) | - |
| 5 | S03 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e7099ce1ef0a8600f7f736e688581f42 (videos/failure/pi0_libero_10_task5_S03_seed142_init0.mp4) | - |
| 5 | S03 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_13a5868382fb070a2605836069097cf4 (videos/success/pi0_libero_10_task5_S03_seed143_init1.mp4) | - |
| 5 | S04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_8188c5d9e1590e933bf9e010322ba388 (videos/failure/pi0_libero_10_task5_S04_seed142_init0.mp4) | - |
| 5 | S04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e532ac21906585f9fdd3ad363bca7563 (videos/failure/pi0_libero_10_task5_S04_seed143_init1.mp4) | - |
| 5 | S05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_95f34d53d2e3fbbfae5c78574102b4b5 (videos/success/pi0_libero_10_task5_S05_seed142_init0.mp4) | - |
| 5 | S05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_c2239e09822d7a916a07d675b36a55a0 (videos/success/pi0_libero_10_task5_S05_seed143_init1.mp4) | - |
| 5 | S06 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_00dc271051bb96af2566541c4e56af35 (videos/failure/pi0_libero_10_task5_S06_seed142_init0.mp4) | - |
| 5 | S06 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_cebac4c51539029e6435399826d4674e (videos/failure/pi0_libero_10_task5_S06_seed143_init1.mp4) | - |
| 5 | S07 | 142 | 0 | PENDING | PENDING | PASS | PASS | 2 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_43666d5d173482c0b4b53179aefdeeb5 (videos/success/pi0_libero_10_task5_S07_seed142_init0.mp4) | - |
| 5 | S07 | 143 | 1 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2be4bc2a7966f0de768586d35e3683e7 (videos/failure/pi0_libero_10_task5_S07_seed143_init1.mp4) | - |
| 5 | S08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_83258bb421f285d165e4668f11b0604d (videos/success/pi0_libero_10_task5_S08_seed142_init0.mp4) | - |
| 5 | S08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_90b4f284cf3bfed0370bbe2be5cac245 (videos/success/pi0_libero_10_task5_S08_seed143_init1.mp4) | - |
| 5 | S09 | 142 | 0 | PENDING | ISSUE | PENDING | PASS | 1 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_c49b769be00e11fb7184c8b00b63f4ef (videos/success/pi0_libero_10_task5_S09_seed142_init0.mp4) | - |
| 5 | S09 | 143 | 1 | PENDING | ISSUE | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fde66ad9e13320022c21dd2586a0acb6 (videos/failure/pi0_libero_10_task5_S09_seed143_init1.mp4) | - |
| 5 | S10 | 142 | 0 | PASS | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_cc9fcfb257962a88d52017173d17d9cc (videos/failure/pi0_libero_10_task5_S10_seed142_init0.mp4) | 穿模 |
| 5 | S10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_97b3f109df5c8a6c9fc7b31eaa10cc6d (videos/success/pi0_libero_10_task5_S10_seed143_init1.mp4) | - |
| 5 | S11 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_a88c4648d99b84995309ee2cdb1193ae (videos/success/pi0_libero_10_task5_S11_seed142_init0.mp4) | - |
| 5 | S11 | 143 | 1 | PASS | ISSUE | PASS | PASS | 2 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_95c70d0860b74863ee5e27d0d9dec0ff (videos/success/pi0_libero_10_task5_S11_seed143_init1.mp4) | - |
| 5 | S12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_88bfbd32cc6c2fa5468dad1575afd1ff (videos/success/pi0_libero_10_task5_S12_seed142_init0.mp4) | - |
| 5 | S12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_c6adc95e2b4b441e4b3a07ee006a6aed (videos/success/pi0_libero_10_task5_S12_seed143_init1.mp4) | - |
| 5 | S13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_08117f34f41b21d47cffffafbb53a64b (videos/failure/pi0_libero_10_task5_S13_seed142_init0.mp4) | - |
| 5 | S13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_5d148f16d695d9df09be0f3089df06f3 (videos/success/pi0_libero_10_task5_S13_seed143_init1.mp4) | - |
| 5 | S14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_c4139e89d9f0de0e324119ab069b93d9 (videos/failure/pi0_libero_10_task5_S14_seed142_init0.mp4) | - |
| 5 | S14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_23b10f332f7d750435bf3671e94052fe (videos/success/pi0_libero_10_task5_S14_seed143_init1.mp4) | - |
| 5 | S15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_970197422c9a6d7318c37a4d07cf7424 (videos/success/pi0_libero_10_task5_S15_seed142_init0.mp4) | - |
| 5 | S15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_ef3db9f6273deb4eafd36eb835cfd951 (videos/success/pi0_libero_10_task5_S15_seed143_init1.mp4) | - |
| 5 | S16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_aa1ca1b8176582d84d87a86e925c0b06 (videos/success/pi0_libero_10_task5_S16_seed142_init0.mp4) | - |
| 5 | S16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_76a3b37b6983a44774b684839aa61cb3 (videos/success/pi0_libero_10_task5_S16_seed143_init1.mp4) | - |
| 5 | S17 | 142 | 0 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_7361494a6f0ae6a35ddbaed511626309 (videos/failure/pi0_libero_10_task5_S17_seed142_init0.mp4) | - |
| 5 | S17 | 143 | 1 | PENDING | PENDING | PASS | PASS | 2 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_7f22ab9e3b69c5b2e146eda05a446b3f (videos/success/pi0_libero_10_task5_S17_seed143_init1.mp4) | - |
| 5 | S18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_accfe263d59c72f3122421d2b5b73440 (videos/success/pi0_libero_10_task5_S18_seed142_init0.mp4) | - |
| 5 | S18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_af7e6052576c2ea4062bd439d36aa511 (videos/failure/pi0_libero_10_task5_S18_seed143_init1.mp4) | - |
| 5 | S19 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b1dcaeabd5f05a0b87175b912e0e4951 (videos/success/pi0_libero_10_task5_S19_seed142_init0.mp4) | - |
| 5 | S19 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_5fdcb6e84c48e6cee2705cd4596fa176 (videos/success/pi0_libero_10_task5_S19_seed143_init1.mp4) | - |
| 5 | S20 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_67586069e6e2449f798b26971f79d12f (videos/failure/pi0_libero_10_task5_S20_seed142_init0.mp4) | - |
| 5 | S20 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_694c8bb3a43e5d5bf2da4c1ff4efb9cc (videos/failure/pi0_libero_10_task5_S20_seed143_init1.mp4) | - |
| 5 | S21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b5db47c42bf04074457b2344e9d9ba55 (videos/success/pi0_libero_10_task5_S21_seed142_init0.mp4) | - |
| 5 | S21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_f6b567d8de5f9e323bf6bab72af19e89 (videos/success/pi0_libero_10_task5_S21_seed143_init1.mp4) | - |
| 5 | S22 | 142 | 0 | - | - | ISSUE | PASS | 1 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_acd43b18fba8bc2ab3ca5623439e60b4 (videos/success/pi0_libero_10_task5_S22_seed142_init0.mp4) | - |
| 5 | S22 | 143 | 1 | - | - | ISSUE | PASS | 1 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_c8b1f2ea1b50edd48baf6a66d00940ae (videos/success/pi0_libero_10_task5_S22_seed143_init1.mp4) | - |
| 5 | D01 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_c2a99f2870982eb7fcd829c76184c319 (videos/failure/pi0_libero_10_task5_D01_seed142_init0.mp4) | - |
| 5 | D01 | 143 | 1 | PASS | PASS | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_c0386779bf1de9de5069dec3e475c461 (videos/failure/pi0_libero_10_task5_D01_seed143_init1.mp4) | - |
| 5 | D02 | 142 | 0 | ISSUE | PASS | PENDING | ISSUE | 0 | ISSUE_OPEN | SUCCESS | NOT_TRIGGERED | R003 | R003:ep_bd5f6f581572f34f52de3f8b75a93395 (videos/success/pi0_libero_10_task5_D02_seed142_init0.mp4) | 接收器没移动 |
| 5 | D02 | 143 | 1 | ISSUE | PASS | PASS | ISSUE | 0 | ISSUE_OPEN | SUCCESS | NOT_TRIGGERED | R003 | R003:ep_e8d3d20af7df93390a8da28e33c14ce1 (videos/success/pi0_libero_10_task5_D02_seed143_init1.mp4) | 接收器没移动 |
| 5 | D03 | 142 | 0 | ISSUE | PASS | PASS | ISSUE | 0 | ISSUE_OPEN | SUCCESS | PENDING | R003 | R003:ep_ce69627b6bccdaab29952f97db86c16d (videos/success/pi0_libero_10_task5_D03_seed142_init0.mp4) | 占用了判定成功，但是没有完全放进去，仿真环境问题 |
| 5 | D03 | 143 | 1 | ISSUE | PASS | ISSUE | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d854f369f9e58a2a900c3fb52954823a (videos/failure/pi0_libero_10_task5_D03_seed143_init1.mp4) | - |
| 5 | D04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_c93ed79f69f012b9b6f3fd8217decd86 (videos/success/pi0_libero_10_task5_D04_seed142_init0.mp4) | - |
| 5 | D04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_d30350f580ec364b11dbfed62732c72e (videos/success/pi0_libero_10_task5_D04_seed143_init1.mp4) | - |
| 5 | D05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_4167e75ad88235b1355ebbdf036ff440 (videos/failure/pi0_libero_10_task5_D05_seed142_init0.mp4) | - |
| 5 | D05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f6d4bf581732f7d3dcbdaef35c3825ef (videos/failure/pi0_libero_10_task5_D05_seed143_init1.mp4) | - |
| 5 | D06 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_bb160751ba524b2efc9f36477c7c3aaa (videos/success/pi0_libero_10_task5_D06_seed142_init0.mp4) | - |
| 5 | D06 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_4836100c2194d5fbe4dd867b6ea35faf (videos/failure/pi0_libero_10_task5_D06_seed143_init1.mp4) | - |
| 5 | D07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_6cba2dcd72e67fa2925735e6968ef3a0 (videos/failure/pi0_libero_10_task5_D07_seed142_init0.mp4) | - |
| 5 | D07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_b96f39b665f1518dfde4d3e54bfc176f (videos/success/pi0_libero_10_task5_D07_seed143_init1.mp4) | - |
| 5 | D08 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_daa2611d769043d6ff5009c73d1c2712 (videos/success/pi0_libero_10_task5_D08_seed142_init0.mp4) | - |
| 5 | D08 | 143 | 1 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_d575d44e2fa7d4182d5e1eff6688db52 (videos/success/pi0_libero_10_task5_D08_seed143_init1.mp4) | - |
| 5 | D09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_7dbdf3f407cb450c07c569c51929878c (videos/success/pi0_libero_10_task5_D09_seed142_init0.mp4) | - |
| 5 | D09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_9a1a9417827cf7feacbed45e75889e61 (videos/success/pi0_libero_10_task5_D09_seed143_init1.mp4) | - |
| 5 | D10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0e2b7e34595e67ddc74fceaaf1683c71 (videos/failure/pi0_libero_10_task5_D10_seed142_init0.mp4) | - |
| 5 | D10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_dcb1eb0710ac51b85edb55f83946225b (videos/success/pi0_libero_10_task5_D10_seed143_init1.mp4) | - |
| 5 | D11 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_89c51d182ab1f04761a24dec57908cf5 (videos/success/pi0_libero_10_task5_D11_seed142_init0.mp4) | - |
| 5 | D11 | 143 | 1 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_c074f46f7d9d82a5e9aeb38dc6f82f76 (videos/success/pi0_libero_10_task5_D11_seed143_init1.mp4) | - |
| 5 | D12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_0b055d8ef767520a78c7b0fe4a5bd45d (videos/success/pi0_libero_10_task5_D12_seed142_init0.mp4) | - |
| 5 | D12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_902bad7c93fb5f8c5188b5b4f197d30d (videos/success/pi0_libero_10_task5_D12_seed143_init1.mp4) | - |
| 5 | D13 | 142 | 0 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_88e8a16b21679de5034a8a4e22ec544f (videos/failure/pi0_libero_10_task5_D13_seed142_init0.mp4) | - |
| 5 | D13 | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_a37aeb92c137b868e5ec6f85c4ab8355 (videos/failure/pi0_libero_10_task5_D13_seed143_init1.mp4) | - |
| 5 | D14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_3d9dc81e244af0915bdee742f1e4c680 (videos/success/pi0_libero_10_task5_D14_seed142_init0.mp4) | - |
| 5 | D14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_9828c9747fc3f00eaf10c9d31871ca68 (videos/success/pi0_libero_10_task5_D14_seed143_init1.mp4) | - |
| 5 | D15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_358f9bf673e814b4d68b3fa3e8e88181 (videos/success/pi0_libero_10_task5_D15_seed142_init0.mp4) | - |
| 5 | D15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_e2c2e3bc65578579155befa86a42cc0f (videos/success/pi0_libero_10_task5_D15_seed143_init1.mp4) | - |
| 5 | D16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_93679e79690f7af17a2d7ebef39bc48d (videos/success/pi0_libero_10_task5_D16_seed142_init0.mp4) | - |
| 5 | D16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fad45284a27e966db8ef3f95731a4b30 (videos/failure/pi0_libero_10_task5_D16_seed143_init1.mp4) | - |
| 5 | D17 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ea196177db4d212d4f0d13bf3fd1d716 (videos/failure/pi0_libero_10_task5_D17_seed142_init0.mp4) | - |
| 5 | D17 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_dedd41431bfd1ad5aaf378ca0a9a783b (videos/failure/pi0_libero_10_task5_D17_seed143_init1.mp4) | - |
| 5 | D18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0ff351fcfc121e2fa17ec7fbbc09b947 (videos/failure/pi0_libero_10_task5_D18_seed142_init0.mp4) | - |
| 5 | D18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_3b0524d1f829d907c3e50107feffe851 (videos/failure/pi0_libero_10_task5_D18_seed143_init1.mp4) | - |
| 5 | D19 | 142 | 0 | PENDING | PASS | PENDING | - | 0 | ISSUE_OPEN | FAILURE | PENDING | R002 | R002:ep_682fc8b53293f15cae75bdcd62ae1d50 (videos/failure/pi0_libero_10_task5_D19_seed142_init0.mp4) | 没懂这个任务在干啥 |
| 5 | D19 | 143 | 1 | PENDING | PASS | PENDING | - | 0 | ISSUE_OPEN | SUCCESS | PENDING | R002 | R002:ep_b60a4fd8a298b1aa4c46cc243e6c17f5 (videos/success/pi0_libero_10_task5_D19_seed143_init1.mp4) | 没懂 |
| 5 | D20 | 142 | 0 | - | - | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_c4e8b4217af559114f0a2612460e065b (videos/failure/pi0_libero_10_task5_D20_seed142_init0.mp4) | - |
| 5 | D20 | 143 | 1 | - | - | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_e8f4aaa57aaef6cc600f6e4ea7f14224 (videos/failure/pi0_libero_10_task5_D20_seed143_init1.mp4) | - |
| 5 | D21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ffcb1cbf9ee99ce294a82be8bda6a645 (videos/failure/pi0_libero_10_task5_D21_seed142_init0.mp4) | - |
| 5 | D21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_3a890bb08eb26c3f6afaf883bee3eb87 (videos/success/pi0_libero_10_task5_D21_seed143_init1.mp4) | - |
| 6 | BASE | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_95f3d1b72a6a49cfdccc4dd86088506e (videos/failure/pi0_libero_10_task6_BASE_seed142_init0.mp4) | - |
| 6 | BASE | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b93b4ba62e94a1dd360bbbce4194d067 (videos/success/pi0_libero_10_task6_BASE_seed143_init1.mp4) | - |
| 6 | S01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_91344cff6f04d9df3c75f624a46e0fb3 (videos/failure/pi0_libero_10_task6_S01_seed142_init0.mp4) | - |
| 6 | S01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2afe533fdecb552c056ea8a8c665d603 (videos/failure/pi0_libero_10_task6_S01_seed143_init1.mp4) | - |
| 6 | S02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e07696b75566b0b298c117485e02f34d (videos/failure/pi0_libero_10_task6_S02_seed142_init0.mp4) | - |
| 6 | S02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bbccaaa7beba25c6e9bdb8b3237b2c32 (videos/failure/pi0_libero_10_task6_S02_seed143_init1.mp4) | - |
| 6 | S03 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2f0113fcc0fe3fc7e549462cc2ff9368 (videos/failure/pi0_libero_10_task6_S03_seed142_init0.mp4) | - |
| 6 | S03 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4b362ad2951504803b0c04a77159ff8c (videos/failure/pi0_libero_10_task6_S03_seed143_init1.mp4) | - |
| 6 | S04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bde3782280dba914ce3a952408f13a91 (videos/failure/pi0_libero_10_task6_S04_seed142_init0.mp4) | - |
| 6 | S04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4cc3f9634fa7bacccb26fe7854d0cb0a (videos/failure/pi0_libero_10_task6_S04_seed143_init1.mp4) | - |
| 6 | S05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_00da5f58549b88c4c715b8979f942dee (videos/failure/pi0_libero_10_task6_S05_seed142_init0.mp4) | - |
| 6 | S05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_82aa6f81964fd70341f4499d50fb5d79 (videos/failure/pi0_libero_10_task6_S05_seed143_init1.mp4) | - |
| 6 | S06 | 142 | 0 | ISSUE | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e9d056fc1e7d2eae17bf48c68a0999a7 (videos/failure/pi0_libero_10_task6_S06_seed142_init0.mp4) | - |
| 6 | S06 | 143 | 1 | ISSUE | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_418134c0471d99d02d9daf81c4a25c68 (videos/failure/pi0_libero_10_task6_S06_seed143_init1.mp4) | - |
| 6 | S07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1474b3bebeeca6777dbf409de885ab38 (videos/failure/pi0_libero_10_task6_S07_seed142_init0.mp4) | - |
| 6 | S07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_37e312398fcb1ace95a372beacf86478 (videos/failure/pi0_libero_10_task6_S07_seed143_init1.mp4) | - |
| 6 | S08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_867e7478f112ea58780024b7d6cb93de (videos/failure/pi0_libero_10_task6_S08_seed142_init0.mp4) | - |
| 6 | S08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1e6e6586598c0582c08cb881ad19a3b5 (videos/failure/pi0_libero_10_task6_S08_seed143_init1.mp4) | - |
| 6 | S09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_2b398731914c5ec0186f80d30930e44b (videos/success/pi0_libero_10_task6_S09_seed142_init0.mp4) | - |
| 6 | S09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_a5b14b70957e761fb9b5885ffaeb8968 (videos/success/pi0_libero_10_task6_S09_seed143_init1.mp4) | - |
| 6 | S10 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f19f753c54c8020ede781f77ecd46267 (videos/failure/pi0_libero_10_task6_S10_seed142_init0.mp4) | - |
| 6 | S10 | 143 | 1 | PASS | PASS | PASS | PASS | 4 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_2350b4bfdfa930c961524500c0e361d4 (videos/success/pi0_libero_10_task6_S10_seed143_init1.mp4) | - |
| 6 | S11 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_617e421bfc076c7c95171a0de419430e (videos/success/pi0_libero_10_task6_S11_seed142_init0.mp4) | - |
| 6 | S11 | 143 | 1 | PASS | PASS | PASS | PASS | 4 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1090d339a8ccc49a0e2cefe431776f99 (videos/failure/pi0_libero_10_task6_S11_seed143_init1.mp4) | - |
| 6 | S12 | 142 | 0 | ISSUE | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4666f541d230b2cd7244727c133c0519 (videos/failure/pi0_libero_10_task6_S12_seed142_init0.mp4) | - |
| 6 | S12 | 143 | 1 | ISSUE | PASS | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_9d98c9b2d75affd3c03aafcad9bb7a23 (videos/failure/pi0_libero_10_task6_S12_seed143_init1.mp4) | 穿模 |
| 6 | S13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_3b3649963a9bc45378cbe32a088916f2 (videos/success/pi0_libero_10_task6_S13_seed142_init0.mp4) | - |
| 6 | S13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fc407e4badc6c212abf658da8c6eb3cd (videos/failure/pi0_libero_10_task6_S13_seed143_init1.mp4) | - |
| 6 | S14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_32a4d0dba4e5ab178592305ccafd4848 (videos/failure/pi0_libero_10_task6_S14_seed142_init0.mp4) | - |
| 6 | S14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_d16fd7b45c9fa69946545e80b01862a3 (videos/success/pi0_libero_10_task6_S14_seed143_init1.mp4) | - |
| 6 | S15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_76d143892b6fbff85d95b0bc49fc4c5b (videos/failure/pi0_libero_10_task6_S15_seed142_init0.mp4) | - |
| 6 | S15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d038d7f19b2fa63ab0d6d72314fee195 (videos/failure/pi0_libero_10_task6_S15_seed143_init1.mp4) | - |
| 6 | S16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_653edc2cd8b09fceb40a7fe263572710 (videos/failure/pi0_libero_10_task6_S16_seed142_init0.mp4) | - |
| 6 | S16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e8db9c15ce250d4b246089cb611d96da (videos/failure/pi0_libero_10_task6_S16_seed143_init1.mp4) | - |
| 6 | S17 | 142 | 0 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_3300dc84b03dd8d7458813d746737b06 (videos/failure/pi0_libero_10_task6_S17_seed142_init0.mp4) | - |
| 6 | S17 | 143 | 1 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_065c1782b65714ca25071c3cd2c76cc6 (videos/failure/pi0_libero_10_task6_S17_seed143_init1.mp4) | - |
| 6 | S18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f3704258199315033474097b9da7401a (videos/failure/pi0_libero_10_task6_S18_seed142_init0.mp4) | - |
| 6 | S18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4503f647cbecb0d8643eb8892e5cc713 (videos/failure/pi0_libero_10_task6_S18_seed143_init1.mp4) | - |
| 6 | S19 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_5f79f8b93af6fb8e92434ff0c5342605 (videos/failure/pi0_libero_10_task6_S19_seed142_init0.mp4) | - |
| 6 | S19 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_386727ef670736e5088220f13b2699b0 (videos/failure/pi0_libero_10_task6_S19_seed143_init1.mp4) | - |
| 6 | S20 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_46272de0f790aedfdfb408844b853a2e (videos/failure/pi0_libero_10_task6_S20_seed142_init0.mp4) | - |
| 6 | S20 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_6b19ed0869cedbbf1268536aa1085f5d (videos/failure/pi0_libero_10_task6_S20_seed143_init1.mp4) | - |
| 6 | S21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_239ae2fc701299512d1cd701604b4bdd (videos/failure/pi0_libero_10_task6_S21_seed142_init0.mp4) | - |
| 6 | S21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_56a8550d24f5d8a4c9dc2a301aea19a5 (videos/failure/pi0_libero_10_task6_S21_seed143_init1.mp4) | - |
| 6 | S22 | 142 | 0 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_60c23dc6b1429030ac274b8a96d3a025 (videos/failure/pi0_libero_10_task6_S22_seed142_init0.mp4) | - |
| 6 | S22 | 143 | 1 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_6cb284ebbf11ac0f22e45a588f4141d7 (videos/failure/pi0_libero_10_task6_S22_seed143_init1.mp4) | - |
| 6 | D01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_766296c532c1edc2bd03ae7c0c0821f1 (videos/failure/pi0_libero_10_task6_D01_seed142_init0.mp4) | - |
| 6 | D01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_8267235fc21d5cd170e6f5d1bc872ecd (videos/failure/pi0_libero_10_task6_D01_seed143_init1.mp4) | - |
| 6 | D02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_8e235f37a96a422834c2f9de4baaa83a (videos/failure/pi0_libero_10_task6_D02_seed142_init0.mp4) | - |
| 6 | D02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_604e62984f81228b98f3df7b3ac0f8db (videos/failure/pi0_libero_10_task6_D02_seed143_init1.mp4) | - |
| 6 | D03 | 142 | 0 | ISSUE | PASS | PASS | ISSUE | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_c18c4063dfd9e443f042acfbfb1922d1 (videos/failure/pi0_libero_10_task6_D03_seed142_init0.mp4) | 占用物体出现的位置非接收区域 |
| 6 | D03 | 143 | 1 | ISSUE | PASS | PASS | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_TRIGGERED | R003 | R003:ep_382279bdce0ef6d0402b3694a830832a (videos/failure/pi0_libero_10_task6_D03_seed143_init1.mp4) | 未出现占用物体 |
| 6 | D04 | 142 | 0 | PASS | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_a60e62d2bf9781dad98229c57132a674 (videos/failure/pi0_libero_10_task6_D04_seed142_init0.mp4) | 穿模 |
| 6 | D04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_416d67a901ab964bebdc88514c7947b3 (videos/failure/pi0_libero_10_task6_D04_seed143_init1.mp4) | - |
| 6 | D05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f1dc00abd871003fbdc79190db5b755f (videos/failure/pi0_libero_10_task6_D05_seed142_init0.mp4) | - |
| 6 | D05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fd3b5482f738a6c255646c939c5342fc (videos/failure/pi0_libero_10_task6_D05_seed143_init1.mp4) | - |
| 6 | D06 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_19ebc08f10381cc46223914a1bc88a32 (videos/failure/pi0_libero_10_task6_D06_seed142_init0.mp4) | - |
| 6 | D06 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_72f8ef8f16acb11c7d9fa9c36eff1924 (videos/success/pi0_libero_10_task6_D06_seed143_init1.mp4) | - |
| 6 | D07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_247da4c8d0c09aebcf11c4bc0f5646a1 (videos/success/pi0_libero_10_task6_D07_seed142_init0.mp4) | - |
| 6 | D07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f4def02c584381010000cbd503f47bf6 (videos/failure/pi0_libero_10_task6_D07_seed143_init1.mp4) | - |
| 6 | D08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_f5b28692534e26907510b27e1c081e0f (videos/success/pi0_libero_10_task6_D08_seed142_init0.mp4) | - |
| 6 | D08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_7f663f96a95dd6cb24de9e15356bd06d (videos/success/pi0_libero_10_task6_D08_seed143_init1.mp4) | - |
| 6 | D09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0559c1e4fcbcf3e0abfe3c9a5d083c55 (videos/failure/pi0_libero_10_task6_D09_seed142_init0.mp4) | - |
| 6 | D09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_bc40ae9994c2ac986902d2fc54e3e735 (videos/success/pi0_libero_10_task6_D09_seed143_init1.mp4) | - |
| 6 | D10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_11e2f8a4c9edabf5f9aa0f961a4ac0be (videos/success/pi0_libero_10_task6_D10_seed142_init0.mp4) | - |
| 6 | D10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f814be3ac9e3fb2383dd7c23e737a40f (videos/failure/pi0_libero_10_task6_D10_seed143_init1.mp4) | - |
| 6 | D11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_d079ab579dfb17c366829bc4bae1c41b (videos/success/pi0_libero_10_task6_D11_seed142_init0.mp4) | - |
| 6 | D11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_0f1228fec5fc6901a31d63adee2ddf94 (videos/success/pi0_libero_10_task6_D11_seed143_init1.mp4) | - |
| 6 | D12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_a4d9ff2f0c302071a1af9ddd5a57ec97 (videos/failure/pi0_libero_10_task6_D12_seed142_init0.mp4) | - |
| 6 | D12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_800069d936648ad5988ca63bbce4045b (videos/failure/pi0_libero_10_task6_D12_seed143_init1.mp4) | - |
| 6 | D13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_85a3856263db45510d361427c7e02f41 (videos/failure/pi0_libero_10_task6_D13_seed142_init0.mp4) | - |
| 6 | D13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_71fc7703d4e68894927d266626c20cb0 (videos/failure/pi0_libero_10_task6_D13_seed143_init1.mp4) | - |
| 6 | D14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_d1691c54196ce7bc3d15e2cb8645cd9e (videos/success/pi0_libero_10_task6_D14_seed142_init0.mp4) | - |
| 6 | D14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f12b58fb94cd2a92d6b60483dcbc4d24 (videos/failure/pi0_libero_10_task6_D14_seed143_init1.mp4) | - |
| 6 | D15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_7c05600aa4c90e3e9f7eda0535af0c97 (videos/success/pi0_libero_10_task6_D15_seed142_init0.mp4) | - |
| 6 | D15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_6f8c136494e14d99c245898bd15c4c97 (videos/success/pi0_libero_10_task6_D15_seed143_init1.mp4) | - |
| 6 | D16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_8f51d5b18f1405df28117c1c7bf86220 (videos/failure/pi0_libero_10_task6_D16_seed142_init0.mp4) | - |
| 6 | D16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_7b0cb1613565cbe6f4ef040378cbba4f (videos/failure/pi0_libero_10_task6_D16_seed143_init1.mp4) | - |
| 6 | D17 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_6a1fda0b82bd9b197e4ced2a9e753abc (videos/failure/pi0_libero_10_task6_D17_seed142_init0.mp4) | - |
| 6 | D17 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_02461f70e7d0094ef5e2a2621e66bc11 (videos/failure/pi0_libero_10_task6_D17_seed143_init1.mp4) | - |
| 6 | D18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_57ae4f69e09f1bd342a099d115d42c2e (videos/failure/pi0_libero_10_task6_D18_seed142_init0.mp4) | - |
| 6 | D18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_b4a2d8e1141c69a9c47037f259d5ecef (videos/failure/pi0_libero_10_task6_D18_seed143_init1.mp4) | - |
| 6 | D19 | 142 | 0 | ISSUE | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_a54380cf5b554bdf32f0891e7a79c4a6 (videos/failure/pi0_libero_10_task6_D19_seed142_init0.mp4) | - |
| 6 | D19 | 143 | 1 | ISSUE | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_00e2fc38ccb918249e4a0367ee1482e0 (videos/failure/pi0_libero_10_task6_D19_seed143_init1.mp4) | - |
| 6 | D20 | 142 | 0 | - | - | PASS | PASS | 2 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fbca3ceb6a7901ea585c2c4c49357d9d (videos/failure/pi0_libero_10_task6_D20_seed142_init0.mp4) | - |
| 6 | D20 | 143 | 1 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | SUCCESS | PENDING | R003 | R003:ep_2bb7647f321405e37a67b6ec51b510e8 (videos/success/pi0_libero_10_task6_D20_seed143_init1.mp4) | 没观察到回退 |
| 6 | D21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_95c9ecef30ba96ca066550152945c251 (videos/failure/pi0_libero_10_task6_D21_seed142_init0.mp4) | - |
| 6 | D21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_4391764212b17a51c5dccba53ef36eb6 (videos/failure/pi0_libero_10_task6_D21_seed143_init1.mp4) | - |
| 7 | BASE | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_63820a9e4ddeeaef09fe9508f3662b01 (videos/failure/pi0_libero_10_task7_BASE_seed142_init0.mp4) | - |
| 7 | BASE | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fa49fd0705bb687441358f39b13c3866 (videos/failure/pi0_libero_10_task7_BASE_seed143_init1.mp4) | - |
| 7 | S01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_dbf615dbd2ce2619c5c2b00d99157f55 (videos/failure/pi0_libero_10_task7_S01_seed142_init0.mp4) | - |
| 7 | S01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1ce2d496865bcc7ff114be3175b0e905 (videos/failure/pi0_libero_10_task7_S01_seed143_init1.mp4) | - |
| 7 | S02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_8cd6025d5c7b5f302f6860a3ca8fcd75 (videos/failure/pi0_libero_10_task7_S02_seed142_init0.mp4) | - |
| 7 | S02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_51a339003cde055810d886a10e235050 (videos/failure/pi0_libero_10_task7_S02_seed143_init1.mp4) | - |
| 7 | S03 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4ce9e8137375f56a036a5fc77c246f7e (videos/failure/pi0_libero_10_task7_S03_seed142_init0.mp4) | - |
| 7 | S03 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_36ff3514234d18dd55378c134d3363e3 (videos/failure/pi0_libero_10_task7_S03_seed143_init1.mp4) | - |
| 7 | S04 | 142 | 0 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_79ab40b415a5586766124b3362affb4e (videos/failure/pi0_libero_10_task7_S04_seed142_init0.mp4) | - |
| 7 | S04 | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e5de14fcab0b21906fd3062e5e078fa7 (videos/failure/pi0_libero_10_task7_S04_seed143_init1.mp4) | - |
| 7 | S05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_89411949a5bfff8c8833b69a0290c733 (videos/failure/pi0_libero_10_task7_S05_seed142_init0.mp4) | - |
| 7 | S05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_963e2d75693d5bb785abad4b26e4d042 (videos/failure/pi0_libero_10_task7_S05_seed143_init1.mp4) | - |
| 7 | S06 | 142 | 0 | ISSUE | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fe5af706156348fdae1d7ab1f28f5636 (videos/failure/pi0_libero_10_task7_S06_seed142_init0.mp4) | - |
| 7 | S06 | 143 | 1 | ISSUE | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_0802822ac5cc0f6d68dcb474e3aac397 (videos/failure/pi0_libero_10_task7_S06_seed143_init1.mp4) | - |
| 7 | S07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_78cfd59c1cccfbd03e252a5eb832f67f (videos/failure/pi0_libero_10_task7_S07_seed142_init0.mp4) | - |
| 7 | S07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_06f50ef32f665003bb0bf44aa02a5d31 (videos/failure/pi0_libero_10_task7_S07_seed143_init1.mp4) | - |
| 7 | S08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_d2a4440e48ef8336d96e1f86c882313c (videos/success/pi0_libero_10_task7_S08_seed142_init0.mp4) | - |
| 7 | S08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bdfd41ff130ac26fceeb00abc8f847e8 (videos/failure/pi0_libero_10_task7_S08_seed143_init1.mp4) | - |
| 7 | S09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_15339d8179828253ccfec7678909b41f (videos/failure/pi0_libero_10_task7_S09_seed142_init0.mp4) | - |
| 7 | S09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_807e03a58d2738382545474aff73dfcf (videos/failure/pi0_libero_10_task7_S09_seed143_init1.mp4) | - |
| 7 | S10 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_ce62c2e5161942baada23603e27b0356 (videos/success/pi0_libero_10_task7_S10_seed142_init0.mp4) | - |
| 7 | S10 | 143 | 1 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_526b23f64a82e7ca2e2a9594d6bfd05c (videos/failure/pi0_libero_10_task7_S10_seed143_init1.mp4) | - |
| 7 | S11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_ddb2e5641a7caf0362a22777c2e6ea7b (videos/failure/pi0_libero_10_task7_S11_seed142_init0.mp4) | - |
| 7 | S11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_a88f2328050d4e3446733de8df6b34b0 (videos/failure/pi0_libero_10_task7_S11_seed143_init1.mp4) | - |
| 7 | S12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bf11f6a8e84b64a495f5e6d8a65e5257 (videos/failure/pi0_libero_10_task7_S12_seed142_init0.mp4) | - |
| 7 | S12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_c61f2c759288e947a8938441f6138343 (videos/failure/pi0_libero_10_task7_S12_seed143_init1.mp4) | - |
| 7 | S13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_26fa78ac7235caef3e3205c58573220b (videos/failure/pi0_libero_10_task7_S13_seed142_init0.mp4) | - |
| 7 | S13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_25f7edc759acab2be43a7120d1b16908 (videos/failure/pi0_libero_10_task7_S13_seed143_init1.mp4) | - |
| 7 | S14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_c475c7aac7549b8f0d3877148e0ecf1b (videos/failure/pi0_libero_10_task7_S14_seed142_init0.mp4) | - |
| 7 | S14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_0f8e2ded62002c41b1cf1b3642f22bba (videos/failure/pi0_libero_10_task7_S14_seed143_init1.mp4) | - |
| 7 | S15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_112e418ca9a60089c0363bda9092a638 (videos/failure/pi0_libero_10_task7_S15_seed142_init0.mp4) | - |
| 7 | S15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_272e33370006bede2550b7db9912b7e9 (videos/failure/pi0_libero_10_task7_S15_seed143_init1.mp4) | - |
| 7 | S16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b2ac67f899da10e9ff378e29db28a8ad (videos/success/pi0_libero_10_task7_S16_seed142_init0.mp4) | - |
| 7 | S16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_7c9fdba588a55e0d6197b8a92404b078 (videos/failure/pi0_libero_10_task7_S16_seed143_init1.mp4) | - |
| 7 | S17 | 142 | 0 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2b4f8c00f907721e58e23a4925384a57 (videos/failure/pi0_libero_10_task7_S17_seed142_init0.mp4) | - |
| 7 | S17 | 143 | 1 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_66523ede4f51843736dd18b4f9e16f5b (videos/failure/pi0_libero_10_task7_S17_seed143_init1.mp4) | - |
| 7 | S18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_55a1952d3a253ca13b2fccbad824533b (videos/failure/pi0_libero_10_task7_S18_seed142_init0.mp4) | - |
| 7 | S18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_86c5ad1b72294ca0a4cbcbd6aed2b379 (videos/failure/pi0_libero_10_task7_S18_seed143_init1.mp4) | - |
| 7 | S19 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1228dbcf396abb8c9029fba7f678614e (videos/failure/pi0_libero_10_task7_S19_seed142_init0.mp4) | - |
| 7 | S19 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_5fe483892fa5121ea5e86175f6aff0cc (videos/failure/pi0_libero_10_task7_S19_seed143_init1.mp4) | - |
| 7 | S20 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_ad167902efde1e10abd95a119c324dea (videos/failure/pi0_libero_10_task7_S20_seed142_init0.mp4) | - |
| 7 | S20 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_9c230ca3b712d16e24a5704cc47ecdf9 (videos/failure/pi0_libero_10_task7_S20_seed143_init1.mp4) | - |
| 7 | S21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_840deee7c9a1b98344a008eb25b5f5cc (videos/failure/pi0_libero_10_task7_S21_seed142_init0.mp4) | - |
| 7 | S21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d40d9a3009c8d7dab4efc95d3acd208b (videos/failure/pi0_libero_10_task7_S21_seed143_init1.mp4) | - |
| 7 | S22 | 142 | 0 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_961959d1b8180a53d463dd33fc016796 (videos/failure/pi0_libero_10_task7_S22_seed142_init0.mp4) | - |
| 7 | S22 | 143 | 1 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_0132e035b3d3236a927d04e1f592563f (videos/failure/pi0_libero_10_task7_S22_seed143_init1.mp4) | - |
| 7 | D01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_6d9f136112dceea8e2dc1e15d51c3fb3 (videos/failure/pi0_libero_10_task7_D01_seed142_init0.mp4) | - |
| 7 | D01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_755c163934ddfc9bd55bd63c25314499 (videos/failure/pi0_libero_10_task7_D01_seed143_init1.mp4) | - |
| 7 | D02 | 142 | 0 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d64eaa7c46d7686ac38e2e287e3bfbc0 (videos/failure/pi0_libero_10_task7_D02_seed142_init0.mp4) | - |
| 7 | D02 | 143 | 1 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_9468efc346bbbf924f3968e88e366e20 (videos/failure/pi0_libero_10_task7_D02_seed143_init1.mp4) | - |
| 7 | D03 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f130a3ff7d1e14cd66a79e80e80f8dfd (videos/failure/pi0_libero_10_task7_D03_seed142_init0.mp4) | - |
| 7 | D03 | 143 | 1 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_6fcdcd14541b249fbf07182607784eb2 (videos/failure/pi0_libero_10_task7_D03_seed143_init1.mp4) | - |
| 7 | D04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_71dbafd926a70cb277f8ce525929f6aa (videos/failure/pi0_libero_10_task7_D04_seed142_init0.mp4) | - |
| 7 | D04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_12d7b7e58999c634c8628ed8141062a3 (videos/failure/pi0_libero_10_task7_D04_seed143_init1.mp4) | - |
| 7 | D05 | 142 | 0 | PENDING | PENDING | PASS | ISSUE | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_7645ca0b4fd13782134cd88cc9f5fbfd (videos/failure/pi0_libero_10_task7_D05_seed142_init0.mp4) | 非运输路径 |
| 7 | D05 | 143 | 1 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_adc460b71cfe09adba0b9a59c3e574af (videos/failure/pi0_libero_10_task7_D05_seed143_init1.mp4) | - |
| 7 | D06 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_62936aa13d2d6a0cca731b26fc65ab70 (videos/failure/pi0_libero_10_task7_D06_seed142_init0.mp4) | - |
| 7 | D06 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_b738c0b8cee77c6955b56d8fdd60e64b (videos/failure/pi0_libero_10_task7_D06_seed143_init1.mp4) | - |
| 7 | D07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_83870d61b1e6cf538f09a1e0d0032f8f (videos/failure/pi0_libero_10_task7_D07_seed142_init0.mp4) | - |
| 7 | D07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_150bf6a742e6beb05e5bdc4dbaef96fc (videos/failure/pi0_libero_10_task7_D07_seed143_init1.mp4) | - |
| 7 | D08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_57af463796191936a8606e23fe18abd7 (videos/failure/pi0_libero_10_task7_D08_seed142_init0.mp4) | - |
| 7 | D08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_df47233c1783b8a995fccb521a236317 (videos/failure/pi0_libero_10_task7_D08_seed143_init1.mp4) | - |
| 7 | D09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f60d06cfb9361eb93ff187ac24787848 (videos/failure/pi0_libero_10_task7_D09_seed142_init0.mp4) | - |
| 7 | D09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_71f96b3ee1639450f14a6a0100ebbe22 (videos/failure/pi0_libero_10_task7_D09_seed143_init1.mp4) | - |
| 7 | D10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_837bc87533f87014519bec04150767dd (videos/failure/pi0_libero_10_task7_D10_seed142_init0.mp4) | - |
| 7 | D10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_b8098aa43309f8c06d3c8648009ae8fa (videos/failure/pi0_libero_10_task7_D10_seed143_init1.mp4) | - |
| 7 | D11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_a5d3dd3fabeab5fd04afbeb9d1c88979 (videos/failure/pi0_libero_10_task7_D11_seed142_init0.mp4) | - |
| 7 | D11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_4965c854e8452cf6be12a945e57fac0c (videos/failure/pi0_libero_10_task7_D11_seed143_init1.mp4) | - |
| 7 | D12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_e5e19cd25f871ff7be14ea97ed486ec3 (videos/success/pi0_libero_10_task7_D12_seed142_init0.mp4) | - |
| 7 | D12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_da6d88a6b019e4669477fa97d1ee1da2 (videos/failure/pi0_libero_10_task7_D12_seed143_init1.mp4) | - |
| 7 | D13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_9eb1c7e4357b215c35ba6df3b486a3d1 (videos/failure/pi0_libero_10_task7_D13_seed142_init0.mp4) | - |
| 7 | D13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0fc07b26b868f1ec966cb276cca887ce (videos/failure/pi0_libero_10_task7_D13_seed143_init1.mp4) | - |
| 7 | D14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_9b3a4bb0c9529bb742676be0623f96f6 (videos/success/pi0_libero_10_task7_D14_seed142_init0.mp4) | - |
| 7 | D14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d5a058d0dcd8aaa89a4871fe759d5f3e (videos/failure/pi0_libero_10_task7_D14_seed143_init1.mp4) | - |
| 7 | D15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_af95d75e4d2091d1584fad8629d2622d (videos/success/pi0_libero_10_task7_D15_seed142_init0.mp4) | - |
| 7 | D15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_085370163f18005f4c3d8fc468e291ed (videos/failure/pi0_libero_10_task7_D15_seed143_init1.mp4) | - |
| 7 | D16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_52d07b1346d8fa0f3707af88e8dead0b (videos/success/pi0_libero_10_task7_D16_seed142_init0.mp4) | - |
| 7 | D16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_2b256bbc678793f86d8bab4176ceaada (videos/failure/pi0_libero_10_task7_D16_seed143_init1.mp4) | - |
| 7 | D17 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_a18376bd518a49e3f65eb83a917b6cb5 (videos/failure/pi0_libero_10_task7_D17_seed142_init0.mp4) | - |
| 7 | D17 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_6b7e9ddd5987e1cc8a1ef8a7a052f69f (videos/failure/pi0_libero_10_task7_D17_seed143_init1.mp4) | - |
| 7 | D18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_18878280ade6ed3dd987b6d35b957b65 (videos/failure/pi0_libero_10_task7_D18_seed142_init0.mp4) | - |
| 7 | D18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0bee3a8bc7bda312b79d83f73849b803 (videos/failure/pi0_libero_10_task7_D18_seed143_init1.mp4) | - |
| 7 | D19 | 142 | 0 | PENDING | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_1f7bdb38eeffcb805c94e9d30e570ec0 (videos/failure/pi0_libero_10_task7_D19_seed142_init0.mp4) | - |
| 7 | D19 | 143 | 1 | PENDING | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_38c044a04e3dc1d2c229ccb6f6d2613a (videos/failure/pi0_libero_10_task7_D19_seed143_init1.mp4) | - |
| 7 | D20 | 142 | 0 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_64dd879fb6a514e314564a2e7a29e9b4 (videos/failure/pi0_libero_10_task7_D20_seed142_init0.mp4) | 没有明显现象 |
| 7 | D20 | 143 | 1 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_ea59fbdcd9eec4124066d881af24b01e (videos/failure/pi0_libero_10_task7_D20_seed143_init1.mp4) | 没有明显现象 |
| 7 | D21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_86ab2c896a3191b04c0b8dad42d993b0 (videos/failure/pi0_libero_10_task7_D21_seed142_init0.mp4) | - |
| 7 | D21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_8a1b8e6b354110daefe4025983f500c4 (videos/failure/pi0_libero_10_task7_D21_seed143_init1.mp4) | - |
| 8 | BASE | 142 | 0 | PASS | - | PENDING | PASS | 1 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_266e3d27fac0b5f299f48bebf459d9e3 (videos/success/pi0_libero_10_task8_BASE_seed142_init0.mp4) | - |
| 8 | BASE | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_697f9a28a07b4de868b3762030f3fc6f (videos/failure/pi0_libero_10_task8_BASE_seed143_init1.mp4) | - |
| 8 | S01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f05b3629c20037c9a50ae887156a1d02 (videos/failure/pi0_libero_10_task8_S01_seed142_init0.mp4) | - |
| 8 | S01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_950caaedb135fb04e68466b2c0df47ba (videos/failure/pi0_libero_10_task8_S01_seed143_init1.mp4) | - |
| 8 | S02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_37c497a64613d9b951d29cc9339df4eb (videos/failure/pi0_libero_10_task8_S02_seed142_init0.mp4) | - |
| 8 | S02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_9f3d5d643d0c8e1a8504644f45a0be39 (videos/failure/pi0_libero_10_task8_S02_seed143_init1.mp4) | - |
| 8 | S03 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_b2ea1a13d0a279ad40fc75a2a2c825bd (videos/failure/pi0_libero_10_task8_S03_seed142_init0.mp4) | - |
| 8 | S03 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_dffbee6b4803aee8758964e455f91f25 (videos/failure/pi0_libero_10_task8_S03_seed143_init1.mp4) | - |
| 8 | S04 | 142 | 0 | PENDING | PENDING | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1c6bcb1a7506594f37881dd6d67d313b (videos/failure/pi0_libero_10_task8_S04_seed142_init0.mp4) | 物体消失 |
| 8 | S04 | 143 | 1 | PENDING | PENDING | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_c42d38ecff62904744ea6e03b625b579 (videos/failure/pi0_libero_10_task8_S04_seed143_init1.mp4) | 物体消失 |
| 8 | S05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_53ee1516e7364c0e7585eb6c0caa1956 (videos/failure/pi0_libero_10_task8_S05_seed142_init0.mp4) | - |
| 8 | S05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bb2421d8d0930177e99af6d053389bb4 (videos/failure/pi0_libero_10_task8_S05_seed143_init1.mp4) | - |
| 8 | S06 | 142 | 0 | PENDING | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fe1863705a9b030f26dc47583efa78b4 (videos/failure/pi0_libero_10_task8_S06_seed142_init0.mp4) | - |
| 8 | S06 | 143 | 1 | PENDING | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_10d0e6a927786f88f7b2390586fb8522 (videos/failure/pi0_libero_10_task8_S06_seed143_init1.mp4) | - |
| 8 | S07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_8bd817f54982b7c7b72ba65b56348d04 (videos/failure/pi0_libero_10_task8_S07_seed142_init0.mp4) | - |
| 8 | S07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1d11d2740bdebe170513f7edc127760d (videos/failure/pi0_libero_10_task8_S07_seed143_init1.mp4) | - |
| 8 | S08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_25297126ff5e5e6777583a3fd9bf971e (videos/failure/pi0_libero_10_task8_S08_seed142_init0.mp4) | - |
| 8 | S08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_55bac197f891e5b7d7169950c8445e35 (videos/failure/pi0_libero_10_task8_S08_seed143_init1.mp4) | - |
| 8 | S09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_a5b0b6f7766e948204780884de8837c1 (videos/failure/pi0_libero_10_task8_S09_seed142_init0.mp4) | - |
| 8 | S09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2ad81637e5b372c699ecf36adce26961 (videos/failure/pi0_libero_10_task8_S09_seed143_init1.mp4) | - |
| 8 | S10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_bc042a3d258b612841f6ee3982aca1fb (videos/success/pi0_libero_10_task8_S10_seed142_init0.mp4) | - |
| 8 | S10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d2e1fc26e6a8bd0c1ec356dd996833e7 (videos/failure/pi0_libero_10_task8_S10_seed143_init1.mp4) | - |
| 8 | S11 | 142 | 0 | PENDING | PASS | PENDING | PASS | 1 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_1bc548bfc2e185d94d11f6a62db8293d (videos/success/pi0_libero_10_task8_S11_seed142_init0.mp4) | - |
| 8 | S11 | 143 | 1 | PENDING | PASS | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_de6ea47e0142e535c0d965e83277cee9 (videos/failure/pi0_libero_10_task8_S11_seed143_init1.mp4) | - |
| 8 | S12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_9eaf62530e006d34f0d64470e1388134 (videos/success/pi0_libero_10_task8_S12_seed142_init0.mp4) | - |
| 8 | S12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d9168919c0765e6c81516b7a185a9f17 (videos/failure/pi0_libero_10_task8_S12_seed143_init1.mp4) | - |
| 8 | S13 | 142 | 0 | PASS | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_c48a0b18e9ac90982eeeecd3e96c8152 (videos/failure/pi0_libero_10_task8_S13_seed142_init0.mp4) | 这是不是所有都得换成绿色 |
| 8 | S13 | 143 | 1 | PASS | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_01e20d0ca3aadda335d0cfde258638f8 (videos/failure/pi0_libero_10_task8_S13_seed143_init1.mp4) | 这是不是所有都得换成绿色 |
| 8 | S14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e2e207d5efe0b40d04954b9c0098a4ef (videos/failure/pi0_libero_10_task8_S14_seed142_init0.mp4) | - |
| 8 | S14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_6ac5b476dffc2d99894de61f927448be (videos/failure/pi0_libero_10_task8_S14_seed143_init1.mp4) | - |
| 8 | S15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_14bb6d562898922b2a172bcd3cbd6bc1 (videos/failure/pi0_libero_10_task8_S15_seed142_init0.mp4) | - |
| 8 | S15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_8d9d2c38b7976e218aa745b610fa464f (videos/failure/pi0_libero_10_task8_S15_seed143_init1.mp4) | - |
| 8 | S16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_ded2817a9c8bc433d5528c03898cc720 (videos/success/pi0_libero_10_task8_S16_seed142_init0.mp4) | - |
| 8 | S16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_d2404a6a11774a281d7b6f2bea7620bb (videos/failure/pi0_libero_10_task8_S16_seed143_init1.mp4) | - |
| 8 | S17 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_565910502c548f50454b2dfb79c458c2 (videos/failure/pi0_libero_10_task8_S17_seed142_init0.mp4) | - |
| 8 | S17 | 143 | 1 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_fd1777ee00b7357c39232f003560f40d (videos/failure/pi0_libero_10_task8_S17_seed143_init1.mp4) | - |
| 8 | S18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_6287d17780ea65426d20f90f51c582e0 (videos/failure/pi0_libero_10_task8_S18_seed142_init0.mp4) | - |
| 8 | S18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_bd30692c6b1c3761f854bc8e14faa9be (videos/failure/pi0_libero_10_task8_S18_seed143_init1.mp4) | - |
| 8 | S19 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_cde9fd0965a31fc971b5594f4a721498 (videos/success/pi0_libero_10_task8_S19_seed142_init0.mp4) | - |
| 8 | S19 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_149cf6567cafae3d42300bf301c3af52 (videos/failure/pi0_libero_10_task8_S19_seed143_init1.mp4) | - |
| 8 | S20 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f2d431512d906283b1f0fc19ba05c8d4 (videos/failure/pi0_libero_10_task8_S20_seed142_init0.mp4) | - |
| 8 | S20 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e51c306005b5fc5d1546f79bdc9d2712 (videos/failure/pi0_libero_10_task8_S20_seed143_init1.mp4) | - |
| 8 | S21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_77f4394f734a6ec99f3e6980a93e8440 (videos/success/pi0_libero_10_task8_S21_seed142_init0.mp4) | - |
| 8 | S21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1e64787a15fdbb387a1ef98a3d9e1866 (videos/failure/pi0_libero_10_task8_S21_seed143_init1.mp4) | - |
| 8 | S22 | 142 | 0 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_75b6c535f8f4b5167e160916ff7e542d (videos/failure/pi0_libero_10_task8_S22_seed142_init0.mp4) | - |
| 8 | S22 | 143 | 1 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_a6de7038b8cd2291ec8c55aa00287f60 (videos/failure/pi0_libero_10_task8_S22_seed143_init1.mp4) | - |
| 8 | D01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_e7150d40668554fd87415b8fdb172010 (videos/failure/pi0_libero_10_task8_D01_seed142_init0.mp4) | - |
| 8 | D01 | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_c37886da82a3216ebfd53cfb81f3214a (videos/failure/pi0_libero_10_task8_D01_seed143_init1.mp4) | - |
| 8 | D02 | 142 | 0 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_88e2d3e5169c6336751462c291a90e9b (videos/failure/pi0_libero_10_task8_D02_seed142_init0.mp4) | - |
| 8 | D02 | 143 | 1 | ISSUE | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_98827b657229f3b4464e9c3f9ae7cc91 (videos/failure/pi0_libero_10_task8_D02_seed143_init1.mp4) | - |
| 8 | D03 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_2eeb8fe71c1248b972c16a8118d0d215 (videos/failure/pi0_libero_10_task8_D03_seed142_init0.mp4) | - |
| 8 | D03 | 143 | 1 | PENDING | PASS | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_TRIGGERED | R003 | R003:ep_91671e6c4e7cfe37e64ab6af42a192b9 (videos/failure/pi0_libero_10_task8_D03_seed143_init1.mp4) | 未出现占用物体 |
| 8 | D04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_7b96b3d1246375758cfa2da267616bb7 (videos/failure/pi0_libero_10_task8_D04_seed142_init0.mp4) | - |
| 8 | D04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_344d9587e6b5e87b583f7731587f9727 (videos/failure/pi0_libero_10_task8_D04_seed143_init1.mp4) | - |
| 8 | D05 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_715973ab379dab3727c94de31f49a95c (videos/failure/pi0_libero_10_task8_D05_seed142_init0.mp4) | - |
| 8 | D05 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_83970919c03162cef8f5db7bc6e3f8a5 (videos/failure/pi0_libero_10_task8_D05_seed143_init1.mp4) | - |
| 8 | D06 | 142 | 0 | PASS | - | PENDING | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_9ac4d8b6a79aec3403b124aec3887f2d (videos/failure/pi0_libero_10_task8_D06_seed142_init0.mp4) | 引入了干扰物体+干扰物体移动 |
| 8 | D06 | 143 | 1 | PASS | - | PENDING | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_67c97eb931ba4290213645302ab66179 (videos/failure/pi0_libero_10_task8_D06_seed143_init1.mp4) | 引入了干扰物体+干扰物体移动d |
| 8 | D07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_b21a6f880881fc1d7be8655d4a503006 (videos/failure/pi0_libero_10_task8_D07_seed142_init0.mp4) | - |
| 8 | D07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_4413ab0510954f8e60717bdf856c3dde (videos/failure/pi0_libero_10_task8_D07_seed143_init1.mp4) | - |
| 8 | D08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_21628906a6e94ab212b8780d84bbb2ea (videos/failure/pi0_libero_10_task8_D08_seed142_init0.mp4) | - |
| 8 | D08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_8bcc380c15a976fc4639ab2622cec1cd (videos/failure/pi0_libero_10_task8_D08_seed143_init1.mp4) | - |
| 8 | D09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_12c9e67529417f06443c1bdc73104c83 (videos/failure/pi0_libero_10_task8_D09_seed142_init0.mp4) | - |
| 8 | D09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_eefb3705637668d2fa37fa112a0afb84 (videos/failure/pi0_libero_10_task8_D09_seed143_init1.mp4) | - |
| 8 | D10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_7c3f1bb09c552b86c94ada0b3ec08404 (videos/failure/pi0_libero_10_task8_D10_seed142_init0.mp4) | - |
| 8 | D10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_84d5d2f1d373ada7169406a2353ebba3 (videos/failure/pi0_libero_10_task8_D10_seed143_init1.mp4) | - |
| 8 | D11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d44892568f2f3c3834c3cca450a52681 (videos/failure/pi0_libero_10_task8_D11_seed142_init0.mp4) | - |
| 8 | D11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_060029ccd1849c872cb3c2d9752fcbbf (videos/failure/pi0_libero_10_task8_D11_seed143_init1.mp4) | - |
| 8 | D12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0ced7642709fbae652c0ba6c4ca71d5b (videos/failure/pi0_libero_10_task8_D12_seed142_init0.mp4) | - |
| 8 | D12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fa37e86c0c0d0dd249b72104bf0dbfeb (videos/failure/pi0_libero_10_task8_D12_seed143_init1.mp4) | - |
| 8 | D13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0a203ac6d6d613059d80f37e21d46a43 (videos/failure/pi0_libero_10_task8_D13_seed142_init0.mp4) | - |
| 8 | D13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_299b265b77ed6e11ae982264945d6655 (videos/failure/pi0_libero_10_task8_D13_seed143_init1.mp4) | - |
| 8 | D14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_950a280a59687880744a0ce5fc609083 (videos/failure/pi0_libero_10_task8_D14_seed142_init0.mp4) | - |
| 8 | D14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_aef3c3f35e6f3db9da8e69c7f59dc2cc (videos/failure/pi0_libero_10_task8_D14_seed143_init1.mp4) | - |
| 8 | D15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_a9e3632a9c6102ea66eff1faa742da71 (videos/success/pi0_libero_10_task8_D15_seed142_init0.mp4) | - |
| 8 | D15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_9ca512f49fc00fafc3beb2e7b89b39bb (videos/failure/pi0_libero_10_task8_D15_seed143_init1.mp4) | - |
| 8 | D16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f82d9de25262a84eb208e757e12fb408 (videos/failure/pi0_libero_10_task8_D16_seed142_init0.mp4) | - |
| 8 | D16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_250f4e596179075536f687da1d974895 (videos/failure/pi0_libero_10_task8_D16_seed143_init1.mp4) | - |
| 8 | D17 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_93833833d6fa765f0e2e20a6424e22c0 (videos/failure/pi0_libero_10_task8_D17_seed142_init0.mp4) | - |
| 8 | D17 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_2d724bb1483f363d38a17b3658f718e4 (videos/failure/pi0_libero_10_task8_D17_seed143_init1.mp4) | - |
| 8 | D18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ddc9016ba25a8b967390154a936328dd (videos/failure/pi0_libero_10_task8_D18_seed142_init0.mp4) | - |
| 8 | D18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fc1c820347db5ae6a41d0ec6c86d4470 (videos/failure/pi0_libero_10_task8_D18_seed143_init1.mp4) | - |
| 8 | D19 | 142 | 0 | PENDING | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_74d0ce506e54ce3d1f313f79d748ddb7 (videos/failure/pi0_libero_10_task8_D19_seed142_init0.mp4) | - |
| 8 | D19 | 143 | 1 | PENDING | PENDING | PASS | - | 1 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_220fb59afb1dd1cd34332ce48530a76f (videos/failure/pi0_libero_10_task8_D19_seed143_init1.mp4) | - |
| 8 | D20 | 142 | 0 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_TRIGGERED | R003 | R003:ep_1db6802c6ae8736b11b148e6d028ad69 (videos/failure/pi0_libero_10_task8_D20_seed142_init0.mp4) | 无明显现象 |
| 8 | D20 | 143 | 1 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_TRIGGERED | R003 | R003:ep_22ea3bccfd057c4eea2104bd0932dd12 (videos/failure/pi0_libero_10_task8_D20_seed143_init1.mp4) | 无明显现象 |
| 8 | D21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_58480d94d542be831290a4c47629afcc (videos/success/pi0_libero_10_task8_D21_seed142_init0.mp4) | - |
| 8 | D21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_29f15bf27d1137fe7371d8f10ca59d2e (videos/failure/pi0_libero_10_task8_D21_seed143_init1.mp4) | - |
| 9 | BASE | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_c3639164fdde24ee7b4dda53cc2a3f10 (videos/success/pi0_libero_10_task9_BASE_seed142_init0.mp4) | - |
| 9 | BASE | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_6b4aa5b7c247182c6e867cb874f0ea06 (videos/success/pi0_libero_10_task9_BASE_seed143_init1.mp4) | - |
| 9 | S01 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_12785a5616f1c4fad3ddb6084f1215aa (videos/failure/pi0_libero_10_task9_S01_seed142_init0.mp4) | - |
| 9 | S01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_30c455d6b5e06ea1f5ca6ea2fc0450ba (videos/failure/pi0_libero_10_task9_S01_seed143_init1.mp4) | - |
| 9 | S02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_091a64b78c70a731c7836a2d57edf7da (videos/failure/pi0_libero_10_task9_S02_seed142_init0.mp4) | - |
| 9 | S02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_b64a765a8f0e1f7adb7982f17a694684 (videos/failure/pi0_libero_10_task9_S02_seed143_init1.mp4) | - |
| 9 | S03 | 142 | 0 | PASS | - | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_a087172ad727580d2253181c3d97d753 (videos/failure/pi0_libero_10_task9_S03_seed142_init0.mp4) | 高度直接挡住机械臂 |
| 9 | S03 | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_71cb8853a805825170040cd43c30f105 (videos/failure/pi0_libero_10_task9_S03_seed143_init1.mp4) | - |
| 9 | S04 | 142 | 0 | PASS | - | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1638121ab6b749dba43557a3a1015d95 (videos/failure/pi0_libero_10_task9_S04_seed142_init0.mp4) | 物体消失 |
| 9 | S04 | 143 | 1 | PASS | - | PENDING | ISSUE | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_03c0c372cf799918e34bc590fe5683ed (videos/failure/pi0_libero_10_task9_S04_seed143_init1.mp4) | 物体消失 |
| 9 | S05 | 142 | 0 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_656a1632285408f422a987116ea5226f (videos/failure/pi0_libero_10_task9_S05_seed142_init0.mp4) | - |
| 9 | S05 | 143 | 1 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_e6445083aa9c1d6ed2eed4c91bca6a68 (videos/failure/pi0_libero_10_task9_S05_seed143_init1.mp4) | - |
| 9 | S06 | 142 | 0 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1ff63abf9478ac11a855748a640bd984 (videos/failure/pi0_libero_10_task9_S06_seed142_init0.mp4) | - |
| 9 | S06 | 143 | 1 | PASS | - | PENDING | PASS | 1 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_57f5c23e47caa271f86489701e66ef9c (videos/failure/pi0_libero_10_task9_S06_seed143_init1.mp4) | - |
| 9 | S07 | 142 | 0 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4148c77ee7e663db64b5b1f5a59c5a6c (videos/failure/pi0_libero_10_task9_S07_seed142_init0.mp4) | - |
| 9 | S07 | 143 | 1 | PENDING | PENDING | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_ce3482b3c7888b39627ac03303646de6 (videos/failure/pi0_libero_10_task9_S07_seed143_init1.mp4) | - |
| 9 | S08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_691f83c235b12142f78bb20ef86cbb4f (videos/success/pi0_libero_10_task9_S08_seed142_init0.mp4) | - |
| 9 | S08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_f809f773e990b276f2a793c25db923c1 (videos/success/pi0_libero_10_task9_S08_seed143_init1.mp4) | - |
| 9 | S09 | 142 | 0 | ISSUE | PENDING | PENDING | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_APPLICABLE | R003 | R003:ep_04272a57f3994aae2fd57710763c5776 (videos/failure/pi0_libero_10_task9_S09_seed142_init0.mp4) | 形变至不符合常理 |
| 9 | S09 | 143 | 1 | ISSUE | PENDING | PENDING | PENDING | 0 | ISSUE_OPEN | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_2ea3268285d90c425c9ac16a5bd72f01 (videos/success/pi0_libero_10_task9_S09_seed143_init1.mp4) | 形变至不符合常理 |
| 9 | S10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_afba846ac906d490c0bcd49974311e67 (videos/success/pi0_libero_10_task9_S10_seed142_init0.mp4) | - |
| 9 | S10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_284932f7d100ca27c203f0b65d92f050 (videos/failure/pi0_libero_10_task9_S10_seed143_init1.mp4) | - |
| 9 | S11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1e37bfd62a9a075af922298b43b4462b (videos/failure/pi0_libero_10_task9_S11_seed142_init0.mp4) | - |
| 9 | S11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_bcbc3094d06fcb82ae60a34d8f78e961 (videos/success/pi0_libero_10_task9_S11_seed143_init1.mp4) | - |
| 9 | S12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_77a8c19c9d3d9cddccfd7e5f41586718 (videos/failure/pi0_libero_10_task9_S12_seed142_init0.mp4) | - |
| 9 | S12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_1d0884fe510f53ef89ffce691a71354d (videos/success/pi0_libero_10_task9_S12_seed143_init1.mp4) | - |
| 9 | S13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_f523155e8c45541fb34dad98c05cfeee (videos/failure/pi0_libero_10_task9_S13_seed142_init0.mp4) | - |
| 9 | S13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_0029685f11663f6178c29b1635e86127 (videos/success/pi0_libero_10_task9_S13_seed143_init1.mp4) | - |
| 9 | S14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_1f6b6c46f5a98cb4e35fff0bbeaee270 (videos/failure/pi0_libero_10_task9_S14_seed142_init0.mp4) | - |
| 9 | S14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_ee34ac65a4f33511807ac8a3449c353d (videos/success/pi0_libero_10_task9_S14_seed143_init1.mp4) | - |
| 9 | S15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_3d3deee5e767bda91f9be0b9cd0edd86 (videos/failure/pi0_libero_10_task9_S15_seed142_init0.mp4) | - |
| 9 | S15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_244c8c294855bebbd85aeae66581cab2 (videos/success/pi0_libero_10_task9_S15_seed143_init1.mp4) | - |
| 9 | S16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_caed0cbbb4f1584fd33648b85e1ce220 (videos/success/pi0_libero_10_task9_S16_seed142_init0.mp4) | - |
| 9 | S16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_3408ec7bb652f1bc2a35b8daac357550 (videos/failure/pi0_libero_10_task9_S16_seed143_init1.mp4) | - |
| 9 | S17 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_5262bac2272a80d0ecd37cb076f9de0f (videos/failure/pi0_libero_10_task9_S17_seed142_init0.mp4) | - |
| 9 | S17 | 143 | 1 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_cd19984543069596ae76a6b096f4c895 (videos/failure/pi0_libero_10_task9_S17_seed143_init1.mp4) | - |
| 9 | S18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_86391a2a4f79ecb117bb9fb010fa654d (videos/failure/pi0_libero_10_task9_S18_seed142_init0.mp4) | - |
| 9 | S18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_134b468b31ea9eab0708c4b238cfbfe9 (videos/failure/pi0_libero_10_task9_S18_seed143_init1.mp4) | - |
| 9 | S19 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_a142ffc82e83fb2a14c2280fb7767fb4 (videos/failure/pi0_libero_10_task9_S19_seed142_init0.mp4) | - |
| 9 | S19 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_049726483a0ca98d3a3f04a105d56d80 (videos/failure/pi0_libero_10_task9_S19_seed143_init1.mp4) | - |
| 9 | S20 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_afe1f08335e3e052f0b921407f3bf29b (videos/failure/pi0_libero_10_task9_S20_seed142_init0.mp4) | - |
| 9 | S20 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_2100db459384701fe655f5cc480a1dbf (videos/failure/pi0_libero_10_task9_S20_seed143_init1.mp4) | - |
| 9 | S21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_1a3294ca2dc5c2ad781ca983e9bb71ec (videos/success/pi0_libero_10_task9_S21_seed142_init0.mp4) | - |
| 9 | S21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_4dfa73ad2712a29caaf910eff18401a1 (videos/failure/pi0_libero_10_task9_S21_seed143_init1.mp4) | - |
| 9 | S22 | 142 | 0 | - | - | PASS | PASS | 2 | RETEST | FAILURE | NOT_APPLICABLE | R003 | R003:ep_0a17971f35dc7c94a8cbeff234ec9ab6 (videos/failure/pi0_libero_10_task9_S22_seed142_init0.mp4) | - |
| 9 | S22 | 143 | 1 | - | - | PASS | PASS | 2 | RETEST | SUCCESS | NOT_APPLICABLE | R003 | R003:ep_b3af6837ac04374755d9c3cb9c25248f (videos/success/pi0_libero_10_task9_S22_seed143_init1.mp4) | - |
| 9 | D01 | 142 | 0 | PASS | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | NOT_TRIGGERED | R003 | R003:ep_e46f82f8f3c40c0fa2d33eb2eec282a0 (videos/failure/pi0_libero_10_task9_D01_seed142_init0.mp4) | 未出现目标移动 |
| 9 | D01 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_eeba278230a1998fabcc02ce82cbe095 (videos/failure/pi0_libero_10_task9_D01_seed143_init1.mp4) | - |
| 9 | D02 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_392ffed2e948a1c89f2adfa17161328c (videos/failure/pi0_libero_10_task9_D02_seed142_init0.mp4) | - |
| 9 | D02 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f0be9d728118309df3eb335be5a24c8c (videos/failure/pi0_libero_10_task9_D02_seed143_init1.mp4) | - |
| 9 | D03 | 142 | 0 | ISSUE | PENDING | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d8ed1449fd9a55d9def378cab33e7f00 (videos/failure/pi0_libero_10_task9_D03_seed142_init0.mp4) | - |
| 9 | D03 | 143 | 1 | ISSUE | PENDING | PENDING | PASS | 1 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_9b3010a96343ca11ef8bb31beebe19dc (videos/failure/pi0_libero_10_task9_D03_seed143_init1.mp4) | - |
| 9 | D04 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_d72a1c87fcf933dbe57b3ad227cc431d (videos/failure/pi0_libero_10_task9_D04_seed142_init0.mp4) | - |
| 9 | D04 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ee6bad88fad81c8f4509b35de1e6a2a9 (videos/failure/pi0_libero_10_task9_D04_seed143_init1.mp4) | - |
| 9 | D05 | 142 | 0 | PENDING | PASS | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ae972d9e6fc7761d9dc5cb26fd66860d (videos/failure/pi0_libero_10_task9_D05_seed142_init0.mp4) | - |
| 9 | D05 | 143 | 1 | ISSUE | PENDING | PASS | PASS | 2 | RETEST | FAILURE | TRIGGERED | R003 | R003:ep_3f1df85b22538c9d791c46214db23ff5 (videos/failure/pi0_libero_10_task9_D05_seed143_init1.mp4) | - |
| 9 | D06 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_0df35db22c8d3a4ea48406ebfc423d47 (videos/success/pi0_libero_10_task9_D06_seed142_init0.mp4) | - |
| 9 | D06 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_22f4cf5b8facd30a05ad3f55979313db (videos/failure/pi0_libero_10_task9_D06_seed143_init1.mp4) | - |
| 9 | D07 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_cc43b4df16e6e01aefcf3b74de63f6b1 (videos/failure/pi0_libero_10_task9_D07_seed142_init0.mp4) | - |
| 9 | D07 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_cc194772f17feb696434a05f6d1ffd79 (videos/failure/pi0_libero_10_task9_D07_seed143_init1.mp4) | - |
| 9 | D08 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f5a86803c6e3e60a04ff08449ca674a8 (videos/failure/pi0_libero_10_task9_D08_seed142_init0.mp4) | - |
| 9 | D08 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_1caac743e3f0b1881f7543bc8f0144f2 (videos/success/pi0_libero_10_task9_D08_seed143_init1.mp4) | - |
| 9 | D09 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ee561f0c34079a486b157d8c07634f17 (videos/failure/pi0_libero_10_task9_D09_seed142_init0.mp4) | - |
| 9 | D09 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_da182c06985f0c89029658793b680263 (videos/success/pi0_libero_10_task9_D09_seed143_init1.mp4) | - |
| 9 | D10 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_0a5e12828e062d67830c18f33b4d0116 (videos/failure/pi0_libero_10_task9_D10_seed142_init0.mp4) | - |
| 9 | D10 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_cc5d66c6064f78b53113ba615cd27d41 (videos/success/pi0_libero_10_task9_D10_seed143_init1.mp4) | - |
| 9 | D11 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_388263a0c1a7919930556b6229f28648 (videos/failure/pi0_libero_10_task9_D11_seed142_init0.mp4) | - |
| 9 | D11 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_fddb8a247317ed437a92bc5b78d17296 (videos/failure/pi0_libero_10_task9_D11_seed143_init1.mp4) | - |
| 9 | D12 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_6f4b052c92f92f66da75ca7ea0fd98e7 (videos/success/pi0_libero_10_task9_D12_seed142_init0.mp4) | - |
| 9 | D12 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_5ff14974d177cb060c208b09238642c5 (videos/success/pi0_libero_10_task9_D12_seed143_init1.mp4) | - |
| 9 | D13 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | SUCCESS | TRIGGERED | R003 | R003:ep_69fb3b116823b885e3d9862c23be2d4f (videos/success/pi0_libero_10_task9_D13_seed142_init0.mp4) | - |
| 9 | D13 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_e8c8e24beff337e917401cb8eed70066 (videos/failure/pi0_libero_10_task9_D13_seed143_init1.mp4) | - |
| 9 | D14 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_5a0e3ad633d9f0f6361545c8a3ef3fc7 (videos/failure/pi0_libero_10_task9_D14_seed142_init0.mp4) | - |
| 9 | D14 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_18698396dc3ea253db366b68ae215af9 (videos/failure/pi0_libero_10_task9_D14_seed143_init1.mp4) | - |
| 9 | D15 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f5a9d5690ebc14dbc8b13d15bd095db8 (videos/failure/pi0_libero_10_task9_D15_seed142_init0.mp4) | - |
| 9 | D15 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_bc49179f9f0372231697e4c75eee324d (videos/failure/pi0_libero_10_task9_D15_seed143_init1.mp4) | - |
| 9 | D16 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_ad08c1a0b3840660921f2f41d86a562e (videos/failure/pi0_libero_10_task9_D16_seed142_init0.mp4) | - |
| 9 | D16 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_812ba63a6fbc05ffafc2857eb1f940de (videos/failure/pi0_libero_10_task9_D16_seed143_init1.mp4) | - |
| 9 | D17 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_1233ba21be67dd6911b2aaabfe71444d (videos/failure/pi0_libero_10_task9_D17_seed142_init0.mp4) | - |
| 9 | D17 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_3838c290140469ce7f9c01f0a7d2373e (videos/failure/pi0_libero_10_task9_D17_seed143_init1.mp4) | - |
| 9 | D18 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_38449a1335468f9f97715bafe50560a6 (videos/failure/pi0_libero_10_task9_D18_seed142_init0.mp4) | - |
| 9 | D18 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_3dc21b105ba904cf69194ab14e7e09be (videos/failure/pi0_libero_10_task9_D18_seed143_init1.mp4) | - |
| 9 | D19 | 142 | 0 | PENDING | PASS | PASS | - | 2 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_cb9b655e516bc5017f80df4600139f3c (videos/failure/pi0_libero_10_task9_D19_seed142_init0.mp4) | - |
| 9 | D19 | 143 | 1 | PENDING | PASS | PASS | - | 2 | RETEST | FAILURE | TRIGGERED | R002 | R002:ep_8e1bb2a26cba0cf7d9248d2c2019e7b3 (videos/failure/pi0_libero_10_task9_D19_seed143_init1.mp4) | - |
| 9 | D20 | 142 | 0 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | FAILURE | PENDING | R003 | R003:ep_6d18ccddaf1331695435d273a595ce44 (videos/failure/pi0_libero_10_task9_D20_seed142_init0.mp4) | 未观察到明显现象 |
| 9 | D20 | 143 | 1 | - | - | PASS | PENDING | 0 | ISSUE_OPEN | SUCCESS | PENDING | R003 | R003:ep_4df3b900a0858e2249bb155e830efe47 (videos/success/pi0_libero_10_task9_D20_seed143_init1.mp4) | 未观察到明显现象 |
| 9 | D21 | 142 | 0 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_81f527a30cf90be306db3014c6373999 (videos/failure/pi0_libero_10_task9_D21_seed142_init0.mp4) | - |
| 9 | D21 | 143 | 1 | PASS | - | PASS | PASS | 3 | STABLE_3_NO_RETEST | FAILURE | TRIGGERED | R003 | R003:ep_f3fbc736ef41a55be1cc5e129a0a8758 (videos/failure/pi0_libero_10_task9_D21_seed143_init1.mp4) | - |

## 各轮非 PASS 明细

| 轮次 | Task | Case | Seed | Init | 审核结论 | 策略结果 | 扰动触发 | Episode | 备注 |
|---|---:|---|---:|---:|---|---|---|---|---|
| R001 | 5 | S07 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_eae4a33713454131b32c4282c9c99c1e | 变形后从物理角度来说也确实放不进去，但环境只要看到书在那就判成功，可能是环境本身的缺陷 |
| R001 | 5 | S07 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_d0a2a21a989545c7a094fc31d64b48e3 | 变形后从物理角度来说也确实放不进去，但环境只要看到书在那就判成功，可能是环境本身的缺陷 |
| R001 | 5 | S09 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_749bc88cefe54fef86dbe375abb30267 | 这个和s07一个问题 变化后能装的下吗 |
| R001 | 5 | S09 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_627e835143b4438fad2995edf7d91d8f | 这个和s07一个问题 变化后能装的下吗 |
| R001 | 5 | S11 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_21ea0b1c7a9948e99d31cdf892323855 | 物体初始化的时候倒了 另一个视频没问题 |
| R001 | 5 | S17 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_2118b0222dc44878b8e2d09982f922ff | 这个如果偏置的方向和正确轨迹保持一致的话其实只是帮机械臂多走了几步 影响不是很严重吧 |
| R001 | 5 | S17 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_011cae7762a64fde838d452d725b2018 | 这个如果偏置的方向和正确轨迹保持一致的话其实只是帮机械臂多走了几步 影响不是很严重吧 |
| R001 | 5 | D01 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_439a5fa0e4de4cf5a4118c791a2800ec | 书移动之后会倒掉 不符合原来的任务定义吧？ |
| R001 | 5 | D02 | 142 | 0 | ISSUE | SUCCESS | NOT_TRIGGERED | ep_7ec32b42cbaa4b9a9abcb459345ea1dd | 接收器没有移动 |
| R001 | 5 | D02 | 143 | 1 | ISSUE | SUCCESS | NOT_TRIGGERED | ep_ec1aff7d83114b33890b889ccc2f7e4c | 接收器没有移动 |
| R001 | 5 | D03 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_a74620be9f7a4575a30da898d8ce36e0 | 占用物体出现了，但是一直没有释放，并且出现的会不会太突然了 |
| R001 | 5 | D03 | 143 | 1 | ISSUE | SUCCESS | PENDING | ep_23bfc24459db489db82ee3b8c80c9316 | 占用物体没有出现 |
| R001 | 5 | D08 | 142 | 0 | PENDING | FAILURE | PENDING | ep_0ad89bd8a66641e2b4aef128740eb45f | 这会不会存在一种可能是你黑屏的时候步数还是在执行chunk的 即使黑屏也不影响，等黑屏结束就回到正确轨迹了 相当于黑屏直接无效 |
| R001 | 5 | D08 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_ae05615bf214493dbb01e6e492d78da5 | 这会不会存在一种可能是你黑屏的时候步数还是在执行chunk的 即使黑屏也不影响，等黑屏结束就回到正确轨迹了 相当于黑屏直接无效 |
| R001 | 5 | D11 | 142 | 0 | PENDING | FAILURE | PENDING | ep_a5f05b5cccfa46c7adb7747486e2aaf3 | 和丢帧的区别是什么 d10 |
| R001 | 5 | D11 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_91ae4fb3a94149fe9379b52b4ec4f2f9 | 和丢帧的区别是什么 d10 |
| R001 | 5 | D19 | 142 | 0 | PENDING | SUCCESS | PENDING | ep_9ddb2c0f6ce344b5b3261231378d8cb6 | 没看懂这个task要设计什么 |
| R001 | 5 | D19 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_bbc80c40f433408faab0e4a908ff3dd9 | 没看懂这个task要设计什么 |
| R001 | 6 | S06 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_730f8e704493497f957bf531d8a14f15 | 物体直接倒了 |
| R001 | 6 | S06 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_7434a1c482eb4d4680c86636130eee31 | 物体直接倒了 |
| R001 | 6 | S10 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_d8f9bcb3c5054bb189e8c0ae24780469 | 物体飞了 |
| R001 | 6 | S11 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_26f1e3611e5444eeb8c62c490bf6c45d | 同一个seed 和task 有一个视频有第二个干扰物 这个视频没有 |
| R001 | 6 | S12 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_ad9c6d6d3fdf4798948ad3d0a5fb26e2 | 穿模了 |
| R001 | 6 | S12 | 143 | 1 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_c4a91e388be7494ea58e6f11dc815203 | 穿模了 |
| R001 | 6 | S17 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_24ed403d73e64f0d9c8bbbe59b282c87 | 不明显 看不出区别 |
| R001 | 6 | S17 | 143 | 1 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_3021467786404b79ad4ee8c076f2bc54 | 不明显 看不出区别 |
| R001 | 6 | D03 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_834612ac1b364b24a758d59a2f7a1c8f | 依旧没有释放 |
| R001 | 6 | D03 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_aaef7366f5ba4a8389b6211635062211 | 依旧没有释放 |
| R001 | 6 | D19 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_9a1fece2e3f84680ae0e612cc2eb7b5c | 物体飞了 |
| R001 | 6 | D19 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_c587ad7305db47c58759310b77f6d5e9 | 物体飞了 |
| R001 | 7 | S06 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_18d87e57c6914e139b69dcdf1f3ec53c | 物品一开始就倒了 |
| R001 | 7 | S06 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_d79aadc1d672495b8ff06a15d884573d | 物品一开始就倒了 |
| R001 | 7 | S10 | 142 | 0 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_550edddab9794becb4fc48ff2c2cef0d | 杂物没有出现 |
| R001 | 7 | S10 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_5f1a3968ac874e6aa578cfb448d6433f | 杂物没有出现 |
| R001 | 7 | S17 | 142 | 0 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_6602ab8d7da745e8bf8df4f3c229e91c | 不明显 |
| R001 | 7 | S17 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_c4299e963fad4e7db9aa49011cb1f870 | 不明显 |
| R001 | 7 | D02 | 142 | 0 | ISSUE | FAILURE | NOT_TRIGGERED | ep_6b4a8a4a57944660a82621e0b8251fb7 | 容器没移动 是因为第一个没抓取吗 |
| R001 | 7 | D02 | 143 | 1 | ISSUE | FAILURE | NOT_TRIGGERED | ep_e89c78560b394840acca7e7586ba5e01 | 容器没移动 是因为第一个没抓取吗 |
| R001 | 7 | D03 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_b3ac8652b02741a4ab32c9ce9f1c764b | 还是没释放 |
| R001 | 7 | D03 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_ec39bcaa10e34d7b933bdbdaf7a76dd5 | 还是没释放 |
| R001 | 7 | D05 | 142 | 0 | PENDING | FAILURE | PENDING | ep_00e4c9ff7a634c758f25d47bc1b4d716 | 这个没有出现障碍物 是因为要抓取到才出现吗 |
| R001 | 7 | D05 | 143 | 1 | PENDING | FAILURE | PENDING | ep_2e435b4a93904a508d488ac3c67003d5 | 这个加入了不释放是吗 |
| R001 | 7 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_44f4a0d6ae014923b5c5f0363856b6f4 | 这个任务太奇怪了 |
| R001 | 7 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_b8850720747743dcbddc5606f542ef19 | 这个任务太奇怪了 |
| R001 | 8 | S04 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_2706138d4516411296a4b060ccb3fc31 | 同样的物体交换位置是base |
| R001 | 8 | S04 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_6da3beb5aa534f299db4dbc7a960cb4a | 同样的物体交换位置是base |
| R001 | 8 | S06 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_e6c91f672b144105ba75da68dd0e18ab | 这也不是同类新实例吧 |
| R001 | 8 | S06 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_25b7b099b62948f5a2f4bbc59e71b7a1 | 这也不是同类新实例吧 |
| R001 | 8 | S11 | 142 | 0 | PENDING | SUCCESS | NOT_APPLICABLE | ep_54335e6561b94a0983dcd4ea697dcca4 | 不是同类杂物吧 |
| R001 | 8 | S11 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_96a8298b4abd4d22a52e3c3aa949bc6d | 不是同类杂物吧 |
| R001 | 8 | S17 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_1c98abf121fd4ceaafcab5e7ae81a487 | 不明显 |
| R001 | 8 | S17 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_cae67928b1eb44b981760e9eee48ae7c | 不明显 |
| R001 | 8 | D02 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_ac0f988ad220493aa0a7500971200485 | 未移动 |
| R001 | 8 | D02 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_152f872907894e2cbba497d82f88f33a | 未移动 |
| R001 | 8 | D03 | 142 | 0 | PENDING | FAILURE | PENDING | ep_e8f9931f64a3479891ddc0f197fb06de | rollout没有出现占用物品，可能是因为没有抓到摩卡壶导致的 |
| R001 | 8 | D03 | 143 | 1 | PENDING | FAILURE | PENDING | ep_51ac0d66f3754d539f552aa26cb01834 | rollout没有出现占用物品，可能是因为没有抓到摩卡壶导致的 |
| R001 | 8 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_fd553fbcfa7d44c39d8c086b80b10536 | 不确定是不是task问题 因为没抓起来 |
| R001 | 8 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_a9f7043da8da4a118d998f04da209823 | 不确定是不是task问题 因为没抓起来 |
| R001 | 9 | S05 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_dd363c4ef1684c1f8b6fd27395460027 | 这个路径不一定能放进去吧 大小 |
| R001 | 9 | S05 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_14f69a6566fd4aca9f1a818b5f5df7ea | 这个路径不一定能放进去吧 大小 |
| R001 | 9 | S07 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_11b902089bf2469cad899a5030aab9af | 这是不是不符合真实场景 |
| R001 | 9 | S07 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_21d9a5da304d4335bd470f497452eced | 这是不是不符合真实场景 |
| R001 | 9 | S09 | 142 | 0 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_8356fe6564694899893fb613b70f7b76 | 不符合真实场景 ，穿模 |
| R001 | 9 | S09 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_0eb81a3f89a94534810aac318f7ec761 | 不符合真实场景 |
| R001 | 9 | S17 | 142 | 0 | PENDING | SUCCESS | NOT_APPLICABLE | ep_f80fa2c25f674e1f9dfa030b31f5c0bd | 不明显 |
| R001 | 9 | S17 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_64052c2fa38b4892a7cd42b2c2599252 | 不明显d |
| R001 | 9 | D03 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_3c455121a4f44e5398d59dc1eca1f14e | 无占用物，然后没释放 |
| R001 | 9 | D03 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_9133a10d0bc74d23a340aa4ae3b8e85b | 无占用物，然后没释放 |
| R001 | 9 | D05 | 142 | 0 | PENDING | FAILURE | NOT_TRIGGERED | ep_e788f0dfaf4a48d3b9cf586ed4a55a36 | 可能因为没抓取所以没出现障碍物 |
| R001 | 9 | D05 | 143 | 1 | ISSUE | FAILURE | PENDING | ep_c5326e03b3b94deb838a7aa54cb89f13 | 这个没有留无碰撞成功路径 直接封死了 |
| R001 | 9 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_201883b100724552ba38914715e50283 | 不知道是task问题还是什么问题 看不出效果 |
| R001 | 9 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_d4d4da9859984dc9bb9f4cc54a5c8dcf | 不知道是task问题还是什么问题 看不出效果 |
| R001-补审 | 5 | S07 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_7748705edb0d3c03c71a7b9e1598afa2 | 这个好像书还是无法正常放进去 口不够大？ |
| R001-补审 | 5 | S07 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_58356b5e49b1ac5b1b8e563613f99827 | 这个好像书还是无法正常放进去 口不够大？ |
| R001-补审 | 5 | S09 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_ec5c7c425100e9fbd55129ac777beeca | 书放进去了依然没有判定成功（另一个视频） |
| R001-补审 | 5 | S09 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_0612dbe593292bab7c8eb21a4f694e1a | 书放进去了依然没有判定成功 |
| R001-补审 | 5 | S11 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_1971a3b4f2b9927632bb86b5a68bc0cf | 这里书没出来 |
| R001-补审 | 5 | S17 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_b55d51ddb8b2c0375bb314c4d01e1b2a | 我还是觉得这个初始化角度有点问题 赶紧不是很明显 |
| R001-补审 | 5 | S17 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_9cea9ae4fb2a900eec238e579cc134ff | 我还是觉得这个初始化角度有点问题 赶紧不是很明显 |
| R001-补审 | 6 | S17 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_cbef0ebb5be4e74fbde3006e72519933 | 同样问题 我觉得初始化区别不大 |
| R001-补审 | 6 | S17 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_6a56883e189a1da5a65553fc62dea809 | 同样问题 我觉得初始化区别不大 |
| R001-补审 | 6 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_8e188af3a9aadb15c606474320d9c760 | 这个和物品突然掉落好像没啥区别 |
| R001-补审 | 6 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_a819bb280c94c903c7d397d2d1b7f1e0 | 这个和物品突然掉落好像没啥区别 |
| R001-补审 | 7 | S17 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_5276234530fe0b91caa109f2ce2341c7 | 不够明显 |
| R001-补审 | 7 | S17 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_c866eaf7a694840e7379b49b5db5d016 | 不够明显 |
| R001-补审 | 7 | D02 | 142 | 0 | PENDING | FAILURE | PENDING | ep_b917c2d51923aedc088ba07cac9b4b75 | 接收器移动会影响下一个物体抓取 |
| R001-补审 | 7 | D02 | 143 | 1 | PENDING | FAILURE | PENDING | ep_929cf9f40f3b901320ba6a23b38ce799 | 变化时机很奇怪 |
| R001-补审 | 7 | D05 | 142 | 0 | PENDING | SUCCESS | PENDING | ep_b133440fb3d514fc3252b2fee9125dfd | 还没运输就已经消失了 持续时间有点短 |
| R001-补审 | 7 | D05 | 143 | 1 | PENDING | FAILURE | PENDING | ep_12b34a75aacfecbf16292125d14e192c | 还没运输就已经消失了 持续时间有点短d |
| R001-补审 | 7 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_83021b981c3f4fb33cc84b67e9608877 | 和物品掉落的区别是什么 |
| R001-补审 | 7 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_2413a67ce32deeae1312f3eafe6a89b0 | 和物品掉落的区别是什么d |
| R001-补审 | 8 | S04 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_01ea4dd9e15a1efbde1fde79c4157974 | 两个物体一样 交换位置不是严格意义交换 因为有一个壶出去了 引入了新的变量 |
| R001-补审 | 8 | S04 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_37915ab09a1d373f21518708fc0dd726 | 两个物体一样 交换位置不是严格意义交换 因为有一个壶出去了 引入了新的变量 |
| R001-补审 | 8 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_408c8a6c608b7829609b825b3e4b3393 | 和物品掉下来的区别是什么 |
| R001-补审 | 8 | D19 | 143 | 1 | PENDING | FAILURE | PENDING | ep_45092f0fbe380b0ca74dff58a84466cd | 和物品掉下来的区别是什么 |
| R001-补审 | 9 | S05 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_d68ca9437fff6fabc3d1f27976cf9490 | 两次rollout放置位置不同d |
| R001-补审 | 9 | S05 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_b7b510fa44dafe6269ad0b6d49035769 | 两次rollout放置位置不同 |
| R001-补审 | 9 | S07 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_bcc791b9f51366142934db5ba6c1fbe7 | 不符合真实场景 |
| R001-补审 | 9 | S07 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_61b189f8893bed9d4c1b74f8a0e38315 | 不符合真实场景 |
| R001-补审 | 9 | S09 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_ce45e69064920158cba62ce364447d10 | 不符合真实场景 |
| R001-补审 | 9 | S09 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_3ff0853379594468a9cc6713b4159eed | 不符合真实场景 |
| R001-补审 | 9 | D03 | 142 | 0 | PENDING | FAILURE | PENDING | ep_0d3cac88168aa336cfa54427f7c6f5ce | 这个不是接收区域 |
| R001-补审 | 9 | D03 | 143 | 1 | PENDING | FAILURE | PENDING | ep_0d547d8bc0d30f4e3e5fbdd1c10006ce | 这个不是接收区域 |
| R001-补审 | 9 | D05 | 143 | 1 | PENDING | FAILURE | PENDING | ep_38ac5ef1797efaea350685d5aa879963 | 进入的位置两次rollout不一样 |
| R002 | 5 | S09 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_f13b683c840abaa35fb83deae0f3efd0 | 完整放入没有正间隙 |
| R002 | 5 | S09 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_b24d37df5756b7cffd9107de0e2267c0 | 完整放入没有正间隙 |
| R002 | 5 | S22 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_956eaa4d070855f84851137eb3b55c2b | s22是不是不存在了 |
| R002 | 5 | S22 | 143 | 1 | ISSUE | SUCCESS | NOT_APPLICABLE | ep_c6df236d4585bec7cfce6ca207c49a43 | s22是不是不存在了 |
| R002 | 5 | D01 | 143 | 1 | PENDING | FAILURE | PENDING | ep_072448ea2c23d6f41b8c21f2dbd63e9e | 移动后已经撞到柜子了 |
| R002 | 5 | D02 | 142 | 0 | PENDING | SUCCESS | NOT_TRIGGERED | ep_e1f6db23e89ef41e5ea1c23a6c357e1c | 接收器没移动 |
| R002 | 5 | D03 | 143 | 1 | ISSUE | SUCCESS | PENDING | ep_cb2e4ff52d438644dd949cd88985fe5c | 没有接受区域物体占用 |
| R002 | 5 | D13 | 142 | 0 | PENDING | SUCCESS | PENDING | ep_93d3d41b726206f0f78bc01cc29e7686 | 看不出来 |
| R002 | 5 | D13 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_289d812eba9e53a42a7e3ff97887dc6c | 看不出来 |
| R002 | 5 | D19 | 142 | 0 | PENDING | FAILURE | PENDING | ep_682fc8b53293f15cae75bdcd62ae1d50 | 没懂这个任务在干啥 |
| R002 | 5 | D19 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_b60a4fd8a298b1aa4c46cc243e6c17f5 | 没懂 |
| R002 | 5 | D20 | 142 | 0 | PENDING | FAILURE | PENDING | ep_1e1318c02d47914a6d1589dd636b4669 | 没有这个编号了 |
| R002 | 5 | D20 | 143 | 1 | PENDING | FAILURE | PENDING | ep_2700d00e8c23819885586ac665e67ce6 | 没有这个编号了 |
| R002 | 6 | S06 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_349eb97ad2770a57dd002359037a8b47 | 同类实例太小了 抓不起来吧 |
| R002 | 6 | S06 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_6404df574d4b35ff3cf687c1a0342f3a | 同类实例太小了 抓不起来吧 |
| R002 | 6 | S12 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_33890519269bbdad1d1a07dccf70fe58 | 穿模 |
| R002 | 6 | S12 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_41ac129ad9414bd884ebba1a7e2c6de6 | 穿模 |
| R002 | 7 | S04 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_24ec88a1b7eb7406992800f7ea8f6231 | 物体交换位置和base的基础位置不同， |
| R002 | 7 | S04 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_80847f033e08d8010965b18f0f56305b | 物体交换位置和base的基础位置不同， |
| R002 | 7 | S06 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_95d7e870ddf74d78441ca8146014c5a8 | 太小了抓不起来 |
| R002 | 7 | S06 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_3ae106b4879bc79f84a393e19e7fb226 | 太小了抓不起来 |
| R002 | 8 | BASE | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_47b9e11edf931cfe379c6377a571e4cd | rollout有问题 |
| R002 | 8 | BASE | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_d12c1d2aa74c44300444b6fc28a2192b | rollout有问题 |
| R002 | 8 | S04 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_a61c3af79f7a9476c715d411c219fdb1 | 这个还是没解决 |
| R002 | 8 | S04 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_0a32b95846517dc209bca45052d29e40 | 这个还是没解决 |
| R002 | 8 | S06 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_2a58d8cabb727e04f89647ec7426489c | 这也不是同类实例 |
| R002 | 8 | S06 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_8af68dca46bb95663a8364dd8b8c11d7 | 这也不是同类实例 |
| R002 | 8 | S11 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_18b20fdd1d7aa619db9ede2c5d68c2f3 | 非同类 |
| R002 | 8 | S11 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_b294cb692cd7f83116924db814c8add7 | 非同类 |
| R002 | 8 | D01 | 143 | 1 | PENDING | FAILURE | PENDING | ep_afd73ac70eb1eb08360d61f741ddb9ac | rollout不够长 |
| R002 | 8 | D06 | 142 | 0 | PENDING | FAILURE | PENDING | ep_93d4f34c26699dd61f5dd2d7165d9989 | 不存在干扰物 |
| R002 | 8 | D06 | 143 | 1 | PENDING | FAILURE | PENDING | ep_65506425c741a17008668d08e4b672d3 | 不存在干扰物 |
| R002 | 9 | S03 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_337b317645643d99c87112d50166d712 | 会直接碰撞 |
| R002 | 9 | S03 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_5d6291c709f1f89049ac219543551b6b | 穿模 |
| R002 | 9 | S04 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_a66895aac1457b5a21c6e376ee9a3914 | 交换位置不严格 |
| R002 | 9 | S04 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_aa6ab575720bc5d9d77bce20a6e45bc2 | 交换位置不严格d |
| R002 | 9 | S06 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_722813b9182040559c703dbec8cff959 | 物体太小抓不到 |
| R002 | 9 | S06 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_65efc7f2036d6cae31d7fe715bde1e5c | 物体太小抓不到 |
| R002 | 9 | S09 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_bf3199a31f8d3ba5adecea1cbabf1da9 | 不够大放进去 |
| R002 | 9 | S09 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_c5fec0dfb82e2de4a5fe2e6347f10ddd | 不够大放进去，且出现穿模 |
| R002 | 9 | D03 | 142 | 0 | PENDING | FAILURE | PENDING | ep_4ce0bbfe8140b99dbe402ca2807be175 | 没有物体占用 |
| R002 | 9 | D03 | 143 | 1 | PENDING | FAILURE | PENDING | ep_92db1a77fcefd81719136b3e321dafe1 | 没有物体占用 |
| R003 | 5 | S10 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_cc9fcfb257962a88d52017173d17d9cc | 穿模 |
| R003 | 5 | D02 | 142 | 0 | ISSUE | SUCCESS | NOT_TRIGGERED | ep_bd5f6f581572f34f52de3f8b75a93395 | 接收器没移动 |
| R003 | 5 | D02 | 143 | 1 | ISSUE | SUCCESS | NOT_TRIGGERED | ep_e8d3d20af7df93390a8da28e33c14ce1 | 接收器没移动 |
| R003 | 5 | D03 | 142 | 0 | ISSUE | SUCCESS | PENDING | ep_ce69627b6bccdaab29952f97db86c16d | 占用了判定成功，但是没有完全放进去，仿真环境问题 |
| R003 | 6 | S12 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_9d98c9b2d75affd3c03aafcad9bb7a23 | 穿模 |
| R003 | 6 | D03 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_c18c4063dfd9e443f042acfbfb1922d1 | 占用物体出现的位置非接收区域 |
| R003 | 6 | D03 | 143 | 1 | ISSUE | FAILURE | NOT_TRIGGERED | ep_382279bdce0ef6d0402b3694a830832a | 未出现占用物体 |
| R003 | 6 | D04 | 142 | 0 | PENDING | FAILURE | PENDING | ep_a60e62d2bf9781dad98229c57132a674 | 穿模 |
| R003 | 6 | D20 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_2bb7647f321405e37a67b6ec51b510e8 | 没观察到回退 |
| R003 | 7 | D05 | 142 | 0 | ISSUE | FAILURE | PENDING | ep_7645ca0b4fd13782134cd88cc9f5fbfd | 非运输路径 |
| R003 | 7 | D20 | 142 | 0 | PENDING | FAILURE | PENDING | ep_64dd879fb6a514e314564a2e7a29e9b4 | 没有明显现象 |
| R003 | 7 | D20 | 143 | 1 | PENDING | FAILURE | PENDING | ep_ea59fbdcd9eec4124066d881af24b01e | 没有明显现象 |
| R003 | 8 | S04 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_1c6bcb1a7506594f37881dd6d67d313b | 物体消失 |
| R003 | 8 | S04 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_c42d38ecff62904744ea6e03b625b579 | 物体消失 |
| R003 | 8 | S13 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_c48a0b18e9ac90982eeeecd3e96c8152 | 这是不是所有都得换成绿色 |
| R003 | 8 | S13 | 143 | 1 | PENDING | FAILURE | NOT_APPLICABLE | ep_01e20d0ca3aadda335d0cfde258638f8 | 这是不是所有都得换成绿色 |
| R003 | 8 | D03 | 143 | 1 | PENDING | FAILURE | NOT_TRIGGERED | ep_91671e6c4e7cfe37e64ab6af42a192b9 | 未出现占用物体 |
| R003 | 8 | D06 | 142 | 0 | PENDING | FAILURE | PENDING | ep_9ac4d8b6a79aec3403b124aec3887f2d | 引入了干扰物体+干扰物体移动 |
| R003 | 8 | D06 | 143 | 1 | PENDING | FAILURE | PENDING | ep_67c97eb931ba4290213645302ab66179 | 引入了干扰物体+干扰物体移动d |
| R003 | 8 | D20 | 142 | 0 | PENDING | FAILURE | NOT_TRIGGERED | ep_1db6802c6ae8736b11b148e6d028ad69 | 无明显现象 |
| R003 | 8 | D20 | 143 | 1 | PENDING | FAILURE | NOT_TRIGGERED | ep_22ea3bccfd057c4eea2104bd0932dd12 | 无明显现象 |
| R003 | 9 | S03 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_a087172ad727580d2253181c3d97d753 | 高度直接挡住机械臂 |
| R003 | 9 | S04 | 142 | 0 | ISSUE | FAILURE | NOT_APPLICABLE | ep_1638121ab6b749dba43557a3a1015d95 | 物体消失 |
| R003 | 9 | S04 | 143 | 1 | ISSUE | FAILURE | NOT_APPLICABLE | ep_03c0c372cf799918e34bc590fe5683ed | 物体消失 |
| R003 | 9 | S09 | 142 | 0 | PENDING | FAILURE | NOT_APPLICABLE | ep_04272a57f3994aae2fd57710763c5776 | 形变至不符合常理 |
| R003 | 9 | S09 | 143 | 1 | PENDING | SUCCESS | NOT_APPLICABLE | ep_2ea3268285d90c425c9ac16a5bd72f01 | 形变至不符合常理 |
| R003 | 9 | D01 | 142 | 0 | PENDING | FAILURE | NOT_TRIGGERED | ep_e46f82f8f3c40c0fa2d33eb2eec282a0 | 未出现目标移动 |
| R003 | 9 | D20 | 142 | 0 | PENDING | FAILURE | PENDING | ep_6d18ccddaf1331695435d273a595ce44 | 未观察到明显现象 |
| R003 | 9 | D20 | 143 | 1 | PENDING | SUCCESS | PENDING | ep_4df3b900a0858e2249bb155e830efe47 | 未观察到明显现象 |

## 后续复测队列

| 优先级 | Task | Case | Seed | Init | 原因 |
|---|---:|---|---:|---:|---|
| P2 | 5 | S07 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 5 | S07 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 5 | S09 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | S09 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 5 | S10 | 142 | 0 | 穿模 |
| P2 | 5 | S11 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 5 | S17 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 5 | S17 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 5 | S22 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | S22 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | D01 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 5 | D02 | 142 | 0 | 接收器没移动 |
| P0 | 5 | D02 | 143 | 1 | 接收器没移动 |
| P0 | 5 | D03 | 142 | 0 | 占用了判定成功，但是没有完全放进去，仿真环境问题 |
| P2 | 5 | D03 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | D13 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | D13 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 5 | D19 | 142 | 0 | 没懂这个任务在干啥 |
| P0 | 5 | D19 | 143 | 1 | 没懂 |
| P2 | 5 | D20 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 5 | D20 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 6 | S06 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 6 | S06 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 6 | S12 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 6 | S12 | 143 | 1 | 穿模 |
| P2 | 6 | S17 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 6 | S17 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 6 | S22 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 6 | S22 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 6 | D03 | 142 | 0 | 占用物体出现的位置非接收区域 |
| P0 | 6 | D03 | 143 | 1 | 未出现占用物体 |
| P0 | 6 | D04 | 142 | 0 | 穿模 |
| P2 | 6 | D19 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 6 | D19 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 6 | D20 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 6 | D20 | 143 | 1 | 没观察到回退 |
| P2 | 7 | S04 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 7 | S04 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 7 | S06 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 7 | S06 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 7 | S17 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | S17 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | S22 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | S22 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | D02 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | D02 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 7 | D05 | 142 | 0 | 非运输路径 |
| P2 | 7 | D05 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 7 | D19 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 7 | D19 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 7 | D20 | 142 | 0 | 没有明显现象 |
| P0 | 7 | D20 | 143 | 1 | 没有明显现象 |
| P2 | 8 | BASE | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 8 | BASE | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 8 | S04 | 142 | 0 | 物体消失 |
| P0 | 8 | S04 | 143 | 1 | 物体消失 |
| P2 | 8 | S06 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 8 | S06 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 8 | S11 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 8 | S11 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 8 | S13 | 142 | 0 | 这是不是所有都得换成绿色 |
| P0 | 8 | S13 | 143 | 1 | 这是不是所有都得换成绿色 |
| P2 | 8 | S22 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 8 | S22 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 8 | D01 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 8 | D03 | 143 | 1 | 未出现占用物体 |
| P0 | 8 | D06 | 142 | 0 | 引入了干扰物体+干扰物体移动 |
| P0 | 8 | D06 | 143 | 1 | 引入了干扰物体+干扰物体移动d |
| P2 | 8 | D19 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 8 | D19 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 8 | D20 | 142 | 0 | 无明显现象 |
| P0 | 8 | D20 | 143 | 1 | 无明显现象 |
| P0 | 9 | S03 | 142 | 0 | 高度直接挡住机械臂 |
| P2 | 9 | S03 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P0 | 9 | S04 | 142 | 0 | 物体消失 |
| P0 | 9 | S04 | 143 | 1 | 物体消失 |
| P2 | 9 | S05 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | S05 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | S06 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 9 | S06 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 9 | S07 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | S07 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 9 | S09 | 142 | 0 | 形变至不符合常理 |
| P0 | 9 | S09 | 143 | 1 | 形变至不符合常理 |
| P2 | 9 | S22 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | S22 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 9 | D01 | 142 | 0 | 未出现目标移动 |
| P2 | 9 | D03 | 142 | 0 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 9 | D03 | 143 | 1 | 连续 PASS 仅 1 次，尚未达到 3 次 |
| P2 | 9 | D05 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | D19 | 142 | 0 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P2 | 9 | D19 | 143 | 1 | 连续 PASS 仅 2 次，尚未达到 3 次 |
| P0 | 9 | D20 | 142 | 0 | 未观察到明显现象 |
| P0 | 9 | D20 | 143 | 1 | 未观察到明显现象 |

---

## R004 定向复审记录

> 负责人：Junhao Wu<br>
> 审核日期：2026-09-03<br>
> 数据批次：`0902rollout` / `pi0-review-final-20260902-51bb70b`<br>
> rollout commit：`51bb70b8f32dde58b61f53b4afe65bd18985f348`

### 范围与证据

本轮是问题项定向复审，不是全量审核。覆盖 `libero_10/task5-task9` 共 39 个 task/case 组、78 个独立 rollout；每组包含 seed142/init0 与 seed143/init1 两次尝试。未出现在本批次中的稳定项不视为漏审，也不新增审核结论。

- 结果文件 SHA-256：`6d542ad2560b018bb09e266fad241789857d8036e5704eafc522598dd22f0025`
- 原始结果：`human_review_results.csv`（第五版人工审核交付）
- 视频与 episode 对应：同批次 `review_manifest.csv`

### 审核结果汇总

| 结论 | 数量 | 占比 |
|---|---:|---:|
| 认可 | 64 | 82.1% |
| 错误 | 8 | 10.3% |
| 存疑 | 6 | 7.7% |
| 异常 | 0 | 0.0% |
| 合计 | 78 | 100.0% |

| Task | 组数 | PASS | ISSUE | PENDING |
|---:|---:|---:|---:|---:|
| 5 | 7 | 12 | 0 | 2 |
| 6 | 8 | 12 | 2 | 2 |
| 7 | 8 | 14 | 2 | 0 |
| 8 | 7 | 12 | 0 | 2 |
| 9 | 9 | 14 | 4 | 0 |

### R004 逐 rollout 记录

| Review Key | 策略结果 | 触发状态 | 审核判定 | Episode ID | 视频证据 | 备注 |
|---|---|---|---|---|---|---|
| `libero_10/task5/D01/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_28c66038f30fde5722f2c96d90564af9` | `videos/failure/pi0_libero_10_task5_D01_seed142_init0.mp4` | - |
| `libero_10/task5/D01/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_89713bee3e04206c99eb86431efeb18a` | `videos/failure/pi0_libero_10_task5_D01_seed143_init1.mp4` | - |
| `libero_10/task5/D02/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_2b1809e8b09174ce393bc9c109afc2fb` | `videos/failure/pi0_libero_10_task5_D02_seed142_init0.mp4` | - |
| `libero_10/task5/D02/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_c07f55551fe1b398388ab41f70615a34` | `videos/failure/pi0_libero_10_task5_D02_seed143_init1.mp4` | - |
| `libero_10/task5/D03/seed142/init0` | `SUCCESS` | `TRIGGERED` | `PENDING` | `ep_7401e52b11c6181e0a1c15ddce6c5b13` | `videos/success/pi0_libero_10_task5_D03_seed142_init0.mp4` | 占用物体不在正确接受区域 出现一下就没了 |
| `libero_10/task5/D03/seed143/init1` | `SUCCESS` | `TRIGGERED` | `PENDING` | `ep_77b23f0b6aad286a280ffadd068e5e41` | `videos/success/pi0_libero_10_task5_D03_seed143_init1.mp4` | 占用物体不在正确接受区域 出现一下就没了 |
| `libero_10/task5/S09/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_e4b332a8168a95652fa3cdecb459690b` | `videos/success/pi0_libero_10_task5_S09_seed142_init0.mp4` | - |
| `libero_10/task5/S09/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_59ac9fa364ce4d2cc3b3996f098df40a` | `videos/failure/pi0_libero_10_task5_S09_seed143_init1.mp4` | - |
| `libero_10/task5/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_84ce7c998c8da5fa21b841dc030c02f7` | `videos/failure/pi0_libero_10_task5_S10_seed142_init0.mp4` | - |
| `libero_10/task5/S10/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_9451c84b6ce340dd6593ce71c7ded9b6` | `videos/success/pi0_libero_10_task5_S10_seed143_init1.mp4` | - |
| `libero_10/task5/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_9cabfd79c4e3f61115ffa6fbff5d213d` | `videos/failure/pi0_libero_10_task5_S11_seed142_init0.mp4` | - |
| `libero_10/task5/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_994c59bc38776a70952a372a0d86596a` | `videos/failure/pi0_libero_10_task5_S11_seed143_init1.mp4` | - |
| `libero_10/task5/S22/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_544d4a46035da6c9090a002bc3756163` | `videos/success/pi0_libero_10_task5_S22_seed142_init0.mp4` | - |
| `libero_10/task5/S22/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_93b4108773082074c07f183f1057dd03` | `videos/success/pi0_libero_10_task5_S22_seed143_init1.mp4` | - |
| `libero_10/task6/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `PENDING` | `ep_9df7c3213aabb5bcddf764dcb2268906` | `videos/failure/pi0_libero_10_task6_D03_seed142_init0.mp4` | 占用物品未消失 而且这个和base有区别 |
| `libero_10/task6/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PENDING` | `ep_2f6201fcb31506670918653cc039bb33` | `videos/failure/pi0_libero_10_task6_D03_seed143_init1.mp4` | 占用物品未消失 而且这个和base有区别 |
| `libero_10/task6/D04/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_ef39b99edb1c266e0a990e7aecbc52ab` | `videos/failure/pi0_libero_10_task6_D04_seed142_init0.mp4` | - |
| `libero_10/task6/D04/seed143/init1` | `SUCCESS` | `TRIGGERED` | `PASS` | `ep_43de8cea4e6fe07ba6bfd1d4def3a6a9` | `videos/success/pi0_libero_10_task6_D04_seed143_init1.mp4` | - |
| `libero_10/task6/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_26edb21a14f9d249218e945809ccdc57` | `videos/failure/pi0_libero_10_task6_D20_seed142_init0.mp4` | - |
| `libero_10/task6/D20/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_74592f7eeebb34aa2dd493af9572f8b2` | `videos/failure/pi0_libero_10_task6_D20_seed143_init1.mp4` | - |
| `libero_10/task6/S06/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_0fe081fa6f3c90a9c3b589aef59ce6ef` | `videos/failure/pi0_libero_10_task6_S06_seed142_init0.mp4` | - |
| `libero_10/task6/S06/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_de55b99865e7588635d4e87a2e1a4224` | `videos/failure/pi0_libero_10_task6_S06_seed143_init1.mp4` | - |
| `libero_10/task6/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_b93f37c26787f64e844c686d3b0c7051` | `videos/failure/pi0_libero_10_task6_S10_seed142_init0.mp4` | - |
| `libero_10/task6/S10/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_c9a0c64dd65335e13bdf4cff0a138628` | `videos/success/pi0_libero_10_task6_S10_seed143_init1.mp4` | - |
| `libero_10/task6/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_bcd47753cef3797abf95429ee1879ec1` | `videos/failure/pi0_libero_10_task6_S11_seed142_init0.mp4` | - |
| `libero_10/task6/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_f49d2900caa37c24286f16b562def996` | `videos/failure/pi0_libero_10_task6_S11_seed143_init1.mp4` | - |
| `libero_10/task6/S12/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `ep_5188aee68bcf53aa05e9d719c0b7450b` | `videos/failure/pi0_libero_10_task6_S12_seed142_init0.mp4` | 穿模 |
| `libero_10/task6/S12/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `ep_e7e6d789781df0899a7b62f3fe307cfd` | `videos/failure/pi0_libero_10_task6_S12_seed143_init1.mp4` | 穿模 |
| `libero_10/task6/S17/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_270e982ad9c042c66870fe3af9f63298` | `videos/failure/pi0_libero_10_task6_S17_seed142_init0.mp4` | - |
| `libero_10/task6/S17/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_1fbf885b28e49eb89d072ff821626730` | `videos/failure/pi0_libero_10_task6_S17_seed143_init1.mp4` | - |
| `libero_10/task7/D02/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_7aa01b3aed753ac78f6eb88b26f5f30c` | `videos/failure/pi0_libero_10_task7_D02_seed142_init0.mp4` | - |
| `libero_10/task7/D02/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_fc0b462b9056e3c96ff691cb2cc72353` | `videos/failure/pi0_libero_10_task7_D02_seed143_init1.mp4` | - |
| `libero_10/task7/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `ISSUE` | `ep_f8f3568ef4561664b62968dbfbaa8076` | `videos/failure/pi0_libero_10_task7_D03_seed142_init0.mp4` | 这个我记得base是有红色罐子的？怎么现在红色罐子变成临时占用物体了，同时占用后不会消失 |
| `libero_10/task7/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `ISSUE` | `ep_24303610baa21b72fea2abd187843440` | `videos/failure/pi0_libero_10_task7_D03_seed143_init1.mp4` | 这个我记得base是有红色罐子的？怎么现在红色罐子变成临时占用物体了，同时占用后不会消失 |
| `libero_10/task7/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_97eb024ab2e327e603c2dde46506716f` | `videos/failure/pi0_libero_10_task7_D05_seed142_init0.mp4` | - |
| `libero_10/task7/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_ae7748bf7961d108c779c81dee132c83` | `videos/failure/pi0_libero_10_task7_D05_seed143_init1.mp4` | - |
| `libero_10/task7/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_16f2d708a9ad2d262edde1d723c8c252` | `videos/failure/pi0_libero_10_task7_D20_seed142_init0.mp4` | - |
| `libero_10/task7/D20/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_69556b9e64f3054b6a818be3f2c2bdd6` | `videos/failure/pi0_libero_10_task7_D20_seed143_init1.mp4` | - |
| `libero_10/task7/S06/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_7d375d639fb3795d780d08a75c7f70cb` | `videos/failure/pi0_libero_10_task7_S06_seed142_init0.mp4` | - |
| `libero_10/task7/S06/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_8f0b735e2384977dc5de584fab3ee053` | `videos/failure/pi0_libero_10_task7_S06_seed143_init1.mp4` | - |
| `libero_10/task7/S10/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_5602da7cc7295bb6a6be93d48618f853` | `videos/success/pi0_libero_10_task7_S10_seed142_init0.mp4` | - |
| `libero_10/task7/S10/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_86aa0541b4224e256ff8894194bcfa35` | `videos/success/pi0_libero_10_task7_S10_seed143_init1.mp4` | - |
| `libero_10/task7/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_34eb4bba3fa89e3b3114dc98aaffe962` | `videos/failure/pi0_libero_10_task7_S11_seed142_init0.mp4` | - |
| `libero_10/task7/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_b0120a0b76b9085f57b0089e80240e22` | `videos/failure/pi0_libero_10_task7_S11_seed143_init1.mp4` | - |
| `libero_10/task7/S17/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_c7fc6e09f2d546cd7409a19d9a763bbc` | `videos/failure/pi0_libero_10_task7_S17_seed142_init0.mp4` | - |
| `libero_10/task7/S17/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_9c8c5a1a3f94a578e97196418e6e96b7` | `videos/failure/pi0_libero_10_task7_S17_seed143_init1.mp4` | - |
| `libero_10/task8/D02/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_766ac7236ca686e2ecde35f2451cfb7c` | `videos/failure/pi0_libero_10_task8_D02_seed142_init0.mp4` | - |
| `libero_10/task8/D02/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_1e81f4a4e269438b25aa67a899b5ea9b` | `videos/failure/pi0_libero_10_task8_D02_seed143_init1.mp4` | - |
| `libero_10/task8/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_caf1f5c45d7d18097f72014f43cff1a6` | `videos/failure/pi0_libero_10_task8_D03_seed142_init0.mp4` | - |
| `libero_10/task8/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_f3dab091093fd5716e73b0edae12eef4` | `videos/failure/pi0_libero_10_task8_D03_seed143_init1.mp4` | - |
| `libero_10/task8/D06/seed142/init0` | `SUCCESS` | `TRIGGERED` | `PENDING` | `ep_0cc420c7d9467c6dc2550e1e32c8fd9a` | `videos/success/pi0_libero_10_task8_D06_seed142_init0.mp4` | 两个变量 添加了干扰物又进行局部移动 |
| `libero_10/task8/D06/seed143/init1` | `FAILURE` | `TRIGGERED` | `PENDING` | `ep_b225928b481d039a07184873a25b9499` | `videos/failure/pi0_libero_10_task8_D06_seed143_init1.mp4` | 两个变量 添加了干扰物又进行局部移动 |
| `libero_10/task8/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_34b95c3a6a67fc6d423caabd14d53f16` | `videos/failure/pi0_libero_10_task8_D20_seed142_init0.mp4` | - |
| `libero_10/task8/D20/seed143/init1` | `SUCCESS` | `TRIGGERED` | `PASS` | `ep_6a91e513d118bea8be4251264bef8c7b` | `videos/success/pi0_libero_10_task8_D20_seed143_init1.mp4` | - |
| `libero_10/task8/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_666e421d8d95578e897bcbfc3e7b8082` | `videos/failure/pi0_libero_10_task8_S10_seed142_init0.mp4` | - |
| `libero_10/task8/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_2536288738fc8ff6ebed1886c64bcf97` | `videos/failure/pi0_libero_10_task8_S10_seed143_init1.mp4` | - |
| `libero_10/task8/S11/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_98caa2919f557fe6e461fe7da1669d75` | `videos/success/pi0_libero_10_task8_S11_seed142_init0.mp4` | - |
| `libero_10/task8/S11/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_1c4dd852761b945641bea2715ca6afeb` | `videos/failure/pi0_libero_10_task8_S11_seed143_init1.mp4` | - |
| `libero_10/task8/S13/seed142/init0` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_46d445fd1f5ec1f6e75fc14e50e4397c` | `videos/success/pi0_libero_10_task8_S13_seed142_init0.mp4` | - |
| `libero_10/task8/S13/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_13af4ef0f5d88199c0e85ad11a3cd40c` | `videos/failure/pi0_libero_10_task8_S13_seed143_init1.mp4` | - |
| `libero_10/task9/D01/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_ef1be1d5c16ef367d8756b37ec8dfd91` | `videos/failure/pi0_libero_10_task9_D01_seed142_init0.mp4` | - |
| `libero_10/task9/D01/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_0a17c012830cd508739f5a7cdc5d715e` | `videos/failure/pi0_libero_10_task9_D01_seed143_init1.mp4` | - |
| `libero_10/task9/D03/seed142/init0` | `FAILURE` | `TRIGGERED` | `ISSUE` | `ep_d5f67bd26784391bd3f656c3e4286f11` | `videos/failure/pi0_libero_10_task9_D03_seed142_init0.mp4` | 不能用base物体，也没放在接收区域 |
| `libero_10/task9/D03/seed143/init1` | `FAILURE` | `TRIGGERED` | `ISSUE` | `ep_8df9c8811686a4c5cd62f8283dc76142` | `videos/failure/pi0_libero_10_task9_D03_seed143_init1.mp4` | 不能用base物体，也没放在接收区域 |
| `libero_10/task9/D05/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_e39a1b3a06103d60a6e88a06779cd03b` | `videos/failure/pi0_libero_10_task9_D05_seed142_init0.mp4` | - |
| `libero_10/task9/D05/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_5550c578265f42a694053985f0c65fa3` | `videos/failure/pi0_libero_10_task9_D05_seed143_init1.mp4` | - |
| `libero_10/task9/D20/seed142/init0` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_c633d5ce0c863364c31d238d68a29c8a` | `videos/failure/pi0_libero_10_task9_D20_seed142_init0.mp4` | - |
| `libero_10/task9/D20/seed143/init1` | `FAILURE` | `TRIGGERED` | `PASS` | `ep_2c34bf64f047ed61b32e6f552973f051` | `videos/failure/pi0_libero_10_task9_D20_seed143_init1.mp4` | - |
| `libero_10/task9/S03/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_6c2c468cd99222c5f80658a1b5cd1d66` | `videos/failure/pi0_libero_10_task9_S03_seed142_init0.mp4` | - |
| `libero_10/task9/S03/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_2679495d867e082a0406b79c70aa49a8` | `videos/failure/pi0_libero_10_task9_S03_seed143_init1.mp4` | - |
| `libero_10/task9/S04/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_f0e0bdd94d76e616579b40aa8e3b16ea` | `videos/failure/pi0_libero_10_task9_S04_seed142_init0.mp4` | - |
| `libero_10/task9/S04/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_75d4e63abbb95ed413e69d3f540b84b6` | `videos/failure/pi0_libero_10_task9_S04_seed143_init1.mp4` | - |
| `libero_10/task9/S09/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `ISSUE` | `ep_b670caa8d1f27aa648e40e6b62937eab` | `videos/failure/pi0_libero_10_task9_S09_seed142_init0.mp4` | a扰动没有生效 |
| `libero_10/task9/S09/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `ISSUE` | `ep_a4f379c65b29608d5ec829458ec204eb` | `videos/success/pi0_libero_10_task9_S09_seed143_init1.mp4` | 扰动没有生效 |
| `libero_10/task9/S10/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_564fcdb634a7d09d6115eb377be90398` | `videos/failure/pi0_libero_10_task9_S10_seed142_init0.mp4` | - |
| `libero_10/task9/S10/seed143/init1` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_6186d5fdcd909f486743a707e30fdf4f` | `videos/failure/pi0_libero_10_task9_S10_seed143_init1.mp4` | - |
| `libero_10/task9/S11/seed142/init0` | `FAILURE` | `NOT_APPLICABLE` | `PASS` | `ep_e138023137119d04b000e72e26a97913` | `videos/failure/pi0_libero_10_task9_S11_seed142_init0.mp4` | - |
| `libero_10/task9/S11/seed143/init1` | `SUCCESS` | `NOT_APPLICABLE` | `PASS` | `ep_40cc2de5d1e592af36c8b50d3fd9d4d8` | `videos/success/pi0_libero_10_task9_S11_seed143_init1.mp4` | - |

### 下一轮必须重新 rollout

下列组在 R004 中至少有一次 `ISSUE` 或 `PENDING`。下一轮应整组重跑两次尝试，不能只补其中一条；动态扰动需保证事件实际触发并提供可观察证据。

| 优先级 | Task | Case | 本轮结论 | 需要修复或验证的问题 | 下一轮目标 |
|---|---:|---|---|---|---|
| `P1` | 5 | `D03` | 存疑/存疑 | 占用物体不在正确接受区域 出现一下就没了 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 6 | `D03` | 存疑/存疑 | 占用物品未消失 而且这个和base有区别 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 6 | `S12` | 错误/错误 | 穿模 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 7 | `D03` | 错误/错误 | 这个我记得base是有红色罐子的？怎么现在红色罐子变成临时占用物体了，同时占用后不会消失 | 修复后 R005，两次 rollout 均需 PASS |
| `P1` | 8 | `D06` | 存疑/存疑 | 两个变量 添加了干扰物又进行局部移动 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 9 | `D03` | 错误/错误 | 不能用base物体，也没放在接收区域 | 修复后 R005，两次 rollout 均需 PASS |
| `P0` | 9 | `S09` | 错误/错误 | a扰动没有生效；扰动没有生效 | 修复后 R005，两次 rollout 均需 PASS |

#### R005 精确 key 清单

- `libero_10/task5/D03/seed142/init0`；`libero_10/task5/D03/seed143/init1`。
- `libero_10/task6/D03/seed142/init0`；`libero_10/task6/D03/seed143/init1`。
- `libero_10/task6/S12/seed142/init0`；`libero_10/task6/S12/seed143/init1`。
- `libero_10/task7/D03/seed142/init0`；`libero_10/task7/D03/seed143/init1`。
- `libero_10/task8/D06/seed142/init0`；`libero_10/task8/D06/seed143/init1`。
- `libero_10/task9/D03/seed142/init0`；`libero_10/task9/D03/seed143/init1`。
- `libero_10/task9/S09/seed142/init0`；`libero_10/task9/S09/seed143/init1`。

### 本轮问题归纳

- `D03`：task5、task6、task7、task9 的临时占用对象在位置、来源或消失时机上仍不一致。
- `S12`：task6 两次 rollout 均出现遮挡物穿模。
- `D06`：task8 同时新增干扰物和移动干扰物，扰动变量不单一。
- `S09`：task9 两次 rollout 均未观察到间隙变化扰动生效。

---

## R005 定向复审记录

> 负责人：Junhao Wu<br>
> 审核日期：2026-09-06<br>
> 数据批次：`0906rollout` / `pi0-review-final-20260905-e9c8d10`<br>
> rollout commit：`e9c8d10677e102f6ec12fb7257d4a6e29225e2f6`

### 范围与证据

本轮覆盖 `libero_10/task5-task9` 中源批次实际提供的 39 个 task/case 组、78 个独立 rollout，每组包含 seed142/init0 与 seed143/init1 两次尝试。未出现在本批次中的稳定项不视为漏审。

- 结果文件 SHA-256：`eb34d9e8fdd69387e920f0f6350e4485e9868fece7dcc567780b23cab5daaa2d`
- 原始结果：`human_review_results.csv`（第六版人工审核交付）
- 视频与 episode 对应：同批次 `review_manifest.csv`

### 审核结果汇总

| 结论 | 数量 | 占比 |
|---|---:|---:|
| 认可 | 76 | 97.4% |
| 错误 | 0 | 0.0% |
| 存疑 | 2 | 2.6% |
| 异常 | 0 | 0.0% |
| 合计 | 78 | 100.0% |

| Task | 组数 | PASS | ISSUE | PENDING | 本轮状态 |
|---:|---:|---:|---:|---:|---|
| 5 | 7 | 14 | 0 | 0 | 全部通过 |
| 6 | 8 | 16 | 0 | 0 | 全部通过 |
| 7 | 8 | 16 | 0 | 0 | 全部通过 |
| 8 | 7 | 12 | 0 | 2 | D06 舍弃，其余通过 |
| 9 | 9 | 18 | 0 | 0 | 全部通过 |

### 唯一非认可项与处置

| Task | Case | 尝试 | 策略结果 | 审核判定 | Episode ID | 备注 | 后续处置 |
|---:|---|---:|---|---|---|---|---|
| 8 | `D06` | 1 | `FAILURE` | `PENDING` | `ep_c3c5aadac9f9d88e5ebb59baa7fba241` | 不算干扰物 | 舍弃，不再 rollout |
| 8 | `D06` | 2 | `FAILURE` | `PENDING` | `ep_c17f23d6e9193814799218d0cb0255e3` | 不算干扰物 | 舍弃，不再 rollout |

### R004 问题项关闭情况

| Task/Case | R005 结论 | 后续 |
|---|---|---|
| `task5/D03` | 两次均通过 | 关闭 |
| `task6/D03` | 两次均通过 | 关闭 |
| `task6/S12` | 两次均通过 | 关闭 |
| `task7/D03` | 两次均通过 | 关闭 |
| `task8/D06` | 两次均存疑：不算干扰物 | 舍弃，不再 rollout |
| `task9/D03` | 两次均通过 | 关闭 |
| `task9/S09` | 两次均通过 | 关闭 |

### 后续 rollout

`task5-task9` 本轮除已明确舍弃的 `task8/D06` 外全部通过，因此不再生成 R006 重跑清单。
