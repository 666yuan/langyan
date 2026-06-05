# 朗言 AI — 验收清单（checklist.md）

> 每一项必须可观测、可勾选。含具体数值、文件名、错误文案。
> 最终验收须通过「端到端验收」一节的全部条目。

---

## 环境启动

- [ ] `pip install -r requirements.txt` 无报错，安装完成后 `python -c "import fastapi, anthropic"` 不抛 ImportError
- [ ] `python main.py` 启动，终端输出包含 `Uvicorn running on http://0.0.0.0:8000`，3 秒内完成启动
- [ ] 浏览器打开 `http://localhost:8000`，页面标题为 **"朗言 AI"**，可见麦克风按钮和阶段进度条，无 JS 报错（DevTools Console 无红色错误）
- [ ] `scenarios/` 目录下存在以下三个文件：`interview.yaml`、`restaurant.yaml`、`meeting.yaml`
- [ ] `scenarios/interview.yaml` 包含四个阶段键：`intro`、`job_qa`、`behavioral`、`candidate_qa`，每个键下有 `max_turns` 字段

---

## STT 模块（`stt/xunfei_stt.py`）

- [ ] 独立运行 `python stt/xunfei_stt.py`，输入 `tests/fixtures/hello_en.wav`，终端打印非空英文字符串（如 `"Hello, my name is..."`)，不抛异常
- [ ] 输入中英混合音频（如"I want to apply for this position 这个职位"），函数返回含英文部分的字符串，不报错
- [ ] 讯飞 WebSocket 连接失败（如 APPID 错误）时，程序打印 `[STT ERROR] 无法连接讯飞语音服务，请检查 APPID/APIKey`，不打印 Python 堆栈 traceback
- [ ] `.env` 文件缺失时，程序打印 `[CONFIG ERROR] 请在 .env 文件中配置 XUNFEI_APPID / XUNFEI_API_KEY / XUNFEI_API_SECRET`

---

## TTS 模块（`tts/xunfei_tts.py`）

- [ ] 独立运行 `python tts/xunfei_tts.py`，输入 `"Hello, welcome to your interview."`，在 `tests/fixtures/` 目录生成 `tts_test.mp3`，文件大小 > 0 字节
- [ ] `tts_test.mp3` 用 VLC 或系统播放器可正常播放，能听到英文语音
- [ ] TTS 合成失败时，函数抛出 `TTSError` 异常（而非返回空字节），调用方捕获后前端显示文案 `"语音播放失败，请查看文字回复"`

---

## 实时对话延迟（`tests/latency_bench.py`）

- [ ] 运行 `python tests/latency_bench.py`，脚本模拟发送预录音频，打印 10 次测量结果
- [ ] **P50 延迟 ≤ 1.5s**（从发送 `audio_end` 消息到收到第一个 `tts_chunk` 消息）
- [ ] **P95 延迟 ≤ 2.5s**（同上测量口径）
- [ ] 网络正常时，前端页面不出现"连接超时"提示

---

## WebSocket 稳定性

- [ ] 连续进行 10 轮对话（每轮用户发言 ≤ 20 秒），WebSocket 连接不断开
- [ ] 用户点击"打断"按钮，AI 语音在 500ms 内停止播放，麦克风按钮变为可用状态
- [ ] 浏览器刷新页面后，旧 WebSocket 连接被服务端正常清理（不残留），重新打开后可正常发起新会话
- [ ] 网络断开（关闭 WiFi）时，前端页面在 5s 内显示文案 `"网络连接中断，请检查后重试"`，而非空白页或 JS 报错

---

## 面试场景阶段推进

- [ ] 会话开始，AI 第一句话包含引导自我介绍的表达（如 "tell me about yourself" 或 "please introduce yourself"），不出现岗位问答或行为面试题
- [ ] `interview.yaml` 中 `intro.max_turns` 设为 **2** 时：用户完成 2 轮发言后，AI 下一句话明确切换到岗位问答（如 "Now let's talk about the role..."）
- [ ] 页面顶部阶段进度条：当前阶段节点颜色与其他节点不同（如蓝色 vs 灰色），切换阶段时 UI 立即更新
- [ ] 四个阶段均可正常经历，不出现阶段跳过或循环
- [ ] 反问环节结束后，AI 说出结束语（包含 "Thank you for your time" 或等效表达），"查看报告"按钮出现

---

## 纠错弹窗

- [ ] 用户说出明显语法错误（如 "I am work here for 3 years."），AI 回复出现后 **3s 内** 弹窗自动显示
- [ ] 弹窗包含三行非空内容：`原始表达`（标红）、`建议表达`（标绿）、`说明`（一句英文解释）
- [ ] 用户说出无明显错误的标准英文（如 "I have been working as a software engineer for three years."），本轮不弹窗
- [ ] 点击弹窗右上角 ✕ 关闭按钮，弹窗在 200ms 内消失，麦克风按钮仍可用
- [ ] 同一轮只弹一次纠错弹窗，不重复弹出

---

## 表达评分（`llm/scorer.py`）

- [ ] 传入 3 条以上用户发言文字列表，函数返回 dict 包含 `accuracy_score`、`fluency_score`、`vocabulary_score` 三个键，值均为 **0–100 整数**（不是浮点数，不是字符串）
- [ ] 传入包含中文片段的发言列表（如 `["I want to 申请 this position"]`），函数正常返回评分，不抛异常
- [ ] 传入空列表 `[]` 时，函数返回 `{"accuracy_score": 0, "fluency_score": 0, "vocabulary_score": 0}`，不报错

---

## 课后报告

- [ ] 会话结束后，`reports/` 目录生成文件名格式为 `session_YYYYMMDD_HHMMSS.html` 的文件（如 `session_20260605_143022.html`）
- [ ] 报告 HTML 包含以下所有内容：
  - [ ] 本次对话总轮数（数字）
  - [ ] 三项评分数值（accuracy / fluency / vocabulary，各为 0–100 整数）
  - [ ] 对话记录全文（用户与 AI 的发言逐条列出）
  - [ ] 纠错汇总：若本次有纠错则列出至少 1 条；若无纠错则显示文案 `"本次对话无明显语法错误"`
- [ ] 用浏览器直接打开 HTML 文件（file:// 协议），页面正常渲染，无 404 资源请求（所有样式内联）
- [ ] 前端点击"查看报告"按钮，报告在 **新标签页** 打开，而非当前页跳转
- [ ] 报告中对话轮数与实际对话轮数一致（误差为 0）

---

## 端到端验收（最终必过）

- [ ] 从零启动（`python main.py`）到进入对话页面，全程无需修改代码或配置（仅需 `.env` 文件存在）
- [ ] 执行完整面试流程：选择面试场景 → 依次经历 **全部 4 个阶段** → 进行 **≥ 5 轮** 用户发言 → 退出会话 → 在 `reports/` 目录看到本次报告 HTML 文件
- [ ] 报告 HTML 中的对话轮数 **≥ 5**，与实际对话轮数一致
- [ ] 全程（从打开网页到查看报告）无需重启服务或刷新页面
- [ ] 全程 Chrome DevTools Console 无未处理的红色 JS 报错

---

## 附：测试夹具（Fixtures）说明

| 文件 | 内容 | 用途 |
|------|------|------|
| `tests/fixtures/hello_en.wav` | 3 秒英文录音："Hello, my name is Alex and I'm applying for the software engineer position." | STT 模块测试 |
| `tests/fixtures/mixed_lang.wav` | 中英混合："I want to apply for this position 这个工作" | STT 容错测试 |
| `tests/fixtures/grammar_error.wav` | 含明显语法错误："I am work here for 3 years." | 纠错触发测试 |
