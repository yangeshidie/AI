from fastapi import APIRouter
from app.schemas import CreateKBRequest, DeleteKBRequest
from app.core.kb_manager import kb_manager

router = APIRouter(prefix="/api/kb", tags=["kb"])

@router.post("/create")
async def create_kb(req: CreateKBRequest):
    return kb_manager.create_kb(req.name, req.description, req.files)

@router.get("/list")
async def list_kbs():
    kbs = kb_manager.list_kbs()
    return {"kbs": list(kbs.values())}

@router.post("/delete")
async def delete_kb(req: DeleteKBRequest):
    kb_manager.delete_kb(req.kb_id)
    return {"status": "success"}