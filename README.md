# 朗言 AI — AI 英语口语陪练应用

> 七牛云 × XEngineer 实训营参赛作品

沉浸式 AI 英语口语陪练工具。不做选择题、不做跟读，让你真正开口完成一次完整的真实场景对话（求职面试、餐厅点餐、商务会议），并在对话过程中和结束后获得即时反馈。

## 功能特性

- **场景化对话**：面试场景按阶段推进（自我介绍 → 岗位问答 → 行为面试题 → 反问环节）
- **实时语音交互**：语音输入 → AI 回复 → 语音输出，端到端对话体验
- **即时纠错**：每轮对话后弹窗展示语法与表达建议
- **表达评分**：准确度 / 流利度 / 词汇丰富度三维评分
- **课后报告**：会话结束后生成 HTML 学习报告

## 技术栈

| 层 | 技术 |
|----|------|
| 后端框架 | Python + FastAPI + Uvicorn |
| 实时通信 | WebSocket（fastapi + websockets） |
| 语音识别 (STT) | 科大讯飞实时语音转写 API |
| 语音合成 (TTS) | 科大讯飞在线语音合成 API |
| 对话 AI | Anthropic Claude API (claude-sonnet-4-6) |
| 前端 | 原生 HTML / CSS / JavaScript（无框架）|

## 第三方依赖说明

```
fastapi        Web 框架
uvicorn        ASGI 服务器
websockets     WebSocket 客户端（连接讯飞）
anthropic      Claude API SDK
python-dotenv  环境变量管理
aiohttp        异步 HTTP 请求
pyyaml         场景配置文件解析
aiofiles       异步文件写入（报告生成）
```

所有依赖均为项目原创功能服务，无复用历史代码。

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/666yuan/langyan.git
cd langyan
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入讯飞和 Anthropic 的 API Key
```

`.env` 需要填写：

```
XUNFEI_APPID=...
XUNFEI_API_KEY=...
XUNFEI_API_SECRET=...
ANTHROPIC_API_KEY=...
```

### 4. 启动服务

```bash
python main.py
```

打开浏览器访问 `http://localhost:8000`

## 项目结构

```
langyan/
├── main.py              # FastAPI 入口
├── stt/                 # 语音识别模块（讯飞）
├── tts/                 # 语音合成模块（讯飞）
├── llm/                 # LLM 对话 / 纠错 / 评分
├── scenarios/           # 场景配置（YAML）
├── reports/             # 课后报告（运行时生成）
├── static/              # 前端静态文件
└── tests/               # 测试与基准脚本
```

## 开发进度

| Task | 功能 | 状态 |
|------|------|------|
| Task 01 | 项目初始化与目录骨架 | ✅ |
| Task 02 | 讯飞 STT 接入 | 🔄 |
| Task 03 | 讯飞 TTS 接入 | ⬜ |
| Task 04 | LLM 对话 + 面试阶段状态机 | ⬜ |
| Task 05 | LLM 纠错模块 | ⬜ |
| Task 06 | Web 界面完整实现 | ⬜ |
| Task 07 | WebSocket 实时音频流水线 | ⬜ |
| Task 08 | 表达评分模块 | ⬜ |
| Task 09 | 课后报告 HTML 生成 | ⬜ |
| Task 10 | 接入主流程（端到端串联）| ⬜ |
| Task 11 | 端到端验证 | ⬜ |

## License

MIT
