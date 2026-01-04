# app/routers/kb.py
"""
知识库相关 API 路由
"""
from typing import Dict, List, Any

from fastapi import APIRouter

from app.schemas import CreateKBRequest, DeleteKBRequest, UpdateKBRequest
from app.core.kb_manager import kb_manager

router = APIRouter(prefix="/api/kb", tags=["kb"])


@router.post("/create")
async def create_kb(req: CreateKBRequest) -> Dict[str, Any]:
    """创建新知识库"""
    return kb_manager.create_kb(req.name, req.description, req.files)


@router.get("/list")
async def list_kbs() -> Dict[str, List[Dict[str, Any]]]:
    """列出所有知识库"""
    kbs = kb_manager.list_kbs()
    return {"kbs": list(kbs.values())}


@router.post("/delete")
async def delete_kb(req: DeleteKBRequest) -> Dict[str, str]:
    """删除知识库"""
    kb_manager.delete_kb(req.kb_id)
    return {"status": "success"}


@router.post("/update")
async def update_kb(req: UpdateKBRequest) -> Dict[str, Any]:
    """更新知识库"""
    result = kb_manager.update_kb(req.kb_id, req.name, req.description)
    if result is None:
        return {"status": "error", "message": "知识库不存在"}
    return {"status": "success", "kb": result}