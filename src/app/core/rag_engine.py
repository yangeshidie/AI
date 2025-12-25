# app/core/rag_engine.py
"""
RAG 引擎模块
负责文本向量化存储和检索
"""
import uuid
from typing import List, Optional

import chromadb
from chromadb.utils import embedding_functions

from app.config import CHROMA_PATH

# =============================================================================
# RAG 引擎初始化
# =============================================================================
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
_embedding_fn = None

def _get_embedding_function():
    """延迟加载 embedding function 以避免 uvicorn reload 模式下的多进程问题"""
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embedding_fn

_collection = None

def _get_collection():
    """延迟加载 collection 以避免 uvicorn reload 模式下的多进程问题"""
    global _collection
    if _collection is None:
        _collection = _chroma_client.get_or_create_collection(
            name="root_library",
            embedding_function=_get_embedding_function()
        )
    return _collection


def add_text_to_rag(filename: str, text: str, chunk_size: int = 500) -> int:
    """
    将文本分块后添加到 RAG 向量库

    Args:
        filename: 文件名，用于元数据标记
        text: 要添加的文本内容
        chunk_size: 分块大小

    Returns:
        添加的块数量
    """
    collection = _get_collection()
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if not chunks:
        return 0

    ids = [f"{filename}_{i}_{uuid.uuid4().hex[:4]}" for i in range(len(chunks))]
    metadatas = [{"source": filename} for _ in range(len(chunks))]

    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    return len(chunks)


def query_rag_with_filter(
    query: str,
    allowed_files: List[str],
    n_results: int = 3
) -> str:
    """
    在指定文件范围内查询 RAG

    Args:
        query: 查询文本
        allowed_files: 允许检索的文件列表
        n_results: 返回结果数量

    Returns:
        拼接的检索结果文本
    """
    if not allowed_files:
        return ""

    collection = _get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"source": {"$in": allowed_files}}
    )
    docs = results['documents'][0]
    return "\n---\n".join(docs) if docs else ""


def delete_from_rag(filename: str) -> None:
    """从 RAG 中删除指定文件的所有块"""
    collection = _get_collection()
    collection.delete(where={"source": filename})


def rename_in_rag(old_name: str, new_name: str) -> None:
    """在 RAG 中重命名文件的元数据"""
    collection = _get_collection()
    existing_records = collection.get(where={"source": old_name})
    if existing_records['ids']:
        ids_to_update = existing_records['ids']
        new_metadatas = [{"source": new_name} for _ in ids_to_update]
        collection.update(ids=ids_to_update, metadatas=new_metadatas)