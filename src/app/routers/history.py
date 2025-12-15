import os
from fastapi import APIRouter, HTTPException
from app.config import HISTORY_DIR
from app.schemas import HistoryActionRequest, LoadHistoryRequest
from app.core.history import get_all_history, load_history_file

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/list")
async def list_history():
    return get_all_history()


@router.post("/load")
async def load_history(req: LoadHistoryRequest):
    data = load_history_file(req.filepath)
    if data is None: raise HTTPException(404, "Not Found")
    return data


@router.post("/delete")
async def delete_history(req: HistoryActionRequest):
    try:
        parts = req.filename.split('/')
        if len(parts) == 2:
            target_path = HISTORY_DIR / parts[0] / parts[1]
        else:
            target_path = HISTORY_DIR / req.filename

        if target_path.exists():
            os.remove(target_path)
            # 清理空目录
            if target_path.parent != HISTORY_DIR and not any(target_path.parent.iterdir()):
                os.rmdir(target_path.parent)
            return {"status": "success"}
        else:
            raise HTTPException(404, "File not found")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/rename")
async def rename_history(req: HistoryActionRequest):
    try:
        parts = req.filename.split('/')
        if len(parts) != 2: raise HTTPException(400, "Invalid format")

        date_dir = parts[0]
        old_name = parts[1]
        new_name = req.new_name if req.new_name.endswith('.json') else req.new_name + '.json'

        old_path = HISTORY_DIR / date_dir / old_name
        new_path = HISTORY_DIR / date_dir / new_name

        if not old_path.exists(): raise HTTPException(404, "File not found")
        if new_path.exists(): raise HTTPException(400, "Name exists")

        os.rename(old_path, new_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))