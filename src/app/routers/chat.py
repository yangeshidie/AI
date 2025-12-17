# app/routers/chat.py
"""
聊天相关 API 路由
"""
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from openai import OpenAI

from app.schemas import ChatRequest, ModelListRequest
from app.core.rag_engine import query_rag_with_filter
from app.core.kb_manager import kb_manager
from app.core.history import save_history
from app.config import DEFAULT_API_URL, DEFAULT_API_KEY, DEFAULT_MODEL
from advanced_system import create_rag_system_prompt, create_chat_system_prompt

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/config")
async def get_config() -> Dict[str, str]:
    """获取默认 API 配置"""
    return {
        "api_url": DEFAULT_API_URL,
        "api_key": DEFAULT_API_KEY,
        "model": DEFAULT_MODEL
    }


def _extract_last_user_query(messages: List[Dict[str, Any]]) -> str:
    """从消息列表中提取最后一条用户消息"""
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            return msg.get('content', '')
    return ''


def _prepare_messages_with_system_prompt(
    messages: List[Dict[str, Any]],
    kb_id: Optional[str],
    user_query: str
) -> List[Dict[str, Any]]:
    """
    根据是否有知识库绑定，准备包含系统提示的消息列表
    """
    current_messages = list(messages)

    if kb_id and user_query:
        kb_info = kb_manager.get_kb(kb_id)
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

    return current_messages


@router.post("/chat")
async def chat_endpoint(request: ChatRequest) -> Dict[str, str]:
    """处理聊天请求"""
    try:
        client = OpenAI(base_url=request.api_url, api_key=request.api_key)
        user_query = _extract_last_user_query(request.messages)

        current_messages = _prepare_messages_with_system_prompt(
            request.messages,
            request.kb_id,
            user_query
        )

        response = client.chat.completions.create(
            model=request.model,
            messages=current_messages
        )
        final_content = response.choices[0].message.content

        new_history = request.messages + [{"role": "assistant", "content": final_content}]
        save_history(new_history, request.session_file)

        return {"role": "assistant", "content": final_content}

    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def list_models(data: ModelListRequest) -> Dict[str, Any]:
    """获取可用模型列表"""
    try:
        client = OpenAI(base_url=data.api_url, api_key=data.api_key)
        models = client.models.list()
        return {"models": sorted([m.id for m in models.data])}
    except Exception as e:
        return {"error": str(e), "models": []}