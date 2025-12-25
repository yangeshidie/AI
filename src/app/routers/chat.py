# app/routers/chat.py
"""
聊天相关 API 路由
"""
import logging
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

logger = logging.getLogger(__name__)


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
    logger.info(f"收到聊天请求 - Model: {request.model}, API URL: {request.api_url}")
    logger.debug(f"请求消息数量: {len(request.messages)}")
    logger.debug(f"KB ID: {request.kb_id}")
    
    try:
        logger.info("初始化 OpenAI 客户端")
        client = OpenAI(base_url=request.api_url, api_key=request.api_key)
        user_query = _extract_last_user_query(request.messages)
        logger.debug(f"提取的用户查询: {user_query}")

        current_messages = _prepare_messages_with_system_prompt(
            request.messages,
            request.kb_id,
            user_query
        )
        logger.debug(f"准备发送的消息数量: {len(current_messages)}")

        logger.info(f"调用模型 API - {request.model}")
        response = client.chat.completions.create(
            model=request.model,
            messages=current_messages
        )
        
        logger.info(f"收到 API 响应")
        logger.debug(f"响应对象类型: {type(response)}")
        logger.debug(f"响应 choices 数量: {len(response.choices) if hasattr(response, 'choices') else 'N/A'}")
        
        if hasattr(response, 'choices') and len(response.choices) > 0:
            logger.debug(f"第一个 choice 类型: {type(response.choices[0])}")
            if hasattr(response.choices[0], 'message'):
                logger.debug(f"message 类型: {type(response.choices[0].message)}")
                if hasattr(response.choices[0].message, 'content'):
                    final_content = response.choices[0].message.content
                    logger.info(f"响应内容长度: {len(final_content) if final_content else 0}")
                    logger.debug(f"响应内容预览: {final_content[:200] if final_content else 'None'}...")
                else:
                    logger.error("message 对象没有 content 属性")
                    raise HTTPException(status_code=500, detail="API 响应格式错误: message 缺少 content 属性")
            else:
                logger.error("choice 对象没有 message 属性")
                raise HTTPException(status_code=500, detail="API 响应格式错误: choice 缺少 message 属性")
        else:
            logger.error("响应对象缺少 choices 属性或 choices 为空")
            raise HTTPException(status_code=500, detail="API 响应格式错误: 缺少 choices")
        
        logger.info(f"原始响应内容: {final_content[:500] if final_content else 'None'}...")
        
        # 检测 API 返回的错误响应
        error_keywords = ['BAKA', 'ERROR', 'RATE LIMIT', 'TOO MANY REQUESTS']
        if final_content and any(keyword in final_content.upper() for keyword in error_keywords):
            logger.warning(f"检测到 API 错误响应: {final_content}")
            raise HTTPException(status_code=500, detail=f"API 返回错误: {final_content}")

        # ==========================================
        # 修改开始：使用正则和兼容逻辑处理 Base64 图片
        # ==========================================
        try:
            import json
            import base64
            import uuid
            from app.config import STATIC_DIR

            logger.debug("开始处理图片内容")
            # 确保生成的图片目录存在
            generated_images_dir = STATIC_DIR / "generated_images"
            generated_images_dir.mkdir(exist_ok=True)

            # 1. 预处理：如果是纯 JSON 格式（为了兼容某些旧模型输出），先将其转换为 Markdown 文本格式
            # 这样后续就可以统一用正则来处理保存逻辑
            if final_content.strip().startswith("{") and final_content.strip().endswith("}"):
                logger.debug("检测到可能的 JSON 格式响应，尝试解析")
                try:
                    data = json.loads(final_content)
                    logger.debug(f"解析后的 JSON 数据: {data}")
                    # 检查是否有 image 字段
                    if "image" in data:
                        image_data = data["image"]
                        logger.debug(f"发现 image 字段，长度: {len(image_data)}")
                        # 如果没有 data:image 前缀，手动加上
                        if not image_data.startswith("data:image"):
                            image_data = f"data:image/png;base64,{image_data}"
                        # 构造 Markdown 格式
                        final_content = f"![Generated Image]({image_data})\n\n{data.get('text', '')}"
                        logger.debug("已转换为 Markdown 格式")
                    # 检查是否有 image_url 字段且包含 base64
                    elif "image_url" in data and data["image_url"].startswith("data:image"):
                        final_content = f"![Generated Image]({data['image_url']})\n\n{data.get('text', '')}"
                        logger.debug("已从 image_url 转换为 Markdown 格式")
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 解析失败: {e}")
                    pass  # 如果 JSON 解析失败，说明可能只是长得很像 JSON 的文本，继续往下走

            # 2. 定义正则回调函数：保存图片并替换链接
            def save_base64_image_match(match):
                alt_text = match.group(1)
                file_ext = match.group(2)  # png, jpeg, webp
                base64_str = match.group(3)

                logger.debug(f"匹配到图片 - alt: {alt_text}, ext: {file_ext}, base64长度: {len(base64_str)}")

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
                    logger.info(f"图片已保存到: {local_url}")

                    # 返回替换后的 Markdown
                    return f"![{alt_text}]({local_url})"
                except Exception as save_err:
                    logger.error(f"保存图片时出错: {save_err}")
                    return match.group(0)  # 如果保存失败，返回原字符串

            # 3. 使用正则全局替换
            # 匹配模式: ![alt](data:image/ext;base64,DATA)
            # 能够匹配 Markdown 图片，无论它在文本的开头、中间还是结尾
            pattern = r'!\[(.*?)\]\(data:image\/(.*?);base64,([^\)]+)\)'

            matches = re.findall(pattern, final_content)
            logger.debug(f"找到 {len(matches)} 个 base64 图片")

            final_content = re.sub(pattern, save_base64_image_match, final_content)
            logger.debug("图片处理完成")

        except Exception as e:
            logger.error(f"处理图片时出错: {e}", exc_info=True)
            pass  # 解析失败则保留原始内容
        # ==========================================
        # 修改结束
        # ==========================================

        new_history = request.messages + [{"role": "assistant", "content": final_content}]
        save_history(new_history, request.session_file)
        logger.info(f"历史记录已保存到: {request.session_file}")

        logger.info("聊天请求处理完成，返回响应")
        return {"role": "assistant", "content": final_content}

    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}", exc_info=True)
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