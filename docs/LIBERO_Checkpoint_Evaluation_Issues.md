# LIBERO Checkpoint 评测适配问题简述

## 问题现象

xVLA 官方 LIBERO checkpoint 标称成功率较高，但平台早期测试连续出现 `reward=0`、运行到步数上限仍不成功。问题主要来自评测接口没有完整复现 checkpoint 训练和官方评测时的输入、坐标系及 reset 约定，而不是模型本身失效。

## 已确认的主要原因

最关键的问题是末端姿态坐标系不一致：

- xVLA 需要 LIBERO controller 的 `ee_ori_mat`，并将其编码为 rotation-6D。
- 远程 observation 提供的 `robot0_eef_quat` 属于末端 site frame。
- 早期 runner 直接将该四元数转换成旋转矩阵，和 controller frame 的最大数值差达到 `1.0008`。
- 对绝对位姿控制而言，错误姿态会导致模型基于错误的机械臂朝向生成抓取动作。

修复方式是在 xVLA 客户端映射层加入固定的 site-to-controller 坐标变换 `[-Y, X, Z]`，不修改远程 observation 协议。

同时修复了以下叠加问题：

- 使用 xVLA 官方 LIBERO processor，生成 20D position + rotation-6D proprio。
- 只翻转主相机，不错误翻转 wrist 相机。
- 补齐 ImageNet 图像归一化和 LIBERO domain id 3。
- 避免 empty camera 被重复计数，保持 checkpoint 声明的 3 个图像视图。
- reset 后执行官方要求的 10 个 no-op 稳定步。
- 元数据请求使用统一超时，避免 LIBERO 冷启动时测试提前中断。

## 修复证据

固定使用 `libero_spatial/task_id=8`、`init_state_id=0`、`seed=142`：

- controller-frame 修复前：500 步结束，`success=false`、`reward=0`。
- controller-frame 修复后：第 100 步成功，`success=true`、`reward=1.0`。

这说明此前观察到的低成功率主要是平台适配造成的假低成功率。

## 更换 LIBERO Checkpoint 后是否会再次出现

如果新 checkpoint 与当前 xVLA checkpoint 使用完全相同的模型架构、processor、相机配置、20D proprio、EEF6D 绝对动作和 gripper 语义，上述已修复问题通常不会再次出现，可以复用当前 xVLA runner。

如果只是同样在 LIBERO 上训练，但来自 OpenVLA、Pi0、其他 xVLA 版本或自定义训练流程，问题仍可能重新暴露。`LIBERO checkpoint` 只说明任务环境相同，不代表模型接口相同。接入前必须重新确认：

1. 相机数量、顺序、名称、分辨率、翻转和归一化方式。
2. proprio 字段、维度、坐标系及旋转表示。
3. action 是 absolute 还是 relative，是 EEF、关节还是其他控制格式。
4. gripper 的范围、阈值和开合正负语义。
5. tokenizer、domain id、processor 配置与 LeRobot 版本。
6. BDDL、init state、seed、reset 稳定步和官方 horizon。

因此，新 checkpoint 不应直接套用现有 runner。应先读取其配置和官方评测代码，建立模型适配器，再用固定任务做 observation、action 和 controller 轨迹对照，最后进行多任务、多 init state 的成功率统计。

> 注意：单次成功只能证明链路可用，不能代表 checkpoint 的整体成功率。官方 xVLA LIBERO 数据使用多任务、多 episode 和最长约 800 步的评测设置。
