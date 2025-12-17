# app/core/kb_manager.py
"""
知识库管理器
负责知识库的创建、查询、删除以及文件关联管理
"""
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.config import KB_META_FILE


class KBManager:
    """
    知识库元数据管理类，使用 JSON 文件存储知识库信息
    """

    def __init__(self) -> None:
        self.file_path: Path = KB_META_FILE
        if not self.file_path.exists():
            self._save({})

    def _load(self) -> Dict[str, Any]:
        """加载知识库元数据"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]) -> None:
        """保存知识库元数据"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def create_kb(self, name: str, description: str, files: List[str]) -> Dict[str, Any]:
        """
        创建新的知识库

        Args:
            name: 知识库名称
            description: 知识库描述
            files: 关联的文件列表

        Returns:
            创建的知识库信息
        """
        data = self._load()
        kb_id = str(uuid.uuid4())[:8]
        data[kb_id] = {
            "id": kb_id,
            "name": name,
            "description": description,
            "files": files,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._save(data)
        return data[kb_id]

    def list_kbs(self) -> Dict[str, Any]:
        """列出所有知识库"""
        return self._load()

    def get_kb(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取知识库信息"""
        return self._load().get(kb_id)

    def delete_kb(self, kb_id: str) -> None:
        """删除指定的知识库"""
        data = self._load()
        if kb_id in data:
            del data[kb_id]
            self._save(data)

    def find_kbs_using_file(self, filename: str) -> List[str]:
        """
        查找使用特定文件的所有知识库

        Args:
            filename: 文件名

        Returns:
            使用该文件的知识库名称列表
        """
        data = self._load()
        affected_kbs: List[str] = []
        for kb_id, kb_data in data.items():
            if filename in kb_data.get("files", []):
                affected_kbs.append(kb_data["name"])
        return affected_kbs

    def remove_file_from_all_kbs(self, filename: str) -> None:
        """从所有知识库中移除指定文件"""
        data = self._load()
        for kb_id, kb_data in data.items():
            if filename in kb_data.get("files", []):
                kb_data["files"].remove(filename)
        self._save(data)

    def rename_file_in_kbs(self, old_name: str, new_name: str) -> None:
        """在所有知识库中重命名文件"""
        data = self._load()
        for kb_id, kb_data in data.items():
            files = kb_data.get("files", [])
            if old_name in files:
                kb_data["files"] = [new_name if f == old_name else f for f in files]
        self._save(data)


# 模块级单例实例
kb_manager = KBManager()