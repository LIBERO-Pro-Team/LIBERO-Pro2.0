# LIBERO-Pro 自定义 VLA Agent 接入方案

## 1. 方案结论

LIBERO-Pro 由平台声明固定的 Agent 接口。用户在本机为自己的 VLA 模型实现 adapter，使模型接收平台标准观测，并返回平台标准动作。

平台不推测未知模型的图像方向、状态表示、归一化方式或动作定义。相关转换由模型作者在 adapter 内完成。

因此，LIBERO-Pro 实际评测对象定义为：

```text
Agent = checkpoint + 推理代码 + tokenizer/processor + adapter + 配置
```

而不是一个无法独立运行的裸 checkpoint。

## 2. 总体结构

```text
LIBERO-Pro 服务器
  - BDDL 任务加载
  - MuJoCo 渲染与物理执行
  - 标准观测输出
  - 标准动作执行
          |
          | 标准 LIBERO-Pro 协议
          v
用户端 Agent adapter
  - 图像预处理
  - 状态和坐标系转换
  - tokenizer / processor
  - 私有模型推理
  - 动作反归一化和格式转换
          |
          v
用户本地 VLA checkpoint
```

模型和 adapter 均运行在用户电脑上。服务器只接收标准动作，不执行用户代码，也不需要获得未发布模型。

## 3. 责任划分

### LIBERO-Pro 平台负责

- 固定并发布标准观测和标准动作语义。
- 提供 BDDL、初始状态、语言任务、渲染结果和机器人状态。
- 执行动作并返回 reward、success、terminated 和 truncated。
- 管理 episode、session、超时和资源回收。
- 提供 adapter 模板、类型定义和 conformance test。
- 记录服务器、任务、BDDL、协议和运行结果版本。

### 用户 adapter 负责

- 加载用户 checkpoint、tokenizer 和 processor。
- 按模型需要选择和排列相机。
- 完成图像翻转、缩放、裁剪和归一化。
- 完成状态拼接、补零和坐标表示转换。
- 完成语言 prompt 和 tokenizer 处理。
- 管理模型内部 action chunk 和历史状态。
- 将模型输出转换成 LIBERO-Pro 标准动作。
- 在 episode reset 时清空模型队列和缓存。

## 4. 建议的最小 Agent 接口

```python
class LiberoProAgent:
    def describe(self) -> AgentCapabilities:
        """声明 Agent 支持的协议版本和环境能力。"""

    def reset(self, episode: EpisodeContext) -> None:
        """开始新 episode，并清空策略内部状态。"""

    def act(self, observation: CanonicalObservation) -> CanonicalAction:
        """接收一帧标准观测，返回一个标准环境动作。"""
```

接口保持三个方法。模型加载、预处理、action chunk、缓存和动作转换均隐藏在 adapter 实现内部。

## 5. 标准观测定义

`CanonicalObservation` 至少包含：

| 字段 | 标准语义 |
|---|---|
| `step_index` | 当前 episode 的环境步编号 |
| `instruction` | BDDL 任务对应的原始自然语言指令 |
| `images.agent` | RGB、uint8、HWC、未经模型专用翻转的主相机图像 |
| `images.wrist` | RGB、uint8、HWC、未经模型专用翻转的腕部图像 |
| `eef.position` | 世界坐标系中的末端位置，单位为米 |
| `eef.rotation_matrix` | 明确定义为 LIBERO controller frame 的 3x3 旋转矩阵 |
| `gripper.qpos` | 明确关节顺序和单位的夹爪状态 |
| `timestamp` | 该观测对应的环境时间或单调时间戳 |

协议文档必须同时规定：

- 图像通道、维度顺序和像素范围；
- 相机名称、方向和分辨率；
- 坐标系、单位和旋转约定；
- 缺失可选字段时的行为；
- 序列化格式和协议版本。

## 6. 标准动作定义

V1 建议只接受单步、7 维、绝对控制动作：

```text
[x, y, z, rx, ry, rz, gripper]
```

其中：

- `x, y, z`：绝对末端目标位置，单位为米；
- `rx, ry, rz`：controller frame 下的 axis-angle，单位为弧度；
- `gripper`：只能为 `-1` 或 `1`，并明确开合含义；
- 所有值必须为有限的 `float32`；
- 平台执行前检查维度、数值范围和控制模式。

一次输出多个动作的模型，应由 adapter 在内部保存 action chunk，每次 `act()` 只返回一个标准动作。平台不需要感知模型的 action horizon。

## 7. 能力协商

`describe()` 返回 `AgentCapabilities`，至少声明：

```text
agent_name
agent_version
protocol_version
required_cameras
required_observation_fields
maximum_inference_seconds
```

正式创建 episode 前，平台比较 Agent 需求与服务器能力。缺少必要相机、状态或协议版本时，应立即拒绝测试，不能静默补零或猜测默认值。

## 8. 测试前一致性校验

平台提供独立的 `validate-agent` 流程：

1. 检查 `describe()` 是否满足协议版本。
2. 向 adapter 提供固定的标准观测样本。
3. 检查动作 shape、dtype、NaN、Inf 和数值范围。
4. 检查每次 `reset()` 后 action queue 是否清空。
5. 展示或保存 adapter 实际输入模型的相机图像，供用户确认方向和顺序。
6. 对坐标系、quaternion 和 rotation matrix 提供数值测试样本。
7. 执行短 episode dry-run，检查推理超时、网络异常和 session 回收。

校验结果必须区分：

```text
protocol_valid = true/false
episode_status = completed/error/timeout
task_success = true/false
```

`protocol_valid=true` 只能证明接口格式合规，不能自动证明用户的模型预处理语义正确。

## 9. 主要隐藏问题及处理方式

### 9.1 格式正确但语义错误

相同 shape 可能分别表示 RGB/BGR、absolute/relative、`xyzw`/`wxyz` 或不同坐标系。

处理方式：接口文档必须定义完整语义；提供黄金样本、图像预览和坐标数值测试，禁止隐式默认值。

### 9.2 未知模型需要额外观测

模型可能需要深度图、第三相机、关节速度、历史帧或不同分辨率。

处理方式：采用“稳定核心字段 + 可选 capability + 协议版本”。平台不支持的必要能力在测试前明确拒绝。

### 9.3 模型状态跨 episode 泄漏

action chunk、RNN 状态或历史帧可能从上一个任务进入下一个任务。

处理方式：每个 episode 强制调用 `reset()`，并提供重复 reset 的回归测试。

### 9.4 网络和推理延迟

本机模型与服务器环境逐步通信，超时可能造成 episode 中断或 session 泄漏。

处理方式：规定单步 deadline、超时结果、重试策略和 session 回收规则；分别记录推理时间、网络时间和总时长。

### 9.5 结果不可复现

私有 adapter、processor 或本地依赖变化后，相同 checkpoint 可能产生不同结果。

处理方式：报告中记录 checkpoint、adapter、配置、依赖和协议版本的哈希；正式公开评测可要求提交可复现容器。

### 9.6 adapter 错误与模型能力难以区分

低成功率可能来自模型，也可能来自图像、坐标系或动作转换错误。

处理方式：日志分别记录标准观测元数据、标准动作、adapter 版本、错误阶段和 conformance 结果；先通过接口校验，再进行成功率评测。

### 9.7 公开排行榜的公平性

用户 adapter 可能根据 `task_id`、初始状态或外部信息写死行为。

处理方式：服务器只发送允许使用的标准观测，不暴露仿真内部隐藏状态；公开评测需要定义允许的数据来源、记录提交物哈希，并根据可信等级区分本地自测与官方结果。

### 9.8 固定接口的演进

直接修改字段含义会让旧 adapter 产生无提示错误。

处理方式：协议采用明确版本，例如 `libero_pro_agent_v1`；新增可选字段保持向后兼容，语义变化必须升级主版本。

## 10. 评测记录要求

每次运行至少记录：

- Agent 名称、版本和 adapter 哈希；
- checkpoint 和 tokenizer/processor 哈希；
- LIBERO-Pro 协议版本；
- 服务器代码、LIBERO、MuJoCo 和 BDDL 版本；
- suite、task、init state、seed 和 max steps；
- 图像尺寸、控制模式和 timeout；
- conformance test 结果；
- success、reward、steps、terminated 和 truncated；
- 推理、网络和 episode 总耗时；
- 错误发生的阶段和结构化异常信息。

## 11. 平台实现顺序

1. 固定 `CanonicalObservation` 和 `CanonicalAction` V1 语义。
2. 定义 `LiberoProAgent`、`AgentCapabilities` 和 `EpisodeContext`。
3. 将现有 xVLA runner 改造成第一个参考 adapter。
4. 实现 `validate-agent` 和固定黄金样本。
5. 在正式 runner 中加入能力协商、超时和结构化错误分类。
6. 将 adapter、checkpoint 和协议哈希写入现有 JSONL 报告。
7. 再使用第二种模型验证这个 seam，确认不是只为 xVLA 设计。

## 12. 最终原则

- 服务器对标准环境观测、标准动作和物理执行负责。
- 用户对私有模型 adapter 的模型语义负责。
- 平台通过 conformance test 排除可检测的接口错误。
- 平台不自动猜测未知模型的训练和预处理约定。
- 所有成绩代表完整 Agent 的表现，而不是孤立 checkpoint 的表现。
