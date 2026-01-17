# Nexus AI Local API 文档

---
# **文件1**：src/main.py
---

### **API1_name**：GET /
**API1_function**: 返回主页面（index.html）
**API1_input**: 无
**API1_output**: FileResponse - index.html 文件
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/
```

---
# **文件2**：src/app/routers/chat.py
---

### **API1_name**：GET /api/config
**API1_function**: 获取默认 API 配置信息
**API1_input**: 无
**API1_output**: Dict[str, str] - 包含 api_url, api_key, model 的字典
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/api/config
```

### **API2_name**：POST /api/chat
**API2_function**: 处理聊天请求，支持流式和非流式响应
**API2_input**: 
```json
{
  "api_url": "string",
  "api_key": "string",
  "model": "string",
  "messages": [
    {
      "role": "user",
      "content": "string",
      "id": "string"
    }
  ],
  "session_file": "string (optional)",
  "kb_id": "string (optional)",
  "stream": false,
  "drawing_workspace_mode": false
}
```
**API2_output**: 
- 流式模式: StreamingResponse (text/event-stream)
- 非流式模式: Dict[str, str] - {"role": "assistant", "content": "string", "id": "string"}
**API2_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.openai.com/v1",
    "api_key": "sk-xxx",
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

### **API3_name**：POST /api/models
**API3_function**: 获取可用模型列表
**API3_input**: 
```json
{
  "api_url": "string",
  "api_key": "string"
}
```
**API3_output**: Dict[str, Any] - {"models": ["model1", "model2", ...]} 或 {"error": "string", "models": []}
**API3_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/models \
  -H "Content-Type: application/json" \
  -d '{
    "api_url": "https://api.openai.com/v1",
    "api_key": "sk-xxx"
  }'
```

### **API4_name**：POST /api/edit_message
**API4_function**: 编辑指定消息的内容
**API4_input**: 
```json
{
  "message_id": "string",
  "role": "user|assistant",
  "content": "string",
  "session_file": "string"
}
```
**API4_output**: Dict[str, Any] - {"success": true, "message": "消息编辑成功"}
**API4_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/edit_message \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "1234567890abc",
    "role": "user",
    "content": "New content",
    "session_file": "2025-01-17/chat_123.json"
  }'
```

### **API5_name**：POST /api/delete_message
**API5_function**: 删除指定消息
**API5_input**: 
```json
{
  "message_id": "string",
  "role": "user|assistant",
  "session_file": "string"
}
```
**API5_output**: Dict[str, Any] - {"success": true, "message": "消息删除成功"}
**API5_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/delete_message \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "1234567890abc",
    "role": "user",
    "session_file": "2025-01-17/chat_123.json"
  }'
```

---
# **文件3**：src/app/routers/files.py
---

### **API1_name**：GET /api/files/list
**API1_function**: 列出所有上传的文件
**API1_input**: 无
**API1_output**: Dict[str, List[Dict[str, Any]]] - {"files": [{"name": "string", "size": "string", "date": "string", "group": "string"}]}
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/api/files/list
```

### **API2_name**：POST /api/files/set_group
**API2_function**: 设置文件分组
**API2_input**: 
```json
{
  "filename": "string",
  "group": "string"
}
```
**API2_output**: Dict[str, str] - {"status": "success"}
**API2_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/files/set_group \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.pdf",
    "group": "技术文档"
  }'
```

### **API3_name**：POST /api/files/upload
**API3_function**: 上传文件并添加到 RAG 向量库
**API3_input**: multipart/form-data - file (UploadFile)
**API3_output**: Dict[str, Any] - {"status": "success", "filename": "string", "chunks": int}
**API3_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/files/upload \
  -F "file=@document.pdf"
```

### **API4_name**：POST /api/files/delete
**API4_function**: 删除文件
**API4_input**: 
```json
{
  "filename": "string",
  "confirm_delete": false
}
```
**API4_output**: 
- 成功: {"status": "success"}
- 文件被使用: {"status": "warning", "message": "File is in use", "affected_kbs": ["kb1", "kb2"]}
**API4_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/files/delete \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "document.pdf",
    "confirm_delete": true
  }'
```

### **API5_name**：POST /api/files/rename
**API5_function**: 重命名文件
**API5_input**: 
```json
{
  "filename": "string",
  "new_name": "string"
}
```
**API5_output**: Dict[str, str] - {"status": "success"}
**API5_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/files/rename \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "old_name.pdf",
    "new_name": "new_name.pdf"
  }'
```

### **API6_name**：POST /api/files/extract_text
**API6_function**: 从上传的文件中提取文本内容（不保存到磁盘）
**API6_input**: multipart/form-data - file (UploadFile)
**API6_output**: Dict[str, str] - {"filename": "string", "text": "string"}
**API6_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/files/extract_text \
  -F "file=@document.pdf"
```

---
# **文件4**：src/app/routers/kb.py
---

### **API1_name**：POST /api/kb/create
**API1_function**: 创建新知识库
**API1_input**: 
```json
{
  "name": "string",
  "description": "string",
  "files": ["file1.pdf", "file2.pdf"]
}
```
**API1_output**: Dict[str, Any] - 创建的知识库信息
**API1_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/kb/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "技术知识库",
    "description": "包含技术文档的知识库",
    "files": ["doc1.pdf", "doc2.pdf"]
  }'
```

### **API2_name**：GET /api/kb/list
**API2_function**: 列出所有知识库
**API2_input**: 无
**API2_output**: Dict[str, List[Dict[str, Any]]] - {"kbs": [{"id": "string", "name": "string", "description": "string", "files": [], "created_at": "string"}]}
**API2_sample**: 
```bash
curl http://127.0.0.1:9000/api/kb/list
```

### **API3_name**：POST /api/kb/delete
**API3_function**: 删除指定知识库
**API3_input**: 
```json
{
  "kb_id": "string"
}
```
**API3_output**: Dict[str, str] - {"status": "success"}
**API3_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/kb/delete \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "abc12345"
  }'
```

### **API4_name**：POST /api/kb/update
**API4_function**: 更新知识库信息
**API4_input**: 
```json
{
  "kb_id": "string",
  "name": "string",
  "description": "string",
  "files": ["file1.pdf", "file2.pdf"] (optional)
}
```
**API4_output**: 
- 成功: {"status": "success", "kb": {...}}
- 失败: {"status": "error", "message": "知识库不存在"}
**API4_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/kb/update \
  -H "Content-Type: application/json" \
  -d '{
    "kb_id": "abc12345",
    "name": "新名称",
    "description": "新描述",
    "files": ["doc1.pdf"]
  }'
```

---
# **文件5**：src/app/routers/history.py
---

### **API1_name**：GET /api/history/list
**API1_function**: 列出所有历史记录，按日期分组
**API1_input**: 无
**API1_output**: Dict[str, List[str]] - {"2025-01-17": ["chat1.json", "chat2.json"], ...}
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/api/history/list
```

### **API2_name**：POST /api/history/load
**API2_function**: 加载指定的历史记录
**API2_input**: 
```json
{
  "filepath": "2025-01-17/chat_123.json"
}
```
**API2_output**: Dict[str, Any] - {"messages": [...], "kb_id": "string"}
**API2_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/history/load \
  -H "Content-Type: application/json" \
  -d '{
    "filepath": "2025-01-17/chat_123.json"
  }'
```

### **API3_name**：POST /api/history/delete
**API3_function**: 删除指定的历史记录
**API3_input**: 
```json
{
  "filename": "2025-01-17/chat_123.json"
}
```
**API3_output**: Dict[str, str] - {"status": "success"}
**API3_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/history/delete \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "2025-01-17/chat_123.json"
  }'
```

### **API4_name**：POST /api/history/rename
**API4_function**: 重命名历史记录
**API4_input**: 
```json
{
  "filename": "2025-01-17/chat_123.json",
  "new_name": "new_chat.json"
}
```
**API4_output**: Dict[str, str] - {"status": "success"}
**API4_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/history/rename \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "2025-01-17/chat_123.json",
    "new_name": "new_chat.json"
  }'
```

---
# **文件6**：src/app/routers/settings.py
---

### **API1_name**：GET /api/settings/configs
**API1_function**: 列出所有保存的 API 配置名称
**API1_input**: 无
**API1_output**: {"configs": ["config1", "config2", ...]}
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/api/settings/configs
```

### **API2_name**：GET /api/settings/config/{name}
**API2_function**: 获取指定配置的详细信息
**API2_input**: 路径参数 name (string)
**API2_output**: {"name": "string", "base_url": "string", "api_key": "string"}
**API2_sample**: 
```bash
curl http://127.0.0.1:9000/api/settings/config/openai
```

### **API3_name**：POST /api/settings/configs
**API3_function**: 保存或更新 API 配置到 .env 文件
**API3_input**: 
```json
{
  "name": "string",
  "base_url": "string",
  "api_key": "string"
}
```
**API3_output**: {"status": "success", "message": "Config 'xxx' saved"}
**API3_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/settings/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai",
    "base_url": "https://api.openai.com/v1",
    "api_key": "sk-xxx"
  }'
```

---
# **文件7**：src/app/routers/prompts.py
---

### **API1_name**：GET /api/prompts
**API1_function**: 获取所有保存的 prompts
**API1_input**: 无
**API1_output**: List[Dict[str, Any]] - [{"id": "string", "name": "string", "content": "string"}]
**API1_sample**: 
```bash
curl http://127.0.0.1:9000/api/prompts
```

### **API2_name**：POST /api/prompts
**API2_function**: 创建新的 prompt
**API2_input**: 
```json
{
  "name": "string",
  "content": "string"
}
```
**API2_output**: Dict[str, Any] - {"id": "string", "name": "string", "content": "string"}
**API2_sample**: 
```bash
curl -X POST http://127.0.0.1:9000/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "翻译助手",
    "content": "你是一个专业的翻译助手，请将用户输入的文本翻译成英文。"
  }'
```

### **API3_name**：DELETE /api/prompts/{prompt_id}
**API3_function**: 删除指定 ID 的 prompt
**API3_input**: 路径参数 prompt_id (string)
**API3_output**: {"message": "Prompt deleted successfully"}
**API3_sample**: 
```bash
curl -X DELETE http://127.0.0.1:9000/api/prompts/abc123-def456
```

---
# **文件8**：src/app/core/api_adapter.py
---

### **API1_name**：MultimodalAdapter.__init__
**API1_function**: 初始化多模态适配器，设置图片保存目录
**API1_input**: 
- image_save_dir: Optional[Path] - 图片保存目录，默认为 STATIC_DIR / "generated_images"
**API1_output**: MultimodalAdapter 实例
**API1_sample**: 
```python
from app.core.api_adapter import MultimodalAdapter
from pathlib import Path

adapter = MultimodalAdapter()
# 或指定自定义目录
adapter = MultimodalAdapter(image_save_dir=Path("custom_images"))
```

### **API2_name**：MultimodalAdapter.prepare_messages
**API2_function**: 准备发送给 API 的消息列表，处理图片上下文持久化
**API2_input**: 
- messages: List[Dict[str, Any]] - 消息列表
- drawing_workspace_mode: bool - 是否为绘图工作区模式
**API2_output**: List[Dict[str, Any]] - 处理后的消息列表
**API2_sample**: 
```python
from app.core.api_adapter import MultimodalAdapter

adapter = MultimodalAdapter()
messages = [
    {"role": "user", "content": "Hello"}
]
prepared = adapter.prepare_messages(messages, drawing_workspace_mode=False)
```

### **API3_name**：MultimodalAdapter.process_response
**API3_function**: 处理模型响应，提取并保存图片
**API3_input**: 
- response_content: str - 模型响应内容
**API3_output**: str - 处理后的响应内容（图片链接已替换为本地路径）
**API3_sample**: 
```python
from app.core.api_adapter import MultimodalAdapter

adapter = MultimodalAdapter()
processed = adapter.process_response("![image](data:image/png;base64,...)")
```

---
# **文件9**：src/app/core/file_manager.py
---

### **API1_name**：FileManager.set_group
**API1_function**: 设置文件的分组
**API1_input**: 
- filename: str - 文件名
- group: str - 分组名称
**API1_output**: null
**API1_sample**: 
```python
from app.core.file_manager import file_manager

file_manager.set_group("document.pdf", "技术文档")
```

### **API2_name**：FileManager.get_group
**API2_function**: 获取文件的分组
**API1_input**: 
- filename: str - 文件名
**API2_output**: str - 分组名称，默认为"未分组"
**API2_sample**: 
```python
from app.core.file_manager import file_manager

group = file_manager.get_group("document.pdf")
```

### **API3_name**：FileManager.get_all_groups
**API3_function**: 获取所有已使用的分组名称
**API3_input**: 无
**API3_output**: List[str] - 分组名称列表
**API3_sample**: 
```python
from app.core.file_manager import file_manager

groups = file_manager.get_all_groups()
```

### **API4_name**：FileManager.delete_meta
**API4_function**: 删除文件的元数据
**API4_input**: 
- filename: str - 文件名
**API4_output**: null
**API4_sample**: 
```python
from app.core.file_manager import file_manager

file_manager.delete_meta("document.pdf")
```

### **API5_name**：FileManager.rename_meta
**API5_function**: 重命名文件时同步更新元数据
**API5_input**: 
- old_name: str - 旧文件名
- new_name: str - 新文件名
**API5_output**: null
**API5_sample**: 
```python
from app.core.file_manager import file_manager

file_manager.rename_meta("old.pdf", "new.pdf")
```

---
# **文件10**：src/app/core/history.py
---

### **API1_name**：save_history
**API1_function**: 保存聊天历史到按日期组织的目录中
**API1_input**: 
- messages: List[Dict[str, Any]] - 消息列表
- filename: str - 文件名或完整路径
- kb_id: Optional[str] - 关联的知识库ID
**API1_output**: null
**API1_sample**: 
```python
from app.core.history import save_history

messages = [
    {"role": "user", "content": "Hello", "id": "123"},
    {"role": "assistant", "content": "Hi there!", "id": "456"}
]
save_history(messages, "chat_123.json", kb_id="abc12345")
```

### **API2_name**：get_all_history
**API2_function**: 获取所有历史记录，按日期分组
**API2_input**: 无
**API2_output**: Dict[str, List[str]] - 日期 -> 文件名列表 的字典
**API2_sample**: 
```python
from app.core.history import get_all_history

history = get_all_history()
```

### **API3_name**：load_history_file
**API3_function**: 加载指定的历史文件
**API3_input**: 
- filepath_str: str - 相对于 HISTORY_DIR 的文件路径
**API3_output**: Optional[Dict[str, Any]] - 包含 messages 和 kb_id 的字典
**API3_sample**: 
```python
from app.core.history import load_history_file

data = load_history_file("2025-01-17/chat_123.json")
```

---
# **文件11**：src/app/core/kb_manager.py
---

### **API1_name**：KBManager.create_kb
**API1_function**: 创建新的知识库
**API1_input**: 
- name: str - 知识库名称
- description: str - 知识库描述
- files: List[str] - 关联的文件列表
**API1_output**: Dict[str, Any] - 创建的知识库信息
**API1_sample**: 
```python
from app.core.kb_manager import kb_manager

kb = kb_manager.create_kb("技术知识库", "包含技术文档", ["doc1.pdf"])
```

### **API2_name**：KBManager.list_kbs
**API2_function**: 列出所有知识库
**API2_input**: 无
**API2_output**: Dict[str, Any] - 所有知识库信息
**API2_sample**: 
```python
from app.core.kb_manager import kb_manager

kbs = kb_manager.list_kbs()
```

### **API3_name**：KBManager.get_kb
**API3_function**: 根据 ID 获取知识库信息
**API3_input**: 
- kb_id: str - 知识库ID
**API3_output**: Optional[Dict[str, Any]] - 知识库信息，不存在则返回 None
**API3_sample**: 
```python
from app.core.kb_manager import kb_manager

kb = kb_manager.get_kb("abc12345")
```

### **API4_name**：KBManager.delete_kb
**API4_function**: 删除指定的知识库
**API4_input**: 
- kb_id: str - 知识库ID
**API4_output**: null
**API4_sample**: 
```python
from app.core.kb_manager import kb_manager

kb_manager.delete_kb("abc12345")
```

### **API5_name**：KBManager.update_kb
**API5_function**: 更新知识库信息
**API5_input**: 
- kb_id: str - 知识库ID
- name: str - 新的名称
- description: str - 新的描述
- files: Optional[List[str]] - 新的文件列表
**API5_output**: Optional[Dict[str, Any]] - 更新后的知识库信息
**API5_sample**: 
```python
from app.core.kb_manager import kb_manager

kb = kb_manager.update_kb("abc12345", "新名称", "新描述", ["doc1.pdf"])
```

### **API6_name**：KBManager.find_kbs_using_file
**API6_function**: 查找使用特定文件的所有知识库
**API6_input**: 
- filename: str - 文件名
**API6_output**: List[str] - 使用该文件的知识库名称列表
**API6_sample**: 
```python
from app.core.kb_manager import kb_manager

kbs = kb_manager.find_kbs_using_file("doc1.pdf")
```

### **API7_name**：KBManager.remove_file_from_all_kbs
**API7_function**: 从所有知识库中移除指定文件
**API7_input**: 
- filename: str - 文件名
**API7_output**: null
**API7_sample**: 
```python
from app.core.kb_manager import kb_manager

kb_manager.remove_file_from_all_kbs("doc1.pdf")
```

### **API8_name**：KBManager.rename_file_in_kbs
**API8_function**: 在所有知识库中重命名文件
**API8_input**: 
- old_name: str - 旧文件名
- new_name: str - 新文件名
**API8_output**: null
**API8_sample**: 
```python
from app.core.kb_manager import kb_manager

kb_manager.rename_file_in_kbs("old.pdf", "new.pdf")
```

---
# **文件12**：src/app/core/rag_engine.py
---

### **API1_name**：add_text_to_rag
**API1_function**: 将文本分块后添加到 RAG 向量库
**API1_input**: 
- filename: str - 文件名
- text: str - 要添加的文本内容
- chunk_size: int - 分块大小，默认为 500
**API1_output**: int - 添加的块数量
**API1_sample**: 
```python
from app.core.rag_engine import add_text_to_rag

count = add_text_to_rag("doc1.pdf", "这是一段很长的文本内容...", chunk_size=500)
```

### **API2_name**：query_rag_with_filter
**API2_function**: 在指定文件范围内查询 RAG
**API2_input**: 
- query: str - 查询文本
- allowed_files: List[str] - 允许检索的文件列表
- n_results: int - 返回结果数量，默认为 3
**API2_output**: str - 拼接的检索结果文本
**API2_sample**: 
```python
from app.core.rag_engine import query_rag_with_filter

result = query_rag_with_filter("如何使用API", ["doc1.pdf", "doc2.pdf"], n_results=3)
```

### **API3_name**：delete_from_rag
**API3_function**: 从 RAG 中删除指定文件的所有块
**API3_input**: 
- filename: str - 文件名
**API3_output**: null
**API3_sample**: 
```python
from app.core.rag_engine import delete_from_rag

delete_from_rag("doc1.pdf")
```

### **API4_name**：rename_in_rag
**API4_function**: 在 RAG 中重命名文件的元数据
**API4_input**: 
- old_name: str - 旧文件名
- new_name: str - 新文件名
**API4_output**: null
**API4_sample**: 
```python
from app.core.rag_engine import rename_in_rag

rename_in_rag("old.pdf", "new.pdf")
```

---
# **文件13**：src/advanced_system.py
---

### **API1_name**：SystemPromptBuilder.set_role
**API1_function**: 设定角色人设
**API1_input**: 
- role_text: str - 角色描述文本
**API1_output**: SystemPromptBuilder - 返回自身以支持链式调用
**API1_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.set_role("你是一个专业的翻译助手")
```

### **API2_name**：SystemPromptBuilder.bind_knowledge_base
**API2_function**: 绑定知识库名称，增强沉浸感
**API2_input**: 
- kb_name: str - 知识库名称
**API2_output**: SystemPromptBuilder - 返回自身以支持链式调用
**API2_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.bind_knowledge_base("技术知识库")
```

### **API3_name**：SystemPromptBuilder.inject_context
**API3_function**: 注入 RAG 检索到的上下文
**API3_input**: 
- context: str - 上下文文本
**API3_output**: SystemPromptBuilder - 返回自身以支持链式调用
**API3_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.inject_context("这是从知识库检索到的相关内容...")
```

### **API4_name**：SystemPromptBuilder.add_constraint
**API4_function**: 添加限制条件
**API4_input**: 
- constraint: str - 限制条件文本
**API4_output**: SystemPromptBuilder - 返回自身以支持链式调用
**API4_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.add_constraint("不要编造事实")
builder.add_constraint("使用简洁的语言")
```

### **API5_name**：SystemPromptBuilder.set_output_style
**API5_function**: 设定输出风格
**API5_input**: 
- style: str - 输出风格描述
**API5_output**: SystemPromptBuilder - 返回自身以支持链式调用
**API5_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
builder.set_output_style("使用 Markdown 格式输出")
```

### **API6_name**：SystemPromptBuilder.build
**API6_function**: 生成最终发送给 API 的 system message 对象
**API6_input**: 无
**API6_output**: Dict[str, str] - {"role": "system", "content": "string"}
**API6_sample**: 
```python
from advanced_system import SystemPromptBuilder

builder = SystemPromptBuilder()
system_msg = (
    builder.set_role("你是一个翻译助手")
    .add_constraint("使用简洁的语言")
    .build()
)
```

### **API7_name**：create_rag_system_prompt
**API7_function**: 创建 RAG 模式的系统提示
**API7_input**: 
- kb_name: str - 知识库名称
- context: str - RAG 检索到的上下文
- role: Optional[str] - 可选的角色定义
**API7_output**: Dict[str, str] - 系统消息字典
**API7_sample**: 
```python
from advanced_system import create_rag_system_prompt

system_msg = create_rag_system_prompt(
    kb_name="技术知识库",
    context="这是检索到的相关内容...",
    role="你是技术知识库的专属助手"
)
```

### **API8_name**：create_chat_system_prompt
**API8_function**: 创建普通聊天模式的系统提示
**API8_input**: 无
**API8_output**: Dict[str, str] - 系统消息字典
**API8_sample**: 
```python
from advanced_system import create_chat_system_prompt

system_msg = create_chat_system_prompt()
```

---
# **文件14**：src/app/config.py
---

### **API1_name**：setup_network
**API1_function**: 智能网络配置，检测代理可用性并设置相应的网络配置
**API1_input**: 无
**API1_output**: null
**API1_sample**: 
```python
from app.config import setup_network

setup_network()
```

---
# **文件15**：src/app/schemas.py
---

### **API1_name**：FileActionRequest
**API1_function**: 文件操作请求的数据模型
**API1_input**: 
- filename: str - 文件名
- new_name: Optional[str] - 新文件名
- confirm_delete: bool - 是否确认删除
**API1_output**: Pydantic BaseModel 实例
**API1_sample**: 
```python
from app.schemas import FileActionRequest

request = FileActionRequest(
    filename="document.pdf",
    new_name="new_document.pdf",
    confirm_delete=True
)
```

### **API2_name**：SetGroupRequest
**API2_function**: 设置文件分组请求的数据模型
**API2_input**: 
- filename: str - 文件名
- group: str - 分组名称
**API2_output**: Pydantic BaseModel 实例
**API2_sample**: 
```python
from app.schemas import SetGroupRequest

request = SetGroupRequest(
    filename="document.pdf",
    group="技术文档"
)
```

### **API3_name**：HistoryActionRequest
**API3_function**: 历史记录操作请求的数据模型
**API3_input**: 
- filename: str - 文件名
- new_name: Optional[str] - 新文件名
**API3_output**: Pydantic BaseModel 实例
**API3_sample**: 
```python
from app.schemas import HistoryActionRequest

request = HistoryActionRequest(
    filename="2025-01-17/chat_123.json",
    new_name="new_chat.json"
)
```

### **API4_name**：LoadHistoryRequest
**API4_function**: 加载历史记录请求的数据模型
**API4_input**: 
- filepath: str - 文件路径
**API4_output**: Pydantic BaseModel 实例
**API4_sample**: 
```python
from app.schemas import LoadHistoryRequest

request = LoadHistoryRequest(filepath="2025-01-17/chat_123.json")
```

### **API5_name**：MessageContent
**API5_function**: 消息内容项（多模态）的数据模型
**API5_input**: 
- type: str - 类型（text 或 image_url）
- text: Optional[str] - 文本内容
- image_url: Optional[Dict[str, str]] - 图片 URL
**API5_output**: Pydantic BaseModel 实例
**API5_sample**: 
```python
from app.schemas import MessageContent

content = MessageContent(
    type="text",
    text="Hello"
)
```

### **API6_name**：ChatRequest
**API6_function**: 聊天请求的数据模型
**API6_input**: 
- api_url: str - API URL
- api_key: str - API Key
- model: str - 模型名称
- messages: List[Dict[str, Any]] - 消息列表
- session_file: Optional[str] - 会话文件
- kb_id: Optional[str] - 知识库ID
- stream: bool - 是否流式响应
- drawing_workspace_mode: bool - 是否绘图工作区模式
**API6_output**: Pydantic BaseModel 实例
**API6_sample**: 
```python
from app.schemas import ChatRequest

request = ChatRequest(
    api_url="https://api.openai.com/v1",
    api_key="sk-xxx",
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello"}],
    stream=False
)
```

### **API7_name**：ModelListRequest
**API7_function**: 模型列表请求的数据模型
**API7_input**: 
- api_url: str - API URL
- api_key: str - API Key
**API7_output**: Pydantic BaseModel 实例
**API7_sample**: 
```python
from app.schemas import ModelListRequest

request = ModelListRequest(
    api_url="https://api.openai.com/v1",
    api_key="sk-xxx"
)
```

### **API8_name**：CreateKBRequest
**API8_function**: 创建知识库请求的数据模型
**API8_input**: 
- name: str - 知识库名称
- description: str - 知识库描述
- files: List[str] - 文件列表
**API8_output**: Pydantic BaseModel 实例
**API8_sample**: 
```python
from app.schemas import CreateKBRequest

request = CreateKBRequest(
    name="技术知识库",
    description="包含技术文档",
    files=["doc1.pdf", "doc2.pdf"]
)
```

### **API9_name**：DeleteKBRequest
**API9_function**: 删除知识库请求的数据模型
**API9_input**: 
- kb_id: str - 知识库ID
**API9_output**: Pydantic BaseModel 实例
**API9_sample**: 
```python
from app.schemas import DeleteKBRequest

request = DeleteKBRequest(kb_id="abc12345")
```

### **API10_name**：UpdateKBRequest
**API10_function**: 更新知识库请求的数据模型
**API10_input**: 
- kb_id: str - 知识库ID
- name: str - 新名称
- description: str - 新描述
- files: Optional[List[str]] - 新文件列表
**API10_output**: Pydantic BaseModel 实例
**API10_sample**: 
```python
from app.schemas import UpdateKBRequest

request = UpdateKBRequest(
    kb_id="abc12345",
    name="新名称",
    description="新描述",
    files=["doc1.pdf"]
)
```
