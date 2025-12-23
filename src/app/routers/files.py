# app/routers/files.py
"""
文件管理相关 API 路由
"""
import os
import io
import datetime
from typing import Dict, Any, List

import PyPDF2
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR
from app.schemas import FileActionRequest, SetGroupRequest
from app.core.rag_engine import add_text_to_rag, delete_from_rag, rename_in_rag
from app.core.kb_manager import kb_manager
from app.core.file_manager import file_manager

router = APIRouter(prefix="/api/files", tags=["files"])


def _extract_text_from_file(filename: str, content: bytes) -> str:
    """
    从文件中提取文本内容

    Args:
        filename: 文件名
        content: 文件二进制内容

    Returns:
        提取的文本内容
    """
    if filename.lower().endswith(".pdf"):
        text_content = ""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        return text_content
    else:
        return content.decode("utf-8", errors='ignore')


@router.get("/list")
async def list_uploaded_files() -> Dict[str, List[Dict[str, Any]]]:
    """列出所有上传的文件"""
    files: List[Dict[str, Any]] = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            stats = f.stat()
            group = file_manager.get_group(f.name)
            files.append({
                "name": f.name,
                "size": f"{stats.st_size / 1024:.1f} KB",
                "date": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d"),
                "group": group
            })
    return {"files": files}


@router.post("/set_group")
async def set_file_group(req: SetGroupRequest) -> Dict[str, str]:
    """设置文件分组"""
    file_manager.set_group(req.filename, req.group)
    return {"status": "success"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上传文件并添加到 RAG"""
    try:
        filename = file.filename
        file_location = UPLOAD_DIR / filename
        content = await file.read()

        with open(file_location, "wb") as f:
            f.write(content)

        text_content = _extract_text_from_file(filename, content)
        count = add_text_to_rag(filename, text_content)

        return {"status": "success", "filename": filename, "chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_file(req: FileActionRequest) -> Dict[str, Any]:
    """删除文件"""
    file_path = UPLOAD_DIR / req.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查文件是否被知识库使用
    used_by = kb_manager.find_kbs_using_file(req.filename)
    if used_by and not req.confirm_delete:
        return {
            "status": "warning",
            "message": "File is in use",
            "affected_kbs": used_by
        }

    try:
        delete_from_rag(req.filename)
        kb_manager.remove_file_from_all_kbs(req.filename)
        file_manager.delete_meta(req.filename)
        os.remove(file_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
async def rename_file(req: FileActionRequest) -> Dict[str, str]:
    """重命名文件"""
    if not req.new_name:
        raise HTTPException(status_code=400, detail="New name required")

    old_path = UPLOAD_DIR / req.filename
    new_path = UPLOAD_DIR / req.new_name
# app/routers/files.py
"""
文件管理相关 API 路由
"""
import os
import io
import datetime
from typing import Dict, Any, List

import PyPDF2
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR
from app.schemas import FileActionRequest, SetGroupRequest
from app.core.rag_engine import add_text_to_rag, delete_from_rag, rename_in_rag
from app.core.kb_manager import kb_manager
from app.core.file_manager import file_manager

router = APIRouter(prefix="/api/files", tags=["files"])


def _extract_text_from_file(filename: str, content: bytes) -> str:
    """
    从文件中提取文本内容

    Args:
        filename: 文件名
        content: 文件二进制内容

    Returns:
        提取的文本内容
    """
    if filename.lower().endswith(".pdf"):
        text_content = ""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content += page_text + "\n"
        return text_content
    else:
        return content.decode("utf-8", errors='ignore')


@router.get("/list")
async def list_uploaded_files() -> Dict[str, List[Dict[str, Any]]]:
    """列出所有上传的文件"""
    files: List[Dict[str, Any]] = []
    for f in UPLOAD_DIR.iterdir():
        if f.is_file():
            stats = f.stat()
            group = file_manager.get_group(f.name)
            files.append({
                "name": f.name,
                "size": f"{stats.st_size / 1024:.1f} KB",
                "date": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d"),
                "group": group
            })
    return {"files": files}


@router.post("/set_group")
async def set_file_group(req: SetGroupRequest) -> Dict[str, str]:
    """设置文件分组"""
    file_manager.set_group(req.filename, req.group)
    return {"status": "success"}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上传文件并添加到 RAG"""
    try:
        filename = file.filename
        file_location = UPLOAD_DIR / filename
        content = await file.read()

        with open(file_location, "wb") as f:
            f.write(content)

        text_content = _extract_text_from_file(filename, content)
        count = add_text_to_rag(filename, text_content)

        return {"status": "success", "filename": filename, "chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_file(req: FileActionRequest) -> Dict[str, Any]:
    """删除文件"""
    file_path = UPLOAD_DIR / req.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 检查文件是否被知识库使用
    used_by = kb_manager.find_kbs_using_file(req.filename)
    if used_by and not req.confirm_delete:
        return {
            "status": "warning",
            "message": "File is in use",
            "affected_kbs": used_by
        }

    try:
        delete_from_rag(req.filename)
        kb_manager.remove_file_from_all_kbs(req.filename)
        file_manager.delete_meta(req.filename)
        os.remove(file_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rename")
async def rename_file(req: FileActionRequest) -> Dict[str, str]:
    """重命名文件"""
    if not req.new_name:
        raise HTTPException(status_code=400, detail="New name required")

    old_path = UPLOAD_DIR / req.filename
    new_path = UPLOAD_DIR / req.new_name

    if not old_path.exists():
        raise HTTPException(status_code=404, detail="原文件不存在")
    if new_path.exists():
        raise HTTPException(status_code=400, detail="新文件名已存在")

    try:
        os.rename(old_path, new_path)
        kb_manager.rename_file_in_kbs(req.filename, req.new_name)
        rename_in_rag(req.filename, req.new_name)
        file_manager.rename_meta(req.filename, req.new_name)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract_text")
async def extract_text_from_upload(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    接收上传的文件（PDF/MD/TXT），提取文本内容并返回
    不保存文件到磁盘
    """
    try:
        content = await file.read()
        filename = file.filename
        text = _extract_text_from_file(filename, content)
        return {"filename": filename, "text": text}
    except Exception as e:
        print(f"Error extracting text: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")