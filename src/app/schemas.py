# app/schemas.py
"""
Pydantic 数据模型定义
包含所有 API 请求/响应模型
"""
from typing import List, Optional

from pydantic import BaseModel


# =============================================================================
# 文件相关模型
# =============================================================================

class FileActionRequest(BaseModel):
    """文件操作请求"""
    filename: str
    new_name: Optional[str] = None
    confirm_delete: bool = False


class SetGroupRequest(BaseModel):
    """设置文件分组请求"""
    filename: str
    group: str


# =============================================================================
# 历史记录相关模型
# =============================================================================

class HistoryActionRequest(BaseModel):
    """历史记录操作请求"""
    filename: str
    new_name: Optional[str] = None


class LoadHistoryRequest(BaseModel):
    """加载历史记录请求"""
    filepath: str


# =============================================================================
# 聊天相关模型
# =============================================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    api_url: str
    api_key: str
    model: str
    messages: list
    session_file: str
    kb_id: Optional[str] = None


class ModelListRequest(BaseModel):
    """模型列表请求"""
    api_url: str
    api_key: str


# =============================================================================
# 知识库相关模型
# =============================================================================

class CreateKBRequest(BaseModel):
    """创建知识库请求"""
    name: str
    description: str
    files: List[str]


class DeleteKBRequest(BaseModel):
    """删除知识库请求"""
    kb_id: str