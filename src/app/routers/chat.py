# app/routers/chat.py
"""
聊天相关 API 路由
"""
import logging
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import re
import json
import base64
import uuid
import time
import random

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from app.schemas import ChatRequest, ModelListRequest
from app.core.rag_engine import query_rag_with_filter
from app.core.kb_manager import kb_manager
from app.core.history import save_history, load_history_file
from app.core.api_adapter import MultimodalAdapter
from app.config import DEFAULT_API_URL, DEFAULT_API_KEY, DEFAULT_MODEL, STATIC_DIR, HISTORY_DIR
from advanced_system import create_rag_system_prompt, create_chat_system_prompt

router = APIRouter(prefix="/api", tags=["chat"])

logger = logging.getLogger(__name__)

# 初始化多模态适配器
adapter = MultimodalAdapter()


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


def save_history(messages: List[Dict[str, Any]], filename: str, kb_id: Optional[str] = None) -> None:
    """
    保存聊天历史到按日期组织的目录中

    Args:
        messages: 消息列表
        filename: 文件名或完整路径（如 "chat_123.json" 或 "2025-12-27/chat_123.json"）
        kb_id: 关联的知识库ID
    """
    from app.core.history import save_history as core_save_history
    
    # 将 kb_id 作为元数据保存到历史记录中
    history_data = {
        "messages": messages,
        "kb_id": kb_id
    }
    
    # 验证文件名不为空
    if not filename or not filename.strip():
        raise ValueError("文件名不能为空")
    
    # 如果 filename 包含日期目录，直接使用；否则创建新的日期目录
    if '/' in filename:
        file_path = HISTORY_DIR / filename
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        import datetime
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        save_dir = HISTORY_DIR / date_str
        save_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith('.json'):
            filename += '.json'

        file_path = save_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)


def load_history_file(filepath_str: str) -> Optional[Dict[str, Any]]:
    """
    加载指定的历史文件

    Args:
        filepath_str: 相对于 HISTORY_DIR 的文件路径

    Returns:
        包含 messages 和 kb_id 的字典，如果文件不存在则返回 None
    """
    file_path = HISTORY_DIR / filepath_str
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 兼容旧格式：如果直接是消息列表，则包装成新格式
    if isinstance(data, list):
        return {"messages": data, "kb_id": None}
    
    # 新格式：包含 messages 和 kb_id
    if isinstance(data, dict) and "messages" in data:
        return data
    
    return None



@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """处理聊天请求"""
    logger.info(f"收到聊天请求 - Model: {request.model}, API URL: {request.api_url}, Stream: {request.stream}, Drawing Workspace: {request.drawing_workspace_mode}")
    logger.debug(f"请求消息数量: {len(request.messages)}")
    logger.debug(f"请求消息ID: {[msg.get('id') for msg in request.messages]}")
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

        # 1. 先处理系统提示词
        current_messages = _prepare_messages_with_system_prompt(
            request.messages,
            request.kb_id,
            user_query
        )
        
        # 2. 再进行多模态上下文增强
        context_aware_messages = adapter.prepare_messages(current_messages, request.drawing_workspace_mode)
        logger.debug(f"准备发送的消息数量: {len(context_aware_messages)}")

        logger.info(f"调用模型 API - {request.model}, Stream: {request.stream}")
        
        if request.stream:
            return StreamingResponse(
                _stream_chat_response(client, request.model, context_aware_messages, request.messages, request.session_file, request.kb_id, request.drawing_workspace_mode),
                media_type="text/event-stream"
            )
        else:
            return await _non_stream_chat_response(client, request.model, context_aware_messages, request.messages, request.session_file, request.kb_id, request.drawing_workspace_mode)
            
    except Exception as e:
        logger.error(f"聊天请求处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_chat_response(client, model: str, messages: List[Dict[str, Any]], original_messages: List[Dict[str, Any]], session_file: str, kb_id: Optional[str] = None, drawing_workspace_mode: bool = False):
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
        
        processed_content = adapter.process_response(full_content)
        
        assistant_id = str(int(time.time() * 1000)) + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))
        
        logger.debug(f"原始消息数量: {len(original_messages)}")
        logger.debug(f"原始消息ID: {[msg.get('id') for msg in original_messages]}")
        
        if not drawing_workspace_mode:
            new_history = original_messages + [{"role": "assistant", "content": processed_content, "id": assistant_id}]
            save_history(new_history, session_file, kb_id)
            logger.info(f"历史记录已保存到: {session_file}")
        else:
            logger.info("绘图工作区模式：不保存历史记录")
        
        yield f"data: {json.dumps({'done': True, 'content': processed_content, 'id': assistant_id}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"流式响应处理失败: {e}", exc_info=True)
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


async def _non_stream_chat_response(client, model: str, messages: List[Dict[str, Any]], original_messages: List[Dict[str, Any]], session_file: str, kb_id: Optional[str] = None, drawing_workspace_mode: bool = False) -> Dict[str, str]:
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

        final_content = adapter.process_response(final_content)

        assistant_id = str(int(time.time() * 1000)) + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=9))
        
        if not drawing_workspace_mode:
            new_history = original_messages + [{"role": "assistant", "content": final_content, "id": assistant_id}]
            save_history(new_history, session_file, kb_id)
            logger.info(f"历史记录已保存到: {session_file}")
        else:
            logger.info("绘图工作区模式：不保存历史记录")

        logger.info("聊天请求处理完成，返回响应")
        return {"role": "assistant", "content": final_content, "id": assistant_id}

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
        history_data = load_history_file(session_file)
        if history_data is None:
            raise HTTPException(status_code=404, detail="会话文件不存在")
        
        messages = history_data.get('messages', [])
        kb_id = history_data.get('kb_id')
        
        # 查找并更新消息
        message_found = False
        for msg in messages:
            if msg.get('id') == message_id and msg.get('role') == role:
                message_found = True
                # 如果原内容是多模态格式（数组），保持多模态格式
                if isinstance(msg.get('content'), list):
                    # 保留图片等媒体，只更新文本部分
                    new_content = []
                    text_updated = False
                    for item in msg['content']:
                        if item.get('type') == 'text' and not text_updated:
                            new_content.append({'type': 'text', 'text': content})
                            text_updated = True
                        else:
                            new_content.append(item)
                    # 如果没有找到文本项，添加一个
                    if not text_updated:
                        new_content.append({'type': 'text', 'text': content})
                    msg['content'] = new_content
                else:
                    # 简单文本格式
                    msg['content'] = content
                logger.info(f"已更新 {role} 消息内容")
                break
        
        if not message_found:
            raise HTTPException(status_code=404, detail="未找到要编辑的消息")
        
        # 保存更新后的历史记录
        save_history(messages, session_file, kb_id)
        
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
        
        logger.info(f"会话文件路径: {session_file}")
        
        # 使用 HISTORY_DIR 而不是 STATIC_DIR / "chat_history"
        history_data = load_history_file(session_file)
        if history_data is None:
            logger.error(f"会话文件不存在: {HISTORY_DIR / session_file}")
            raise HTTPException(status_code=404, detail="会话文件不存在")
        
        messages = history_data.get('messages', [])
        kb_id = history_data.get('kb_id')
        
        logger.info(f"当前消息数量: {len(messages)}, kb_id: {kb_id}")
        
        # 查找并删除消息
        message_found = False
        new_messages = []
        deleted_content = None
        
        for msg in messages:
            if msg.get('id') == message_id and msg.get('role') == role:
                message_found = True
                deleted_content = msg.get('content', '')
                logger.info(f"已删除 {role} 消息")
                continue
            new_messages.append(msg)
        
        if not message_found:
            logger.error(f"未找到要删除的消息 - ID: {message_id}, Role: {role}")
            logger.error(f"当前所有消息ID: {[msg.get('id') for msg in messages]}")
            raise HTTPException(status_code=404, detail="未找到要删除的消息")
        
        # 如果删除的内容包含图片URL，尝试删除本地图片文件
        if deleted_content:
            content_to_check = ''
            if isinstance(deleted_content, str):
                content_to_check = deleted_content
            elif isinstance(deleted_content, list):
                # 从多模态内容中提取文本部分
                text_parts = [item.get('text', '') for item in deleted_content if item.get('type') == 'text']
                content_to_check = ' '.join(text_parts)
            
            image_pattern = r'!\[.*?\]\(/static/generated_images/([^\)]+)\)'
            image_matches = re.findall(image_pattern, content_to_check)
            
            for image_filename in image_matches:
                image_path = STATIC_DIR / "generated_images" / image_filename
                if image_path.exists():
                    try:
                        image_path.unlink()
                        logger.info(f"已删除本地图片: {image_path}")
                    except Exception as img_err:
                        logger.warning(f"删除图片文件失败: {img_err}")
        
        # 保存更新后的历史记录
        save_history(new_messages, session_file, kb_id)
        
        return {"success": True, "message": "消息删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))