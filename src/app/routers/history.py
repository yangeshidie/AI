# app/routers/history.py
"""
聊天历史相关 API 路由
"""
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from fastapi import APIRouter, HTTPException

from app.config import HISTORY_DIR
from app.schemas import HistoryActionRequest, LoadHistoryRequest
from app.core.history import get_all_history, load_history_file

router = APIRouter(prefix="/api/history", tags=["history"])


def _parse_history_path(filename: str) -> Tuple[Optional[str], str]:
    """
    解析历史文件路径

    Args:
        filename: 文件路径字符串，可能是 "date/file.json" 或 "file.json" 格式

    Returns:
        (日期目录, 文件名) 元组
    """
    parts = filename.split('/')
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, filename


@router.get("/list")
async def list_history() -> Dict[str, List[str]]:
    """列出所有历史记录"""
    return get_all_history()


@router.post("/load")
async def load_history(req: LoadHistoryRequest) -> List[Dict[str, Any]]:
    """加载指定的历史记录"""
    data = load_history_file(req.filepath)
    if data is None:
        raise HTTPException(status_code=404, detail="Not Found")
    return data


@router.post("/delete")
async def delete_history(req: HistoryActionRequest) -> Dict[str, str]:
    """删除历史记录"""
    try:
        date_dir, file_name = _parse_history_path(req.filename)
        if date_dir:
            target_path = HISTORY_DIR / date_dir / file_name
        else:
            target_path = HISTORY_DIR / req.filename

        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        os.remove(target_path)

        # 清理空目录
        if target_path.parent != HISTORY_DIR and not any(target_path.parent.iterdir()):
            os.rmdir(target_path.parent)

        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
async def rename_history(req: HistoryActionRequest) -> Dict[str, str]:
    """重命名历史记录"""
    try:
        date_dir, old_name = _parse_history_path(req.filename)
        if date_dir is None:
            raise HTTPException(status_code=400, detail="Invalid format")

        new_name = req.new_name
        if not new_name.endswith('.json'):
            new_name += '.json'

        old_path = HISTORY_DIR / date_dir / old_name
        new_path = HISTORY_DIR / date_dir / new_name

        if not old_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        if new_path.exists():
            raise HTTPException(status_code=400, detail="Name exists")

        os.rename(old_path, new_path)
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))