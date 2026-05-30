# 🤖 OS Polygraph - Mac 观察日记系统

> 一个让你的 Mac 可以像个傲娇幽灵一样观察、吐槽、嘲讽你工作状态的监控与日记生成系统。
> 使用 **SiliconFlow DeepSeek-V4-Flash** 模型，实时生成带有黑色幽默的工作行为分析日记。

---

## ✨ 核心特性

- 🎯 **实时行为监控**：捕获窗口切换、文件保存、CPU 负载、系统闲置等多维度工作指标
- 🧠 **AI 驱动的吐槽**：基于真实行为数据，用 SiliconFlow API 生成独一无二、充满个性的观察日记
- 🛡️ **智能降级容灾**：API 超时或失败时自动启用本地 fallback，确保日记不间断生成
- ⚡ **异步非阻塞**：后台守护进程持续监控，定期异步触发日记生成，不占用你的 CPU
- 📊 **多层次分析**：从窗口活动、代码提交频率、CPU 峰值到系统闲置，一网打尽
- 🎨 **可自定义提示词**：随时修改生成逻辑，打造属于你的 AI 观察者

---

## 🚀 快速开始

### 1️⃣ 前置要求

- **macOS 10.15+** 及 **Python 3.8+**
- **OpenAI SDK**：`pip install openai`
- **SiliconFlow API Key**：从 [SiliconFlow 官网](https://siliconflow.cn/) 注册并获取

### 2️⃣ 配置环境

#### 创建 `.env` 文件（从模板复制）
```bash
cp .env.example .env
```

#### 编辑 `.env` 并填入 API Key
```bash
# 打开 .env 文件
nano .env

# 填入你的真实 API Key
SF_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **关键配置位置**：
> - **API Key 位置**：`.env` 文件第 1 行 `SF_API_KEY=<YOUR_KEY>`
> - **模型配置位置**：`config.py` 第 67 行 `SF_MODEL = "deepseek-ai/DeepSeek-V4-Flash"`
> - **API 端点位置**：`config.py` 第 66 行 `SF_BASE_URL = "https://api.siliconflow.cn/v1"`

### 3️⃣ 启动系统

```bash
# 启动后台守护进程
./start.sh start

# 验证运行状态
./start.sh status

# 手动触发日记生成（立即看到结果）
./start.sh trigger

# 查看实时日志
./start.sh log

# 停止守护进程
./start.sh stop
```

### 4️⃣ 查看生成的日记

```bash
# 打开日记文件（会自动滚动到最新条目）
open Mac_Observation_Diary.md

# 或在终端查看最新 10 条
head -n 50 Mac_Observation_Diary.md
```

---

## 📁 项目结构

```
.
├── daemon.py                    # 后台守护进程（实时监控 + 异步触发）
├── diary_generator.py           # 日记生成引擎（调用 API 或本地 fallback）
├── config.py                    # 中央配置管理 ⭐ API Key/模型位置
├── start.sh                     # 启动脚本与命令行控制台
├── .env.example                 # 环境变量模板（安全模式）
├── .env                         # 真实环境变量（被 .gitignore 保护）
├── .gitignore                   # Git 脱敏清单
├── Mac_Observation_Diary.md     # 自动生成的日记文件
└── README.md                    # 本文件
```

---

## ⚙️ 配置参数详解

### 📍 API & 模型配置（`config.py` 第 66-67 行）

```python
# 🔴 修改 API 端点：
SF_BASE_URL = "https://api.siliconflow.cn/v1"  # 改这里切换不同的 API 提供商

# 🔴 修改模型名称：
SF_MODEL = "deepseek-ai/DeepSeek-V4-Flash"  # 改这里尝试其他模型
```

### 📍 API Key 管理（`.env` 文件）

```bash
# 从 SiliconFlow 或其他提供商获取 Key，填在这里
SF_API_KEY=sk-your_api_key_here_xxxxxxxxxx
```

### 📍 监控参数（`config.py` 第 27-30 行）

```python
MONITOR_INTERVAL = 3.0       # 监控轮询间隔（秒）
FLUSH_INTERVAL = 120.0       # 日记自动生成间隔（秒）
IDLE_THRESHOLD = 300.0       # 系统闲置阈值（秒）
FOCUS_EGG_THRESHOLD = 3600.0 # 连续专注彩蛋触发时长（秒）
```

---

## 🔧 进阶用法

### 自定义提示词（Prompt）

编辑 `diary_generator.py` 的 `build_prompt()` 函数（第 143-160 行），修改 System Prompt 和评价逻辑，打造你专属的 AI 观察风格。

### 处理 API 超时

如果 SiliconFlow 响应缓慢：
- **自动重试**：已内置 3 次重试机制，timeout 设为 45 秒（在 `diary_generator.py` 第 85 行）
- **手动调整**：修改 `timeout_seconds = 45` 改为更大的值

### 本地 Fallback 方案

当 API 调用失败时，系统自动使用 `get_fallback_diary()` 函数生成本地吐槽。修改该函数（`diary_generator.py` 第 12-73 行）可自定义离线内容。

---

## 🛡️ 安全与隐私

- ✅ **API Key 脱敏**：`.env` 已被 `.gitignore` 保护，永远不会提交到 Git
- ✅ **日记本隐私**：`Mac_Observation_Diary.md` 本地生成，不上传任何云存储
- ✅ **敏感文件清单**：详见 `.gitignore`，包含日志、缓存、临时文件等

---

## 📊 监控指标说明

系统捕获以下维度的行为数据：

| 指标 | 含义 | 触发条件 |
|------|------|---------|
| `window_switches` | 窗口切换次数 | 检测到不同应用成为最前台 |
| `file_saves` | 代码/文件保存次数 | 工作区内文件修改时间变化 |
| `cpu_spikes` | CPU 峰值事件 | 系统总 CPU 占用 > 150% |
| `max_idle_seconds` | 最长系统闲置 | 无鼠标/键盘输入时长 |
| `consecutive_focus_seconds` | 连续专注时长 | Code 应用持续活跃的累计时间 |

---

## 🎯 日常运维清单

```bash
# 每天启动
./start.sh start

# 查看最新日记（随时了解 AI 的吐槽）
tail -n 20 Mac_Observation_Diary.md

# 监控后台日志
./start.sh log

# 手动触发（想立即看结果时）
./start.sh trigger

# 晚上关闭
./start.sh stop
```

---

## 🐛 故障排查

### 问题：API 超时或响应慢

**解决方案**：
1. 检查网络连接
2. 在 `diary_generator.py` 第 85 行增加 `timeout_seconds`
3. 查看 `daemon.log` 了解重试日志

### 问题：日记中全是 `(离线/限流保护模式)`

**解决方案**：
1. 验证 `.env` 中的 `SF_API_KEY` 是否正确
2. 确认 SiliconFlow 账户有足够额度
3. 运行 `./start.sh stop` 后手动执行 `python3 diary_generator.py .snapshot_stats.json` 查看详细错误

### 问题：后台守护进程崩溃

**解决方案**：
1. 查看 `daemon.log` 最后 50 行：`tail -n 50 daemon.log`
2. 确保 `config.py` 中的路径配置正确
3. 重启系统：`./start.sh stop && ./start.sh start`

---

## 📝 开发与贡献

### 本地测试

```bash
# 直接运行生成器（不启动后台）
python3 diary_generator.py .snapshot_stats.json

# 验证配置是否正确加载
python3 -c "import config; print(f'API Key: {config.SF_API_KEY[:10]}...')"
```

### 代码风格

- Python 3.8+ 兼容
- 遵循 PEP 8 规范
- 使用 UTF-8 编码
- 异常必须记录到 `daemon.log`

---

## 📜 License

MIT License - 自由使用、修改、分发本项目，但保留原作者署名。

---

## 💬 致开发者

这个项目的核心哲学是：**让你的电脑也能像个活生生的"幽灵"一样，用黑色幽默的方式观察你的工作状态**。

它不仅是一个监控工具，更是一个充满人文关怀的"吐槽伙伴"。每一条日记都是基于你真实的行为数据生成的，AI 的吐槽越扎心，说明你的工作方式越值得反思 🎭。

---

**🚀 现在就启动吧：`./start.sh start`**

**😏 然后等着被你的 Mac 幽灵噎住。**
