# app/routers/chat.py
"""
聊天相关 API 路由
"""
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import re  # 新增: 用于正则匹配图片
import json
import base64
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from app.schemas import ChatRequest, ModelListRequest
from app.core.rag_engine import query_rag_with_filter
from app.core.kb_manager import kb_manager
from app.core.history import save_history, load_history_file
from app.config import DEFAULT_API_URL, DEFAULT_API_KEY, DEFAULT_MODEL, STATIC_DIR, HISTORY_DIR
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


def _process_image_content(content: str) -> str:
    """
    处理响应内容中的Base64图片，保存到本地并替换为本地URL
    """
    try:
        logger.info("开始处理图片内容")
        logger.debug(f"原始内容长度: {len(content)}")
        logger.debug(f"原始内容前200字符: {content[:200]}")
        
        generated_images_dir = STATIC_DIR / "generated_images"
        generated_images_dir.mkdir(exist_ok=True)
        logger.info(f"图片保存目录: {generated_images_dir}")

        if content.strip().startswith("{") and content.strip().endswith("}"):
            logger.info("检测到可能的 JSON 格式响应，尝试解析")
            try:
                data = json.loads(content)
                logger.info(f"解析后的 JSON 数据: {data}")
                if "image" in data:
                    image_data = data["image"]
                    logger.info(f"发现 image 字段，长度: {len(image_data)}")
                    if not image_data.startswith("data:image"):
                        image_data = f"data:image/png;base64,{image_data}"
                    content = f"![Generated Image]({image_data})\n\n{data.get('text', '')}"
                    logger.info("已转换为 Markdown 格式")
                elif "image_url" in data and data["image_url"].startswith("data:image"):
                    content = f"![Generated Image]({data['image_url']})\n\n{data.get('text', '')}"
                    logger.info("已从 image_url 转换为 Markdown 格式")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 解析失败: {e}")
                pass

        def save_base64_image_match(match):
            alt_text = match.group(1)
            file_ext = match.group(2)
            base64_str = match.group(3)

            logger.info(f"匹配到图片 - alt: {alt_text}, ext: {file_ext}, base64长度: {len(base64_str)}")

            if file_ext == "jpeg":
                file_ext = "jpg"

            img_filename = f"gen_{uuid.uuid4().hex}.{file_ext}"
            img_path = generated_images_dir / img_filename
            logger.info(f"准备保存图片到: {img_path}")

            try:
                decoded_data = base64.b64decode(base64_str)
                logger.info(f"Base64解码成功，数据长度: {len(decoded_data)}")
                
                with open(img_path, "wb") as f:
                    f.write(decoded_data)

                local_url = f"/static/generated_images/{img_filename}"
                logger.info(f"图片已保存到: {local_url}")

                return f"![{alt_text}]({local_url})"
            except Exception as save_err:
                logger.error(f"保存图片时出错: {save_err}", exc_info=True)
                return match.group(0)

        pattern = r'!\[(.*?)\]\(data:image\/(.*?);base64,([^\)]+)\)'

        matches = re.findall(pattern, content)
        logger.info(f"找到 {len(matches)} 个 base64 图片")

        content = re.sub(pattern, save_base64_image_match, content)
        logger.info("图片处理完成")

        return content

    except Exception as e:
        logger.error(f"处理图片时出错: {e}", exc_info=True)
        return content


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """处理聊天请求"""
    logger.info(f"收到聊天请求 - Model: {request.model}, API URL: {request.api_url}, Stream: {request.stream}")
    logger.debug(f"请求消息数量: {len(request.messages)}")
    logger.debug(f"KB ID: {request.kb_id}")
    
    try:
        logger.info("初始化 OpenAI 客户端")
        
        client = OpenAI(
            base_url=request.api_url, 
            api_key=request.api_key,
            max_retries=0,
            timeout=300.0  # 设置5分钟超时，适合长图片生成
        )
        
        user_query = _extract_last_user_query(request.messages)
        logger.debug(f"提取的用户查询: {user_query}")

        current_messages = _prepare_messages_with_system_prompt(
            request.messages,
            request.kb_id,
            user_query
        )
        logger.debug(f"准备发送的消息数量: {len(current_messages)}")

        logger.info(f"调用模型 API - {request.model}, Stream: {request.stream}")
        
        if request.stream:
            return StreamingResponse(
                _stream_chat_response(client, request.model, current_messages, request.messages, request.session_file),
                media_type="text/event-stream"
            )
        else:
            return await _non_stream_chat_response(client, request.model, current_messages, request.messages, request.session_file)
            
    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_response(client, model: str, messages: List[Dict[str, Any]], original_messages: List[Dict[str, Any]], session_file: str):
    """流式响应生成器"""
    full_content = ""
    
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    content = delta.content
                    full_content += content
                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        
        logger.info(f"流式响应完成，总内容长度: {len(full_content)}")
        
        processed_content = _process_image_content(full_content)
        
        new_history = original_messages + [{"role": "assistant", "content": processed_content}]
        save_history(new_history, session_file)
        logger.info(f"历史记录已保存到: {session_file}")
        
        yield f"data: {json.dumps({'done': True, 'content': processed_content}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"流式响应处理失败: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


async def _non_stream_chat_response(client, model: str, messages: List[Dict[str, Any]], original_messages: List[Dict[str, Any]], session_file: str) -> Dict[str, str]:
    """非流式响应处理"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
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
        
        error_keywords = ['BAKA', 'ERROR', 'RATE LIMIT', 'TOO MANY REQUESTS']
        if final_content and any(keyword in final_content.upper() for keyword in error_keywords):
            logger.warning(f"检测到 API 错误响应: {final_content}")
            raise HTTPException(status_code=500, detail=f"API 返回错误: {final_content}")

        final_content = _process_image_content(final_content)

        new_history = original_messages + [{"role": "assistant", "content": final_content}]
        save_history(new_history, session_file)
        logger.info(f"历史记录已保存到: {session_file}")

        logger.info("聊天请求处理完成，返回响应")
        return {"role": "assistant", "content": final_content}

    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models")
async def list_models(data: ModelListRequest) -> Dict[str, Any]:
    """获取可用模型列表"""
    try:
        client = OpenAI(
            base_url=data.api_url, 
            api_key=data.api_key,
            max_retries=0  # 禁用自动重试
        )
        models = client.models.list()
        return {"models": sorted([m.id for m in models.data])}
    except Exception as e:
        return {"error": str(e), "models": []}


@router.post("/edit_message")
async def edit_message(request: Dict[str, Any]) -> Dict[str, Any]:
    """编辑消息内容"""
    try:
        message_id = request.get('message_id')
        role = request.get('role')
        content = request.get('content')
        
        if not message_id or not role or content is None:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        logger.info(f"编辑消息 - ID: {message_id}, Role: {role}")
        
        # 读取当前会话历史
        session_file = request.get('session_file')
        if not session_file:
            raise HTTPException(status_code=400, detail="缺少 session_file 参数")
        
        # 使用 HISTORY_DIR 而不是 STATIC_DIR / "chat_history"
        history = load_history_file(session_file)
        if history is None:
            raise HTTPException(status_code=404, detail="会话文件不存在")
        
        # 查找并更新消息
        message_found = False
        for msg in history:
            if msg.get('role') == role:
                # 这里使用简单的匹配逻辑，实际应该使用更精确的消息ID
                # 由于前端生成的message_id是随机的，我们这里简化处理
                # 实际应用中应该维护一个消息ID到历史记录索引的映射
                message_found = True
                msg['content'] = content
                logger.info(f"已更新 {role} 消息内容")
                break
        
        if not message_found:
            raise HTTPException(status_code=404, detail="未找到要编辑的消息")
        
        # 保存更新后的历史记录
        save_history(history, session_file)
        
        return {"success": True, "message": "消息编辑成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"编辑消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete_message")
async def delete_message(request: Dict[str, Any]) -> Dict[str, Any]:
    """删除消息"""
    try:
        message_id = request.get('message_id')
        role = request.get('role')
        
        if not message_id or not role:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        logger.info(f"删除消息 - ID: {message_id}, Role: {role}")
        
        # 读取当前会话历史
        session_file = request.get('session_file')
        if not session_file:
            raise HTTPException(status_code=400, detail="缺少 session_file 参数")
        
        # 使用 HISTORY_DIR 而不是 STATIC_DIR / "chat_history"
        history = load_history_file(session_file)
        if history is None:
            raise HTTPException(status_code=404, detail="会话文件不存在")
        
        # 查找并删除消息
        message_found = False
        new_history = []
        deleted_content = None
        
        for msg in history:
            if msg.get('role') == role and not message_found:
                # 删除第一条匹配的消息
                message_found = True
                deleted_content = msg.get('content', '')
                logger.info(f"已删除 {role} 消息")
                continue
            new_history.append(msg)
        
        if not message_found:
            raise HTTPException(status_code=404, detail="未找到要删除的消息")
        
        # 如果删除的内容包含图片URL，尝试删除本地图片文件
        if deleted_content and isinstance(deleted_content, str):
            image_pattern = r'!\[.*?\]\(/static/generated_images/([^\)]+)\)'
            image_matches = re.findall(image_pattern, deleted_content)
            
            for image_filename in image_matches:
                image_path = STATIC_DIR / "generated_images" / image_filename
                if image_path.exists():
                    try:
                        image_path.unlink()
                        logger.info(f"已删除本地图片: {image_path}")
                    except Exception as img_err:
                        logger.warning(f"删除图片文件失败: {img_err}")
        
        # 保存更新后的历史记录
        save_history(new_history, session_file)
        
        return {"success": True, "message": "消息删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))