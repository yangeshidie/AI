# 工作流系统使用指南

## 概述

Nexus AI 工作流系统是一个基于 Dify 灵感开发的可视化工作流编排系统，允许用户通过拖拽方式创建复杂的 AI 应用流程。

## 核心功能

### 1. 节点类型

| 节点类型 | 功能 | 配置参数 |
|---------|------|---------|
| **LLM** | 调用大语言模型 | model, api_url, api_key, system_prompt, temperature, user_message |
| **RAG** | 检索增强生成 | kb_ids, query, top_k |
| **Code** | 执行 Python 代码 | code, timeout |
| **Condition** | 条件分支判断 | conditions, default_branch |
| **HTTP** | 发送 HTTP 请求 | url, method, headers, body, timeout |
| **Variable** | 定义变量 | variable_name, default_value, variable_type |
| **Template** | 文本模板 | template |

### 2. 变量引用

在工作流中，可以使用 `{{变量名}}` 的格式引用变量：

```python
# 引用输入变量
{{user_input}}

# 引用节点输出
{{llm_1}}

# 引用全局变量
{{api_key}}
```

### 3. 工作流模板

系统提供了三个预置模板：

#### 简单对话 (simple_chat)
```
[START] → [LLM] → [END]
```

#### RAG 对话 (rag_chat)
```
[START] → [RAG] → [Template] → [LLM] → [END]
```

#### 条件分支 (conditional_flow)
```
              → [LLM Admin] ─┐
[START] → [Condition] ─┼→ [LLM User] ─→ [END]
              → [LLM Default]─┘
```

## API 文档

### 1. 创建工作流

```bash
POST /api/workflows/create
Content-Type: application/json

{
  "name": "我的工作流",
  "description": "工作流描述",
  "nodes": [...],
  "edges": [...],
  "variables": {
    "api_key": "sk-xxx"
  }
}
```

### 2. 列出工作流

```bash
GET /api/workflows/list
```

### 3. 获取工作流详情

```bash
GET /api/workflows/{workflow_id}
```

### 4. 更新工作流

```bash
POST /api/workflows/{workflow_id}
Content-Type: application/json

{
  "name": "新名称",
  "nodes": [...],
  "edges": [...]
}
```

### 5. 删除工作流

```bash
DELETE /api/workflows/{workflow_id}
```

### 6. 执行工作流

```bash
POST /api/workflows/{workflow_id}/execute
Content-Type: application/json

{
  "inputs": {
    "user_input": "你好",
    "user_type": "admin"
  },
  "stream": false
}
```

### 7. 获取工作流模板

```bash
GET /api/workflows/templates/{template_name}

# 可用模板: simple_chat, rag_chat, conditional_flow
```

## 使用示例

### 示例 1: 创建简单的对话工作流

```python
import requests

# 创建工作流
workflow_data = {
    "name": "简单对话",
    "description": "一个简单的 LLM 对话工作流",
    "nodes": [
        {
            "node_id": "start",
            "node_type": "start",
            "position": {"x": 100, "y": 100},
            "data": {}
        },
        {
            "node_id": "llm_1",
            "node_type": "llm",
            "position": {"x": 300, "y": 100},
            "data": {
                "model": "gpt-3.5-turbo",
                "api_url": "https://api.openai.com/v1",
                "api_key": "sk-xxx",
                "system_prompt": "你是一个智能助手",
                "temperature": 0.7,
                "user_message": "{{user_input}}"
            }
        },
        {
            "node_id": "end",
            "node_type": "end",
            "position": {"x": 500, "y": 100},
            "data": {
                "output_mapping": {
                    "response": "{{llm_1}}"
                }
            }
        }
    ],
    "edges": [
        {"id": "e1", "source": "start", "target": "llm_1"},
        {"id": "e2", "source": "llm_1", "target": "end"}
    ],
    "variables": {}
}

response = requests.post(
    "http://localhost:9000/api/workflows/create",
    json=workflow_data
)
print(response.json())
```

### 示例 2: 执行工作流

```python
import requests

# 执行工作流
execution_data = {
    "inputs": {
        "user_input": "你好，请介绍一下你自己"
    },
    "stream": False
}

response = requests.post(
    "http://localhost:9000/api/workflows/{workflow_id}/execute",
    json=execution_data
)
result = response.json()

print(f"执行状态: {result['status']}")
print(f"执行时间: {result['execution_time']:.2f}s")
print(f"输出结果: {result['outputs']}")
print(f"节点结果: {result['node_results']}")
```

### 示例 3: 创建 RAG 工作流

```python
import requests

workflow_data = {
    "name": "知识库问答",
    "description": "基于知识库的问答系统",
    "nodes": [
        {
            "node_id": "start",
            "node_type": "start",
            "position": {"x": 100, "y": 100},
            "data": {}
        },
        {
            "node_id": "rag_1",
            "node_type": "rag",
            "position": {"x": 300, "y": 100},
            "data": {
                "kb_ids": ["kb_12345"],
                "query": "{{user_input}}",
                "top_k": 3
            }
        },
        {
            "node_id": "llm_1",
            "node_type": "llm",
            "position": {"x": 500, "y": 100},
            "data": {
                "model": "gpt-3.5-turbo",
                "api_url": "https://api.openai.com/v1",
                "api_key": "sk-xxx",
                "system_prompt": "你是一个知识库助手，基于提供的上下文回答问题",
                "user_message": "上下文：\n{{rag_1}}\n\n问题：{{user_input}}"
            }
        },
        {
            "node_id": "end",
            "node_type": "end",
            "position": {"x": 700, "y": 100},
            "data": {
                "output_mapping": {
                    "response": "{{llm_1}}",
                    "context": "{{rag_1}}"
                }
            }
        }
    ],
    "edges": [
        {"id": "e1", "source": "start", "target": "rag_1"},
        {"id": "e2", "source": "rag_1", "target": "llm_1"},
        {"id": "e3", "source": "llm_1", "target": "end"}
    ],
    "variables": {}
}

response = requests.post(
    "http://localhost:9000/api/workflows/create",
    json=workflow_data
)
print(response.json())
```

## 可视化编辑器

访问 `http://localhost:9000/static/workflow-editor.html` 可以使用可视化编辑器创建和编辑工作流。

### 编辑器功能

1. **添加节点**: 点击工具栏按钮添加不同类型的节点
2. **移动节点**: 拖拽节点到画布上的任意位置
3. **编辑属性**: 点击节点后在右侧面板编辑节点属性
4. **删除节点**: 点击节点右上角的 × 按钮
5. **保存工作流**: 点击"保存工作流"按钮
6. **加载模板**: 点击"加载模板"按钮加载预置模板
7. **清空画布**: 点击"清空"按钮清空所有节点

## 技术架构

### 后端架构

```
app/
├── workflow/
│   ├── schemas.py      # 数据模型定义
│   ├── engine.py      # 工作流执行引擎
│   └── manager.py     # 工作流管理器
└── routers/
    └── workflows.py   # 工作流 API 路由
```

### 执行流程

```
1. 接收工作流定义
   ↓
2. 构建节点邻接表
   ↓
3. 从起始节点开始执行
   ↓
4. 解析变量引用
   ↓
5. 执行节点逻辑
   ↓
6. 保存节点结果
   ↓
7. 根据边连接执行后续节点
   ↓
8. 到达结束节点，返回结果
```

### 变量解析优先级

```
1. 节点输出结果 (node_results)
   ↓
2. 输入变量 (inputs)
   ↓
3. 全局变量 (variables)
```

## 注意事项

1. **安全性**: 代码节点使用 `exec()` 执行，生产环境应使用沙箱环境
2. **性能**: 复杂工作流可能需要较长时间执行，建议使用流式输出
3. **错误处理**: 节点执行失败会中断整个工作流，建议添加条件节点进行错误处理
4. **循环引用**: 工作流引擎会检测循环引用并跳过已访问的节点
5. **变量命名**: 建议使用有意义的变量名，避免与系统变量冲突

## 扩展开发

### 添加新节点类型

1. 在 `schemas.py` 中定义节点数据模型
2. 在 `engine.py` 中实现节点执行逻辑
3. 在 `workflows.py` 中添加模板（可选）
4. 在前端 `workflow-editor.js` 中添加节点类型

### 自定义节点执行逻辑

```python
async def _execute_custom_node(self, node: Dict[str, Any]) -> Any:
    """执行自定义节点"""
    data = node.get("data", {})
    
    # 获取节点配置
    config = data.get("config", {})
    
    # 解析变量
    resolved_config = self._resolve_variables(config)
    
    # 执行自定义逻辑
    result = self._do_custom_logic(resolved_config)
    
    return result
```

## 未来计划

- [ ] 支持子工作流（嵌套工作流）
- [ ] 添加更多节点类型（数据库、邮件等）
- [ ] 支持工作流版本管理
- [ ] 添加工作流调试功能
- [ ] 支持工作流导入/导出
- [ ] 添加工作流模板市场
- [ ] 支持工作流协作编辑
- [ ] 添加工作流性能监控
