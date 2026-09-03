# Libero 10, Task 5~9 — R005 定向复审记录

> 负责人：Junhao Wu<br>
> 审核日期：2026-09-03<br>
> 数据批次：`0902rollout` / `pi0-review-final-20260902-51bb70b`<br>
> rollout commit：`51bb70b8f32dde58b61f53b4afe65bd18985f348`

## 范围与证据

本轮是问题项定向复审，不是全量审核。覆盖 `libero_10/task5-task9` 共 39 个 task/case 组、78 个独立 rollout；每组包含 seed142/init0 与 seed143/init1 两次尝试。未出现在本批次中的稳定项不视为漏审，也不新增审核结论。

- 结果文件 SHA-256：`6d542ad2560b018bb09e266fad241789857d8036e5704eafc522598dd22f0025`
- 原始结果：`human_review_results.csv`（第五版人工审核交付）
- 视频与 episode 对应：同批次 `review_manifest.csv`

## 审核结果汇总

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

## R005 逐 rollout 记录

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

## 下一轮必须重新 rollout

下列组在 R005 中至少有一次 `ISSUE` 或 `PENDING`。下一轮应整组重跑两次尝试，不能只补其中一条；动态扰动需保证事件实际触发并提供可观察证据。

| 优先级 | Task | Case | 本轮结论 | 需要修复或验证的问题 | 下一轮目标 |
|---|---:|---|---|---|---|
| `P1` | 5 | `D03` | 存疑/存疑 | 占用物体不在正确接受区域 出现一下就没了 | 修复后 R006，两次 rollout 均需 PASS |
| `P1` | 6 | `D03` | 存疑/存疑 | 占用物品未消失 而且这个和base有区别 | 修复后 R006，两次 rollout 均需 PASS |
| `P0` | 6 | `S12` | 错误/错误 | 穿模 | 修复后 R006，两次 rollout 均需 PASS |
| `P0` | 7 | `D03` | 错误/错误 | 这个我记得base是有红色罐子的？怎么现在红色罐子变成临时占用物体了，同时占用后不会消失 | 修复后 R006，两次 rollout 均需 PASS |
| `P1` | 8 | `D06` | 存疑/存疑 | 两个变量 添加了干扰物又进行局部移动 | 修复后 R006，两次 rollout 均需 PASS |
| `P0` | 9 | `D03` | 错误/错误 | 不能用base物体，也没放在接收区域 | 修复后 R006，两次 rollout 均需 PASS |
| `P0` | 9 | `S09` | 错误/错误 | a扰动没有生效；扰动没有生效 | 修复后 R006，两次 rollout 均需 PASS |

### R006 精确 key 清单

- `libero_10/task5/D03/seed142/init0`；`libero_10/task5/D03/seed143/init1`。
- `libero_10/task6/D03/seed142/init0`；`libero_10/task6/D03/seed143/init1`。
- `libero_10/task6/S12/seed142/init0`；`libero_10/task6/S12/seed143/init1`。
- `libero_10/task7/D03/seed142/init0`；`libero_10/task7/D03/seed143/init1`。
- `libero_10/task8/D06/seed142/init0`；`libero_10/task8/D06/seed143/init1`。
- `libero_10/task9/D03/seed142/init0`；`libero_10/task9/D03/seed143/init1`。
- `libero_10/task9/S09/seed142/init0`；`libero_10/task9/S09/seed143/init1`。

## 本轮问题归纳

- `D03`：task5、task6、task7、task9 的临时占用对象在位置、来源或消失时机上仍不一致。
- `S12`：task6 两次 rollout 均出现遮挡物穿模。
- `D06`：task8 同时新增干扰物和移动干扰物，扰动变量不单一。
- `S09`：task9 两次 rollout 均未观察到间隙变化扰动生效。
