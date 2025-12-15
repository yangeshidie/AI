from fastapi import APIRouter, HTTPException
from openai import OpenAI
from app.schemas import ChatRequest, ModelListRequest
from app.core.rag_engine import query_rag_with_filter
from app.core.kb_manager import kb_manager
from app.core.history import save_history
from app.config import DEFAULT_API_URL, DEFAULT_API_KEY, DEFAULT_MODEL
# 引入根目录的 advanced_system (假设它在 PYTHONPATH 中或已正确处理)
from advanced_system import create_rag_system_prompt, create_chat_system_prompt

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/config")
async def get_config():
    return {
        "api_url": DEFAULT_API_URL,
        "api_key": DEFAULT_API_KEY,
        "model": DEFAULT_MODEL
    }


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        client = OpenAI(base_url=request.api_url, api_key=request.api_key)
        user_query = next((m['content'] for m in reversed(request.messages) if m['role'] == 'user'), "")
        current_messages = list(request.messages)

        if request.kb_id and user_query:
            kb_info = kb_manager.get_kb(request.kb_id)
            if kb_info:
                print(f"🤖 激活 Agent: {kb_info['name']}")
                context = query_rag_with_filter(user_query, kb_info['files'])
                system_msg = create_rag_system_prompt(
                    kb_name=kb_info['name'],
                    context=context,
                    role=f"你是 {kb_info['name']}，{kb_info['description']}"
                )
                if current_messages and current_messages[0]['role'] == 'system':
                    current_messages[0] = system_msg
                else:
                    current_messages.insert(0, system_msg)
        else:
            if not current_messages or current_messages[0]['role'] != 'system':
                current_messages.insert(0, create_chat_system_prompt())

        response = client.chat.completions.create(
            model=request.model, messages=current_messages
        )
        final_content = response.choices[0].message.content

        new_history = request.messages + [{"role": "assistant", "content": final_content}]
        save_history(new_history, request.session_file)

        return {"role": "assistant", "content": final_content}

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def list_models(data: ModelListRequest):
    try:
        client = OpenAI(base_url=data.api_url, api_key=data.api_key)
        models = client.models.list()
        return {"models": sorted([m.id for m in models.data])}
    except Exception as e:
        return {"error": str(e), "models": []}