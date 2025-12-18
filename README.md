# Nexus AI Local

Nexus AI Local 是一个功能强大的本地 LLM API 调用与管理平台。它提供了一个现代化的 Web 界面，支持多模型对话、RAG（检索增强生成）知识库管理、智能体创建以及提示词管理。

## ✨ 主要功能

- **💬 多模型对话**：兼容 OpenAI 格式的 API，支持流式对话，实时切换模型。
- **📚 RAG 知识库**：
    - 支持上传多种格式文件（PDF, TXT, MD 等）。
    - 基于 ChromaDB 的本地向量检索。
    - 动态创建智能体（Agent），挂载特定的知识库。
- **🤖 智能体系统**：创建具有特定角色和知识背景的 AI 助手。
- **🔖 提示词库**：
    - 本地存储常用提示词。
    - 一键调用，支持增删改查。
- **📝 富文本体验**：
    - Markdown 实时渲染。
    - 代码高亮。
    - **LaTeX 公式渲染**（支持数学公式显示）。
- **💾 本地化存储**：
    - 对话历史、知识库、提示词均存储在本地，保障隐私。
- **🎨 现代化 UI**：
    - 响应式设计，深色模式。
    - 可拖拽调整的输入框。

## 🛠️ 技术栈

- **后端**：Python 3.10+, FastAPI, LangChain, ChromaDB
- **前端**：HTML5, CSS3, Vanilla JavaScript (ES6+)
- **包管理**：Poetry

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装 Python 3.10 或更高版本，并安装了 `poetry`。

```bash
# 安装 poetry (如果尚未安装)
pip install poetry
```

### 2. 安装依赖

在项目根目录（`src` 的上一级目录，即包含 `pyproject.toml` 的目录）运行：

```bash
poetry install
```

### 3. 启动应用

进入 `src` 目录并启动服务器：

```bash
cd src
poetry run python main.py
```

或者，如果你已经激活了虚拟环境：

```bash
cd src
python main.py
```

服务器默认将在 `http://127.0.0.1:8000` 启动。

### 4. 配置

首次访问时，请在**设置**页面配置你的 API 信息：
- **API Endpoint**: 你的 LLM API 地址 (例如 `https://api.openai.com/v1` 或本地 Ollama 地址 `http://localhost:11434/v1`)
- **API Key**: 你的 API 密钥

## 📂 项目结构

```text
.
├── pyproject.toml       # (上级目录) 依赖管理配置
├── poetry.lock          # (上级目录) 依赖锁定文件
└── src/                 # 源代码目录
    ├── app/             # 后端核心逻辑
    │   ├── core/        # RAG, 历史记录, 文件管理等核心模块
    │   ├── routers/     # FastAPI 路由 (chat, files, kb, prompts)
    │   ├── config.py    # 配置文件
    │   ├── main.py      # 应用入口
    │   └── schemas.py   # Pydantic 数据模型
    ├── static/          # 前端静态资源
    │   ├── css/         # 样式文件
    │   ├── js/          # JavaScript 模块
    │   └── index.html   # 主页面
    ├── storage/         # (自动生成) 提示词等本地数据存储
    ├── history/         # (自动生成) 对话历史存储
    ├── chroma_db/       # (自动生成) 向量数据库存储
    └── main.py          # 启动脚本
```

## ⚠️ 注意事项

- 本项目完全本地运行，不上传任何数据到云端（除非你配置的 API 是云端服务）。
- 请确保 `src` 目录下的 `storage`, `history`, `chroma_db` 等目录有写入权限。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
