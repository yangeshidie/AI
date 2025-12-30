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
from io import BytesIO
from PIL import Image

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
        self.max_history_images = 2  # 最多保留最近的 N 张图片上下文

    def prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        准备发送给 API 的消息列表
        确保所有历史图片都被包含在上下文中，但进行数量限制和压缩优化
        """
        normalized_messages = []
        
        # 1. 预先扫描所有图片，确定哪些需要保留
        # 我们倒序遍历消息，收集最近的 N 张图片的 ID (或路径)
        images_to_keep = set()
        image_count = 0
        
        # Markdown 图片正则
        md_image_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
        
        for msg in reversed(messages):
            content = msg.get("content")
            
            # Case A: Multimodal List
            if isinstance(content, list):
                for item in reversed(content):
                    if item.get("type") == "image_url":
                        url = item["image_url"]["url"]
                        if image_count < self.max_history_images:
                            images_to_keep.add(url)
                            image_count += 1
                            
            # Case B: Markdown String
            elif isinstance(content, str):
                # 查找所有 markdown 图片链接
                matches = md_image_pattern.findall(content)
                # findall 返回 [(alt, url), ...]
                # 我们需要倒序处理，因为我们要保留"最近"的
                for _, url in reversed(matches):
                    if image_count < self.max_history_images:
                        images_to_keep.add(url)
                        image_count += 1
        
        logger.info(f"上下文优化: 保留最近 {len(images_to_keep)} 张图片 (上限: {self.max_history_images})")

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            # 构建新的消息体
            new_content = []
            
            # Case A: Multimodal List (Existing Logic)
            if isinstance(content, list):
                # 1. 添加文本内容
                text_content = self._extract_text_from_content(content)
                if text_content:
                    new_content.append({"type": "text", "text": text_content})
                
                # 2. 处理图片
                for item in content:
                    if item.get("type") == "image_url":
                        img_url = item["image_url"]["url"]
                        
                        if img_url in images_to_keep:
                            if img_url.startswith("/static/") or img_url.startswith("http://localhost"):
                                base64_url = self._local_path_to_base64(img_url, compress=True)
                                if base64_url:
                                    new_content.append({
                                        "type": "image_url",
                                        "image_url": {"url": base64_url}
                                    })
                                else:
                                    new_content.append(item)
                            else:
                                new_content.append(item)
                        else:
                            filename = Path(img_url).name
                            new_content.append({
                                "type": "text", 
                                "text": f"\n[System: Historical image {filename} omitted for brevity]\n"
                            })
            
            # Case B: Markdown String (New Logic)
            elif isinstance(content, str):
                # 我们需要将 Markdown 字符串拆分为 [Text, Image, Text, Image...]
                # 使用 split 可能会比较麻烦，我们用 finditer
                last_idx = 0
                for match in md_image_pattern.finditer(content):
                    start, end = match.span()
                    alt_text = match.group(1)
                    img_url = match.group(2)
                    
                    # 添加之前的文本
                    if start > last_idx:
                        text_segment = content[last_idx:start]
                        if text_segment.strip():
                            new_content.append({"type": "text", "text": text_segment})
                    
                    # 处理图片
                    if img_url in images_to_keep:
                        if img_url.startswith("/static/") or img_url.startswith("http://localhost"):
                            base64_url = self._local_path_to_base64(img_url, compress=True)
                            if base64_url:
                                new_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": base64_url}
                                })
                            else:
                                # 转换失败，保留原 Markdown
                                new_content.append({"type": "text", "text": match.group(0)})
                        else:
                            # 外部链接，尝试保留为 image_url (如果 API 支持) 或者保留原样
                            # 这里假设外部链接 API 能处理，或者我们无法处理
                            # 为安全起见，如果不是本地图片，我们保留原 Markdown
                            new_content.append({"type": "text", "text": match.group(0)})
                    else:
                        # 不保留，替换为占位符
                        filename = Path(img_url).name
                        new_content.append({
                            "type": "text", 
                            "text": f"\n[System: Historical image {filename} omitted for brevity]\n"
                        })
                    
                    last_idx = end
                
                # 添加剩余文本
                if last_idx < len(content):
                    text_segment = content[last_idx:]
                    if text_segment.strip():
                        new_content.append({"type": "text", "text": text_segment})
                
                # 如果没有找到任何图片，或者内容为空，确保至少有一个文本块
                if not new_content and content.strip():
                     new_content.append({"type": "text", "text": content})
            
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

    def _local_path_to_base64(self, path_or_url: str, compress: bool = True) -> Optional[str]:
        """
        将本地路径或 URL 转换为 Base64 data URI
        
        Args:
            path_or_url: 图片路径
            compress: 是否压缩图片 (Resize to max 1024px, JPEG quality 80)
        """
        try:
            # 移除 URL 前缀，获取相对路径
            if "/static/" in path_or_url:
                rel_path = path_or_url.split("/static/")[1]
                full_path = STATIC_DIR / rel_path
            else:
                return None 

            if not full_path.exists():
                logger.warning(f"图片文件不存在: {full_path}")
                return None

            # 使用 PIL 处理图片
            with Image.open(full_path) as img:
                # 转换为 RGB (防止 RGBA 转 JPEG 报错)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                if compress:
                    # 调整大小：最大边长 1024
                    max_size = 1024
                    if max(img.size) > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # 保存到内存缓冲区
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=80)
                data = buffer.getvalue()
                
                b64_data = base64.b64encode(data).decode('utf-8')
                return f"data:image/jpeg;base64,{b64_data}"
            
        except Exception as e:
            logger.error(f"转换图片为 Base64 失败: {e}")
            return None
            
        except Exception as e:
            logger.error(f"转换图片为 Base64 失败: {e}")
            return None
