"""
多模态 API 适配器
负责处理不同模型（OpenAI, Gemini, Claude）之间的多模态格式转换
确保图片上下文在多轮对话中保持一致
"""
import base64
import json
import logging
import re
import uuid
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from app.config import STATIC_DIR

logger = logging.getLogger(__name__)

class MultimodalAdapter:
    """
    多模态消息适配器
    处理图片上下文持久化和响应中的图片提取
    """
    
    def __init__(self, image_save_dir: Path = None):
        self.image_save_dir = image_save_dir or (STATIC_DIR / "generated_images")
        self.image_save_dir.mkdir(parents=True, exist_ok=True)

    def prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        准备发送给 API 的消息列表
        确保所有历史图片都被包含在上下文中
        """
        normalized_messages = []
        
        # 收集所有历史图片
        # 格式: {"url": "data:image/...", "detail": "auto"}
        history_images = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # 提取该消息中的所有图片
            current_msg_images = self._extract_images_from_content(content)
            history_images.extend(current_msg_images)
            
            # 构建新的消息体
            new_content = []
            
            # 1. 添加文本内容
            text_content = self._extract_text_from_content(content)
            if text_content:
                new_content.append({"type": "text", "text": text_content})
            
            # 2. 如果是当前最新的一条消息(用户发送的)，或者策略决定每条消息都带图片
            # 这里采用策略：
            # - 用户消息：保留该消息原本包含的图片
            # - 助手消息：保留该消息原本生成的图片
            # - 上下文增强：如果需要"强一致性"，可以在 System Prompt 后或者最新 User Message 前插入所有历史图片
            # 但为了避免 Token 爆炸，我们通常只保留"该消息原本的图片" + "最近 N 轮的图片"
            # 
            # 修正策略：
            # 为了达到"前后文一致性"，我们需要确保模型"看得到"之前的图片。
            # 大多数模型（如 GPT-4V, Gemini）是无状态的，必须在每次请求中包含图片。
            # 简单的做法是：保持消息原样，但确保格式是 OpenAI 兼容的 image_url 格式。
            # 如果之前的消息里已经有了 image_url (base64)，那么直接发过去就行。
            # 
            # 关键点：OpenAI SDK 会自动处理历史消息中的 image_url。
            # 我们只需要确保：
            # 1. 历史记录里的图片是 base64 格式的 image_url，而不是本地路径
            # 2. 如果历史记录里存的是本地路径，需要转换回 base64 发送给 API
            
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "image_url":
                        img_url = item["image_url"]["url"]
                        # 如果是本地路径引用，尝试读取并转换为 base64
                        if img_url.startswith("/static/") or img_url.startswith("http://localhost"):
                            base64_url = self._local_path_to_base64(img_url)
                            if base64_url:
                                item["image_url"]["url"] = base64_url
                new_content = content
            elif isinstance(content, str):
                # 检查文本中是否包含 markdown 图片链接，如果有，转换为 multimodal 格式
                # pattern = r'!\[(.*?)\]\((.*?)\)'
                # 暂时只处理纯文本，图片通常在前端已经处理成 list 格式上传
                new_content = content
            
            normalized_messages.append({
                "role": role,
                "content": new_content
            })
            
        return normalized_messages

    def process_response(self, response_content: str) -> str:
        """
        处理模型响应
        1. 识别 Base64 图片（Gemini 风格）
        2. 识别 image_url (OpenAI 风格)
        3. 保存图片到本地
        4. 替换为 Markdown 图片链接
        """
        # 1. 处理 JSON 格式的响应 (Gemini 经常返回 JSON)
        try:
            if response_content.strip().startswith("{") and response_content.strip().endswith("}"):
                data = json.loads(response_content)
                # 处理 image 字段 (Base64)
                if "image" in data:
                    return self._save_base64_image(data["image"], data.get("text", ""))
                # 处理 image_url 字段
                if "image_url" in data:
                    return self._save_base64_image(data["image_url"], data.get("text", ""))
        except json.JSONDecodeError:
            pass

        # 2. 处理 Markdown 中的 Base64 图片
        # 格式: ![alt](data:image/png;base64,...)
        pattern = r'!\[(.*?)\]\(data:image\/(.*?);base64,([^\)]+)\)'
        
        def replace_match(match):
            alt_text = match.group(1)
            ext = match.group(2)
            base64_str = match.group(3)
            
            # 修正扩展名
            if ext == "jpeg": ext = "jpg"
            
            filename = f"gen_{uuid.uuid4().hex}.{ext}"
            file_path = self.image_save_dir / filename
            
            try:
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(base64_str))
                
                local_url = f"/static/generated_images/{filename}"
                logger.info(f"已保存生成图片: {local_url}")
                return f"![{alt_text}]({local_url})"
            except Exception as e:
                logger.error(f"保存图片失败: {e}")
                return match.group(0)

        return re.sub(pattern, replace_match, response_content)

    def _save_base64_image(self, base64_data: str, text_content: str = "") -> str:
        """
        保存 Base64 图片数据到本地
        """
        try:
            # 处理 data:image/png;base64, 前缀
            if "," in base64_data:
                header, base64_str = base64_data.split(",", 1)
                # 尝试从 header 提取扩展名
                if "image/jpeg" in header:
                    ext = "jpg"
                elif "image/png" in header:
                    ext = "png"
                elif "image/webp" in header:
                    ext = "webp"
                else:
                    ext = "png"
            else:
                base64_str = base64_data
                ext = "png"

            filename = f"gen_{uuid.uuid4().hex}.{ext}"
            file_path = self.image_save_dir / filename

            with open(file_path, "wb") as f:
                f.write(base64.b64decode(base64_str))
            
            local_url = f"/static/generated_images/{filename}"
            logger.info(f"已保存生成图片: {local_url}")
            
            image_markdown = f"![Generated Image]({local_url})"
            if text_content:
                return f"{image_markdown}\n\n{text_content}"
            return image_markdown
            
        except Exception as e:
            logger.error(f"保存 Base64 图片失败: {e}")
            return text_content  # 如果保存失败，至少返回文本

    def _extract_text_from_content(self, content: Union[str, List]) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join([item["text"] for item in content if item.get("type") == "text"])
        return ""

    def _extract_images_from_content(self, content: Union[str, List]) -> List[str]:
        images = []
        if isinstance(content, list):
            for item in content:
                if item.get("type") == "image_url":
                    images.append(item["image_url"]["url"])
        return images

    def _local_path_to_base64(self, path_or_url: str) -> Optional[str]:
        """将本地路径或 URL 转换为 Base64 data URI"""
        try:
            # 移除 URL 前缀，获取相对路径
            # 假设 URL 格式为 /static/generated_images/xxx.png
            if "/static/" in path_or_url:
                rel_path = path_or_url.split("/static/")[1]
                full_path = STATIC_DIR / rel_path
            else:
                return None # 无法处理外部 URL

            if not full_path.exists():
                logger.warning(f"图片文件不存在: {full_path}")
                return None

            with open(full_path, "rb") as f:
                data = f.read()
                b64_data = base64.b64encode(data).decode('utf-8')
                
            # 推断 mime type
            ext = full_path.suffix.lower().replace(".", "")
            if ext == "jpg": ext = "jpeg"
            mime_type = f"image/{ext}"
            
            return f"data:{mime_type};base64,{b64_data}"
            
        except Exception as e:
            logger.error(f"转换图片为 Base64 失败: {e}")
            return None
