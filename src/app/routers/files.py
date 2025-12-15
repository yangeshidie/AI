import os
import io
import datetime
import PyPDF2
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import UPLOAD_DIR
from app.schemas import FileActionRequest
from app.core.rag_engine import add_text_to_rag, delete_from_rag, rename_in_rag
from app.core.kb_manager import kb_manager
from app.core.file_manager import file_manager
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])


# 新增 Request Model
class SetGroupRequest(BaseModel):
    filename: str
    group: str

# 修改 list 接口
@router.get("/list")
async def list_uploaded_files():
    files = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            stats = f.stat()
            # 获取分组
            group = file_manager.get_group(f.name)
            files.append({
                "name": f.name,
                "size": f"{stats.st_size / 1024:.1f} KB",
                "date": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d"),
                "group": group # <--- 新增字段
            })
    return {"files": files}

# 新增设置分组接口
@router.post("/set_group")
async def set_file_group(req: SetGroupRequest):
    file_manager.set_group(req.filename, req.group)
    return {"status": "success"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        filename = file.filename
        file_location = UPLOAD_DIR / filename
        content = await file.read()

        with open(file_location, "wb") as f:
            f.write(content)

        text_content = ""
        if filename.lower().endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                t = page.extract_text()
                if t: text_content += t + "\n"
        else:
            text_content = content.decode("utf-8", errors='ignore')

        count = add_text_to_rag(filename, text_content)
        return {"status": "success", "filename": filename, "chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_file(req: FileActionRequest):
    file_path = UPLOAD_DIR / req.filename
    if not file_path.exists(): raise HTTPException(404, "文件不存在")

    used_by = kb_manager.find_kbs_using_file(req.filename)
    if used_by and not req.confirm_delete:
        return {"status": "warning", "message": "File is in use", "affected_kbs": used_by}

    try:
        delete_from_rag(req.filename)
        kb_manager.remove_file_from_all_kbs(req.filename)
        file_manager.delete_meta(req.filename)  # <--- 新增：清理分组信息

        os.remove(file_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/rename")
async def rename_file(req: FileActionRequest):
    if not req.new_name: raise HTTPException(400, "New name required")
    old_path = UPLOAD_DIR / req.filename
    new_path = UPLOAD_DIR / req.new_name

    if not old_path.exists(): raise HTTPException(404, "原文件不存在")
    if new_path.exists(): raise HTTPException(400, "新文件名已存在")

    try:
        os.rename(old_path, new_path)
        kb_manager.rename_file_in_kbs(req.filename, req.new_name)
        rename_in_rag(req.filename, req.new_name)

        file_manager.rename_meta(req.filename, req.new_name)  # <--- 新增：同步重命名分组信息

        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))