# Nexus AI Local

Nexus AI Local 是一个功能强大的本地 LLM API 调用与管理平台。它提供了一个现代化的 Web 界面，支持多模型对话、RAG（检索增强生成）知识库管理、智能体创建以及提示词管理。

## 功能特性

### 对话系统
- 多模型支持：兼容 OpenAI 格式的 API，支持流式和非流式对话
- 实时模型切换：无需重启即可切换不同的 LLM 模型
- 流式传输控制：全局开关控制是否启用流式输出
- 对话历史管理：自动保存和加载对话历史
- 多模态支持：支持文本和图片输入
- 图片生成：支持 Base64 图片自动保存和本地存储
- 超时控制：5分钟超时设置，适合长图片生成任务

### RAG 知识库
- 多格式文件上传：支持 PDF、TXT、MD 等多种格式
- 本地向量检索：基于 ChromaDB 的本地向量数据库
- 智能分块：自动将文档分块存储，提高检索精度
- 动态智能体：创建具有特定知识背景的 AI 助手
- 知识库管理：支持知识库的创建、删除和查询

### 智能体系统
- 角色定义：为智能体设定特定的角色和性格
- 知识库挂载：将特定知识库挂载到智能体
- 系统提示词：自定义智能体的行为模式
- 智能体库：管理和复用创建的智能体

### 提示词管理
- 本地存储：常用提示词本地保存
- 快速调用：一键调用预设提示词
- 增删改查：完整的提示词管理功能
- 分类管理：支持提示词分类和标签

### 富文本体验
- Markdown 渲染：实时渲染 Markdown 格式文本
- 代码高亮：支持多种编程语言的语法高亮
- LaTeX 公式：支持数学公式显示和渲染
- 可拖拽输入框：灵活调整输入区域大小
- 响应式设计：适配不同屏幕尺寸

### 本地化存储
- 完全本地运行：不上传任何数据到云端（除非配置的 API 是云端服务）
- 隐私保护：对话历史、知识库、提示词均存储在本地
- 数据持久化：自动保存所有用户数据

## 技术架构

### 后端技术栈
- Python 3.10+
- FastAPI：高性能 Web 框架
- OpenAI SDK：LLM API 调用
- ChromaDB：向量数据库
- SentenceTransformers：文本向量化
- PyPDF：PDF 文档解析
- DuckDuckGo Search：网络搜索集成

### 前端技术栈
- HTML5：页面结构
- CSS3：样式设计
- Vanilla JavaScript (ES6+)：交互逻辑
- Marked.js：Markdown 渲染
- Highlight.js：代码高亮
- KaTeX：LaTeX 公式渲染
- Material Symbols：图标库

### 包管理
- Poetry：Python 依赖管理和虚拟环境

## 快速开始

### 环境准备

确保你的系统已安装：
- Python 3.10 或更高版本
- Poetry（Python 包管理工具）

```bash
pip install poetry
```

### 安装依赖

在项目根目录运行：

```bash
poetry install
```

### 配置环境变量

创建 `.env` 文件（可选），配置默认 API 信息：

```env
PROXY_BASE_URL=https://api.openai.com/v1
PROXY_API_KEY=your-api-key-here
TARGET_MODEL=gpt-3.5-turbo
```

### 启动应用

```bash
cd src
poetry run python main.py
```

或者，如果你已经激活了虚拟环境：

```bash
cd src
python main.py
```

服务器将在 `http://127.0.0.1:8000` 启动。

### 首次配置

首次访问时，请在**设置**页面配置你的 API 信息：
- API Endpoint：你的 LLM API 地址
  - OpenAI: `https://api.openai.com/v1`
  - 本地 Ollama: `http://localhost:11434/v1`
  - 其他兼容 OpenAI 格式的 API
- API Key：你的 API 密钥
- 默认模型：选择默认使用的模型

## 使用指南

### 对话功能

1. **发起对话**：在输入框中输入消息，点击发送或按 Enter 键
2. **切换模型**：在设置中选择不同的模型
3. **流式传输**：在设置中开启或关闭流式输出
   - 开启：响应会逐字显示，适合长文本生成
   - 关闭：等待完整响应后一次性显示
4. **图片输入**：点击图片图标上传图片，支持多模态对话
5. **查看历史**：左侧历史列表查看和切换对话历史

### 知识库管理

1. **上传文件**：在根数据库页面上传 PDF、TXT、MD 等文件
2. **创建智能体**：在智能体库页面创建新的智能体
3. **挂载知识库**：为智能体选择要挂载的知识库
4. **使用智能体**：在对话中选择使用特定智能体

### 提示词管理

1. **创建提示词**：在提示词库页面添加新提示词
2. **分类管理**：为提示词添加分类和标签
3. **快速调用**：在对话中快速调用预设提示词

## API 文档

### 聊天接口

#### POST /api/chat
发起聊天请求

**请求体：**
```json
{
  "model": "gpt-3.5-turbo",
  "api_url": "https://api.openai.com/v1",
  "api_key": "your-api-key",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": true,
  "kb_id": null
}
```

**响应（流式）：**
```
data: {"content": "Hello"}
data: {"done": true, "content": "Hello! How can I help you?"}
```

**响应（非流式）：**
```json
{
  "role": "assistant",
  "content": "Hello! How can I help you?"
}
```

### 模型列表

#### POST /api/models
获取可用模型列表

**请求体：**
```json
{
  "api_url": "https://api.openai.com/v1",
  "api_key": "your-api-key"
}
```

**响应：**
```json
{
  "models": ["gpt-3.5-turbo", "gpt-4", ...]
}
```

### 知识库管理

#### POST /api/kb/upload
上传文件到知识库

**请求：** multipart/form-data
- file: 文件
- kb_id: 知识库 ID

#### GET /api/kb/list
获取知识库列表

**响应：**
```json
{
  "kbs": [
    {
      "id": "kb_001",
      "name": "My Knowledge Base",
      "files": ["doc1.pdf", "doc2.txt"]
    }
  ]
}
```

### 历史记录

#### GET /api/history/list
获取对话历史列表

**响应：**
```json
{
  "sessions": [
    {
      "id": "chat_123",
      "title": "First Conversation",
      "created_at": "2025-12-26T10:00:00"
    }
  ]
}
```

#### GET /api/history/{session_id}
获取特定对话历史

**响应：**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

## 项目结构

```
.
├── pyproject.toml              # Poetry 依赖管理配置
├── poetry.lock                 # 依赖锁定文件
├── .gitignore                  # Git 忽略文件配置
├── README.md                   # 项目文档
├── plan.md                     # 项目规划文档
├── image_download.py           # 图片下载工具
├── advanced_system.py          # 高级系统提示词生成
│
└── src/                        # 源代码目录
    ├── main.py                 # 应用入口
    ├── test.py                 # 测试文件
    ├── test_settings.py        # 设置测试
    │
    ├── app/                    # 后端核心逻辑
    │   ├── __init__.py
    │   ├── config.py           # 配置管理
    │   ├── schemas.py          # Pydantic 数据模型
    │   │
    │   ├── core/               # 核心模块
    │   │   ├── __init__.py
    │   │   ├── rag_engine.py   # RAG 向量检索引擎
    │   │   ├── kb_manager.py   # 知识库管理器
    │   │   ├── history.py      # 对话历史管理
    │   │   └── file_manager.py # 文件管理器
    │   │
    │   └── routers/            # FastAPI 路由
    │       ├── __init__.py
    │       ├── chat.py         # 聊天相关接口
    │       ├── files.py        # 文件处理接口
    │       ├── kb.py           # 知识库接口
    │       ├── history.py      # 历史记录接口
    │       ├── prompts.py      # 提示词接口
    │       └── settings.py     # 设置接口
    │
    ├── static/                 # 前端静态资源
    │   ├── index.html          # 主页面
    │   ├── .gitignore
    │   │
    │   ├── css/                # 样式文件
    │   │   └── style.css
    │   │
    │   └── js/                 # JavaScript 模块
    │       ├── main.js         # 主入口
    │       ├── router.js       # 路由管理
    │       ├── state.js        # 状态管理
    │       ├── utils.js        # 工具函数
    │       ├── api.js          # API 调用
    │       │
    │       └── modules/        # 功能模块
    │           ├── chat.js      # 聊天模块
    │           ├── files.js     # 文件模块
    │           ├── history.js   # 历史记录模块
    │           ├── kb.js        # 知识库模块
    │           ├── prompts.js   # 提示词模块
    │           └── settings.js  # 设置模块
    │
    ├── storage/                # 提示词等本地数据存储（自动生成）
    ├── history/                # 对话历史存储（自动生成）
    ├── data_uploads/           # 上传文件存储（自动生成）
    ├── chroma_db/              # 向量数据库存储（自动生成）
    └── static/generated_images/ # 生成的图片存储（自动生成）
```

## 开发指南

### 添加新功能

1. **后端 API**：在 `src/app/routers/` 下创建新的路由文件
2. **前端模块**：在 `src/static/js/modules/` 下创建新的模块
3. **数据模型**：在 `src/app/schemas.py` 中定义 Pydantic 模型
4. **核心逻辑**：在 `src/app/core/` 下实现核心业务逻辑

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型提示（Type Hints）
- 模块化设计，高内聚低耦合
- 完善的错误处理和日志记录
- 详细的文档字符串

### 测试

```bash
cd src
poetry run python test.py
poetry run python test_settings.py
```

### 调试

应用启动后会自动生成日志，日志级别为 INFO。可以在 `src/main.py` 中修改日志级别：

```python
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG 获取更详细的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 常见问题

### Q: 如何切换到本地模型（如 Ollama）？

A: 在设置页面配置：
- API Endpoint: `http://localhost:11434/v1`
- API Key: `ollama`（或任意值）
- 默认模型: `llama2`（或其他已安装的模型）

### Q: 流式传输和非流式传输有什么区别？

A: 
- **流式传输**：响应会逐字显示，适合长文本生成，用户体验更好
- **非流式传输**：等待完整响应后一次性显示，适合短对话

### Q: 为什么非流式模式会返回 500 错误？

A: 非流式模式对错误处理更严格。如果图片处理失败或 API 返回异常格式，会返回 500 错误。建议使用流式模式以获得更好的容错性。

### Q: 如何备份我的数据？

A: 备份以下目录：
- `src/history/`：对话历史
- `src/storage/`：提示词和配置
- `src/chroma_db/`：向量数据库
- `src/data_uploads/`：上传的文件

### Q: 如何重置应用？

A: 删除以下目录并重启应用：
- `src/history/`
- `src/storage/`
- `src/chroma_db/`
- `src/data_uploads/`

### Q: 支持哪些文件格式？

A: 目前支持：
- PDF (.pdf)
- 文本文件 (.txt)
- Markdown (.md)
- 其他纯文本格式

### Q: 如何配置代理访问 Hugging Face？

A: 应用会自动检测代理（端口 7890）。如果检测到代理，会自动配置使用代理访问 Hugging Face；否则使用国内镜像。

## 性能优化

### RAG 检索优化
- 调整分块大小：在 `rag_engine.py` 中修改 `chunk_size` 参数
- 选择合适的嵌入模型：在 `rag_engine.py` 中修改 `model_name`

### 图片生成优化
- 调整超时时间：在 `chat.py` 中修改 `timeout` 参数
- 启用流式传输：减少等待时间

### 内存优化
- 定期清理历史记录
- 限制向量数据库大小
- 使用更小的嵌入模型

## 安全建议

- 不要将 `.env` 文件提交到版本控制
- 定期更新依赖包
- 使用强密码保护 API Key
- 限制文件上传大小
- 验证用户输入

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 提交 Issue
1. 清晰描述问题
2. 提供复现步骤
3. 附上错误日志
4. 说明环境和版本信息

### 提交 Pull Request
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 作者：2813204478@qq.com
- 项目地址：[[GitHub Repository](https://github.com/yangeshidie/AI)]

## 更新日志

### v0.1.0 (2025-12-26)
- 初始版本发布
- 支持多模型对话
- 实现 RAG 知识库功能
- 添加智能体系统
- 实现提示词管理
- 支持流式和非流式传输
- 添加图片生成和存储功能
- 实现代码高亮和 LaTeX 公式渲染
