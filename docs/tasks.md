# 朗言 AI — 任务列表（tasks.md）

> 共 11 个任务，每个任务可在一次专注会话（1–3 小时）内完成。
> 按依赖顺序排列，Task 10 和 Task 11 必须最后执行。

---

## Task 01｜项目初始化与目录骨架

**影响文件**
- `main.py`（空壳 FastAPI app）
- `requirements.txt`
- `static/index.html`（空壳页面）
- `scenarios/interview.yaml`（四阶段配置占位）
- `scenarios/restaurant.yaml`、`scenarios/meeting.yaml`（TODO 占位文件）

**内容**
建立完整目录结构；安装 fastapi、uvicorn、websockets、anthropic、python-dotenv；
`main.py` 启动后在 `http://localhost:8000` 返回 `index.html`；
`interview.yaml` 包含四个阶段键：`intro`、`job_qa`、`behavioral`、`candidate_qa`，每个阶段含 `max_turns` 字段（暂时填占位值）。

**依赖任务**：无

**参考**
- FastAPI 快速上手：https://fastapi.tiangolo.com/tutorial/first-steps/
- 参考项目结构：[RealtimeVoiceChat](https://github.com/KoljaB/RealtimeVoiceChat)

---

## Task 02｜讯飞 STT 接入

**影响文件**
- `stt/xunfei_stt.py`
- `tests/fixtures/hello_en.wav`（放一段 3 秒标准英文录音用于测试）

**内容**
封装讯飞实时语音转写 WebSocket API，对外暴露：
```python
async def transcribe(audio_bytes: bytes) -> str
```
函数接收 PCM 音频字节，返回识别结果文字。
包含鉴权逻辑（APPID/APIKey/APISecret 从环境变量读取）、帧格式组装、结果解析。
单独运行 `python stt/xunfei_stt.py` 对 `tests/fixtures/hello_en.wav` 识别并打印结果。

**依赖任务**：01

**参考**
- 讯飞实时语音转写 WebSocket API 文档：https://www.xfyun.cn/doc/asr/rtasr/API.html
  - 重点：鉴权参数生成（hmac-sha256 签名）、音频帧格式（PCM 16kHz mono）、结果 JSON 结构中的 `ws[].cw[].w` 字段

---

## Task 03｜讯飞 TTS 接入

**影响文件**
- `tts/xunfei_tts.py`

**内容**
封装讯飞在线语音合成 WebSocket API，对外暴露：
```python
async def synthesize(text: str) -> bytes
```
函数接收英文文本，返回可播放的 MP3 音频字节。
发音人选英文音色（如 `x4_EnUs_laura`）。
单独运行 `python tts/xunfei_tts.py` 合成一段英文并保存为 `tests/fixtures/tts_test.mp3`。

**依赖任务**：01

**参考**
- 讯飞在线语音合成 API 文档：https://www.xfyun.cn/doc/tts/online_tts/API.html
  - 重点：status 字段（0/1/2 分片）、audio base64 解码拼接、英文发音人参数 `vcn`

---

## Task 04｜LLM 对话核心 + 面试阶段状态机

**影响文件**
- `llm/conversation.py`（多轮对话历史管理、LLM 流式调用）
- `llm/stage_manager.py`（四阶段状态机）
- `scenarios/interview.yaml`（补全每阶段 system prompt 模板）

**内容**
`StageManager` 类维护当前阶段和轮次计数，`advance()` 方法返回是否切换阶段及新阶段名称。
`ConversationManager` 类维护对话历史（最近 10 轮），提供 `async def chat(user_text, stage) -> AsyncGenerator[str]` 流式返回 LLM token。
LLM 调用使用 Anthropic Claude API（claude-sonnet-4-6），streaming=True。
`interview.yaml` 中每个阶段补充一段 system prompt 描述 AI 扮演的角色和本阶段目标。

**依赖任务**：01

**参考**
- Anthropic Streaming API 文档（context7 可查）
- 参考 `scenarios/interview.yaml` 结构：

```yaml
stages:
  intro:
    max_turns: 2
    prompt_hint: "You are a friendly HR interviewer. Ask the candidate to introduce themselves."
  job_qa:
    max_turns: 3
    prompt_hint: "..."
```

---

## Task 05｜LLM 纠错模块

**影响文件**
- `llm/corrector.py`

**内容**
封装纠错逻辑，对外暴露：
```python
async def correct(user_text: str, context: list[str]) -> dict | None
```
返回 `None` 表示本轮无需纠错。
返回 dict 包含三个字段：`original`（原始表达）、`suggestion`（建议替换）、`explanation`（一句话说明，英文）。
使用单独的 LLM 调用（非流式），prompt 要求模型只在有明显语法或表达问题时才返回建议，否则返回 `null`。

**依赖任务**：04

---

## Task 06｜Web 界面基础（静态）

**影响文件**
- `static/index.html`
- `static/style.css`
- `static/app.js`（仅 UI 骨架，WebSocket 逻辑在 Task 07 补充）

**内容**
页面布局：
- 顶部：阶段进度条（4 个节点，当前阶段高亮）
- 中部：对话气泡区（用户气泡左对齐，AI 气泡右对齐），字幕滚动
- 底部：麦克风按钮（按住说话）+ 打断按钮
- 弹窗：纠错弹窗组件（默认隐藏，`display:none`），含原始表达/建议/说明三行 + 关闭按钮
- 底部角落：「结束会话」按钮

纯原生 HTML/CSS/JS，无框架依赖。
参考 [RealtimeVoiceChat](https://github.com/KoljaB/RealtimeVoiceChat) 的前端交互模式。

**依赖任务**：01

---

## Task 07｜WebSocket 实时音频流水线（核心集成）

**影响文件**
- `main.py`（添加 WebSocket endpoint `/ws`）
- `static/app.js`（补充 MediaRecorder 录音、WebSocket 收发逻辑）

**内容**

后端 `/ws` endpoint 处理流程：
1. 接收前端二进制音频帧（PCM）
2. 收到 `audio_end` 信号后调用 STT 得到文字
3. 调用 StageManager 检查是否推进阶段，构建 context
4. 流式调用 LLM，将 token 实时发回前端
5. 句子边界时调用 TTS，将音频分块发回前端
6. LLM 回复完成后，异步调用 corrector，将结果以 JSON 消息发回前端
7. 前端收到纠错消息后显示弹窗

前端音频采集：MediaRecorder API，采样率 16kHz，格式 PCM，100ms 一帧推送。

WebSocket 消息类型枚举（约定为 JSON envelope）：
- 前端→后端：`{type: "audio_chunk", data: <binary>}`、`{type: "audio_end"}`、`{type: "interrupt"}`
- 后端→前端：`{type: "stt_result", text: "..."}`、`{type: "llm_token", token: "..."}`、`{type: "tts_chunk", audio: <binary>}`、`{type: "correction", ...}`、`{type: "stage_change", stage: "..."}`、`{type: "session_end", report_path: "..."}`

**依赖任务**：02, 03, 04, 05, 06

**参考**
- FastAPI WebSocket 文档：https://fastapi.tiangolo.com/advanced/websockets/
- MediaRecorder API：https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder

---

## Task 08｜表达评分模块

**影响文件**
- `llm/scorer.py`

**内容**
封装会话结束时的整体打分逻辑，对外暴露：
```python
async def score_session(turns: list[str]) -> dict
```
`turns` 为本次会话所有用户发言的文字列表。
返回 dict：`{"accuracy_score": int, "fluency_score": int, "vocabulary_score": int}`，三值均为 0–100 整数。
使用单次 LLM 调用（非流式），prompt 要求模型对整体表现评分并以 JSON 返回。

**依赖任务**：04

---

## Task 09｜课后报告 HTML 生成

**影响文件**
- `reports/generator.py`
- `reports/template.html`

**内容**
`generate_report(session_data: dict) -> str` 函数接收会话数据，基于 `template.html` 用字符串替换生成 HTML，写入 `reports/session_{timestamp}.html`，返回文件路径。

`session_data` 包含：
- `turns`：对话记录列表（角色 + 文字）
- `scores`：三项评分
- `corrections`：纠错列表（每轮的 correction dict）
- `scene`、`duration_seconds`

报告 HTML 展示：会话基本信息、三项评分（可用进度条样式）、对话记录全文、纠错汇总表。
所有样式内联，无外部 CSS 依赖，确保离线打开正常渲染。

**依赖任务**：05, 08

---

## Task 10｜接入主流程（端到端串联）

**影响文件**
- `main.py`（完善 WebSocket handler，接入 scorer 和 report generator）

**内容**
在 Task 07 的 WebSocket 流水线基础上，补充会话收尾逻辑：
- 反问阶段完成后（或用户点击"结束会话"），StageManager 返回 `session_end` 信号
- 触发 `score_session(all_user_turns)`
- 触发 `generate_report(session_data)`
- 向前端发送 `{type: "session_end", report_path: "reports/session_xxx.html"}`
- 前端展示"查看报告"按钮，点击用 `window.open(report_path)` 打开

完整数据流从用户开口到报告生成全部打通。

**依赖任务**：07, 08, 09

---

## Task 11｜端到端验证

**影响文件**
- `tests/e2e_test.md`（手动测试用例文档）
- `tests/latency_bench.py`（延迟测量脚本）

**内容**
手动执行一次完整面试会话：
1. `python main.py` 启动服务
2. 浏览器打开 `http://localhost:8000`，选择面试场景
3. 依次经历全部 4 个阶段，进行 ≥ 5 轮对话
4. 结束会话，在 `reports/` 目录确认报告生成
5. 打开报告 HTML，检查内容完整性

`latency_bench.py` 模拟发送预录音频，测量从发送 `audio_end` 到收到第一个 `tts_chunk` 的时间，运行 10 次取 P50/P95。

**依赖任务**：10
