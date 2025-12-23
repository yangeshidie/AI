# app/routers/chat.py
"""
聊天相关 API 路由
"""
from typing import Dict, Any, List, Optional, Union

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
    """
    从消息列表中提取最后一条用户消息的文本内容
    支持处理纯文本字符串和多模态列表格式
    """
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # 提取列表中的文本部分
                text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
                return " ".join(text_parts)
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

        # 尝试解析 JSON 格式的非文本响应
        try:
            import json
            import base64
            import uuid
            from app.config import STATIC_DIR

            # 确保生成的图片目录存在
            generated_images_dir = STATIC_DIR / "generated_images"
            generated_images_dir.mkdir(exist_ok=True)

            if final_content.strip().startswith("{") and final_content.strip().endswith("}"):
                data = json.loads(final_content)
                
                # 处理 image 字段 (base64)
                image_data_b64 = None
                if "image" in data:
                    image_data_b64 = data["image"]
                elif "image_url" in data:
                    # 有些模型可能返回 image_url 字段带 base64
                    if data["image_url"].startswith("data:image"):
                        image_data_b64 = data["image_url"]
                    else:
                        # 如果是真实 URL，直接使用
                        final_content = f"![Generated Image]({data['image_url']})\n\n{data.get('text', '')}"

                if image_data_b64:
                    # 提取 base64 数据
                    if "base64," in image_data_b64:
                        header, encoded = image_data_b64.split("base64,", 1)
                        file_ext = "png"  # 默认
                        if "image/jpeg" in header: file_ext = "jpg"
                        elif "image/webp" in header: file_ext = "webp"
                    else:
                        encoded = image_data_b64
                        file_ext = "png"

                    # 保存到文件
                    img_filename = f"gen_{uuid.uuid4().hex}.{file_ext}"
                    img_path = generated_images_dir / img_filename
                    
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(encoded))
                    
                    # 生成本地 URL
                    local_url = f"/static/generated_images/{img_filename}"
                    print(f"🖼️ Image saved to {local_url}")

                    # 替换内容中的 base64 为 URL
                    final_content = f"![Generated Image]({local_url})\n\n{data.get('text', '')}"

        except Exception as e:
            print(f"Error parsing/saving image: {e}")
            pass # 解析失败则保留原始内容

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