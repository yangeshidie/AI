import os
import json
import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

# --- RAG 依赖 ---
import chromadb
from chromadb.utils import embedding_functions
import PyPDF2
import io

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

HISTORY_DIR = Path("history")
CHROMA_PATH = "chroma_db"

# ==========================================
# 核心模块: RAG 向量数据库引擎 (保持不变)
# ==========================================

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# 使用轻量级开源 Embedding 模型
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = chroma_client.get_or_create_collection(
    name="local_knowledge",
    embedding_function=emb_fn
)


def add_text_to_rag(filename: str, text: str):
    """将文本切片并存入向量数据库"""
    chunk_size = 500
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if not chunks: return 0

    ids = [f"{filename}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": filename} for _ in range(len(chunks))]

    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    return len(chunks)


def query_rag_db(query: str, n_results: int = 3):
    """检索最相似的文本，返回字符串，如果距离太远可以返回空"""
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        docs = results['documents'][0]
        # 这里可以直接返回，LLM 会判断是否有用
        return "\n---\n".join(docs) if docs else ""
    except Exception as e:
        print(f"RAG Search Error: {e}")
        return ""


# ==========================================
# 数据模型与 API 接口
# ==========================================

class ChatRequest(BaseModel):
    api_url: str
    api_key: str
    model: str
    messages: list
    session_file: str


class LoadHistoryRequest(BaseModel):
    filepath: str


# --- 基础页面 ---
@app.get("/")
async def read_index():
    return FileResponse('static/index.html')


@app.get("/api/config")
async def get_config():
    return {
        "api_url": os.getenv("PROXY_BASE_URL", "https://api.openai.com/v1"),
        "api_key": os.getenv("PROXY_API_KEY", ""),
        "model": os.getenv("TARGET_MODEL", "gpt-3.5-turbo")
    }


# --- 知识库上传接口 ---
@app.post("/api/rag/upload")
async def upload_to_rag(file: UploadFile = File(...)):
    try:
        filename = file.filename
        content = await file.read()
        text_content = ""

        if filename.lower().endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                t = page.extract_text()
                if t: text_content += t + "\n"
        else:
            text_content = content.decode("utf-8", errors='ignore')

        count = add_text_to_rag(filename, text_content)
        return {"status": "success", "chunks_added": count, "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- 聊天主接口 (重构为经典的 Context Injection RAG) ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        client = OpenAI(base_url=request.api_url, api_key=request.api_key)

        # 1. 获取用户最新的问题
        user_query = ""
        for msg in reversed(request.messages):
            if msg['role'] == 'user':
                user_query = msg['content']
                break

        current_messages = list(request.messages)

        # 2. 【核心修改】直接搜索本地知识库 (不经过 LLM 思考)
        # 只要用户发了消息，我们就去数据库捞一下看有没有相关的
        if user_query:
            print(f"🔍 正在检索知识库: {user_query}")
            context_data = query_rag_db(user_query)

            if context_data:
                print(f"✅ 找到相关背景知识，正在注入 Prompt...")
                # 构造一个系统提示词，插入到用户问题之前
                # 告诉 LLM：这是背景资料，请参考它
                rag_system_prompt = {
                    "role": "system",
                    "content": f"【参考资料（请优先基于此资料回答）】\n{context_data}\n\n【用户问题】如下："
                }
                # 将参考资料插入到倒数第二个位置（即最新用户提问之前）
                # 这样可以保证上下文连贯性
                current_messages.insert(-1, rag_system_prompt)

        # 3. 发送给 LLM (普通对话模式，无 Tool)
        response = client.chat.completions.create(
            model=request.model,
            messages=current_messages
        )

        final_content = response.choices[0].message.content

        # 4. 保存历史
        # 注意：保存历史时，我们不保存那个临时的“参考资料”system prompt，
        # 否则历史记录会变得非常臃肿。只保存用户问题和 AI 回答。
        new_history = request.messages + [{"role": "assistant", "content": final_content}]
        save_history_to_file(new_history, request.session_file)

        return {"role": "assistant", "content": final_content}

    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 辅助函数：保存/加载历史 ---
def save_history_to_file(messages, filename):
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    save_dir = HISTORY_DIR / date_str
    save_dir.mkdir(parents=True, exist_ok=True)
    if not filename.endswith('.json'): filename += '.json'
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


@app.get("/api/history/list")
async def list_history():
    if not HISTORY_DIR.exists(): return {}
    result = {}
    for date_dir in sorted(HISTORY_DIR.iterdir(), reverse=True):
        if date_dir.is_dir():
            files = [f.name for f in sorted(date_dir.glob("*.json"), key=os.path.getmtime, reverse=True)]
            if files: result[date_dir.name] = files
    return result


@app.post("/api/history/load")
async def load_history(req: LoadHistoryRequest):
    file_path = HISTORY_DIR / req.filepath
    if not file_path.exists(): raise HTTPException(status_code=404, detail="Not Found")
    with open(file_path, "r", encoding="utf-8") as f: return json.load(f)


@app.post("/api/models")
async def list_models(data: dict):
    try:
        client = OpenAI(base_url=data['api_url'], api_key=data['api_key'])
        models = client.models.list()
        return {"models": sorted([m.id for m in models.data])}
    except Exception as e:
        return {"error": str(e), "models": []}


if __name__ == "__main__":
    import uvicorn

    print("🚀 极简版本地 RAG 启动中...")
    uvicorn.run(app, host="127.0.0.1", port=8000)