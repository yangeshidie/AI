# app/routers/chat.py
"""
聊天相关 API 路由
"""
from typing import Dict, Any, List, Optional, Union
import re  # 新增: 用于正则匹配图片

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

        # ==========================================
        # 修改开始：使用正则和兼容逻辑处理 Base64 图片
        # ==========================================
        try:
            import json
            import base64
            import uuid
            from app.config import STATIC_DIR

            # 确保生成的图片目录存在
            generated_images_dir = STATIC_DIR / "generated_images"
            generated_images_dir.mkdir(exist_ok=True)

            # 1. 预处理：如果是纯 JSON 格式（为了兼容某些旧模型输出），先将其转换为 Markdown 文本格式
            # 这样后续就可以统一用正则来处理保存逻辑
            if final_content.strip().startswith("{") and final_content.strip().endswith("}"):
                try:
                    data = json.loads(final_content)
                    # 检查是否有 image 字段
                    if "image" in data:
                        image_data = data["image"]
                        # 如果没有 data:image 前缀，手动加上
                        if not image_data.startswith("data:image"):
                            image_data = f"data:image/png;base64,{image_data}"
                        # 构造 Markdown 格式
                        final_content = f"![Generated Image]({image_data})\n\n{data.get('text', '')}"
                    # 检查是否有 image_url 字段且包含 base64
                    elif "image_url" in data and data["image_url"].startswith("data:image"):
                        final_content = f"![Generated Image]({data['image_url']})\n\n{data.get('text', '')}"
                except json.JSONDecodeError:
                    pass  # 如果 JSON 解析失败，说明可能只是长得很像 JSON 的文本，继续往下走

            # 2. 定义正则回调函数：保存图片并替换链接
            def save_base64_image_match(match):
                alt_text = match.group(1)
                file_ext = match.group(2)  # png, jpeg, webp
                base64_str = match.group(3)

                # 修正文件扩展名
                if file_ext == "jpeg": file_ext = "jpg"

                # 生成唯一文件名
                img_filename = f"gen_{uuid.uuid4().hex}.{file_ext}"
                img_path = generated_images_dir / img_filename

                try:
                    # 解码并保存
                    with open(img_path, "wb") as f:
                        f.write(base64.b64decode(base64_str))

                    # 生成本地访问 URL
                    local_url = f"/static/generated_images/{img_filename}"
                    print(f"🖼️ Image saved to {local_url}")

                    # 返回替换后的 Markdown
                    return f"![{alt_text}]({local_url})"
                except Exception as save_err:
                    print(f"Error saving extracted image: {save_err}")
                    return match.group(0)  # 如果保存失败，返回原字符串

            # 3. 使用正则全局替换
            # 匹配模式: ![alt](data:image/ext;base64,DATA)
            # 能够匹配 Markdown 图片，无论它在文本的开头、中间还是结尾
            pattern = r'!\[(.*?)\]\(data:image\/(.*?);base64,([^\)]+)\)'

            final_content = re.sub(pattern, save_base64_image_match, final_content)

        except Exception as e:
            print(f"Error parsing/saving image logic: {e}")
            pass  # 解析失败则保留原始内容
        # ==========================================
        # 修改结束
        # ==========================================

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