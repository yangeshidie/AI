# app/core/file_manager.py
"""
文件元数据管理器
负责管理上传文件的分组等元信息
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from app.config import BASE_DIR

FILE_META_PATH: Path = BASE_DIR / "file_metadata.json"


class FileManager:
    """
    文件元数据管理类，使用 JSON 文件存储文件的分组等信息
    """

    def __init__(self) -> None:
        self.path: Path = FILE_META_PATH
        if not self.path.exists():
            self._save({})

    def _load(self) -> Dict[str, Any]:
        """加载元数据文件"""
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]) -> None:
        """保存元数据文件"""
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_group(self, filename: str, group: str) -> None:
        """设置文件的分组"""
        data = self._load()
        if filename not in data:
            data[filename] = {}
        data[filename]["group"] = group
        self._save(data)

    def get_group(self, filename: str) -> str:
        """获取文件的分组，默认为 '未分组'"""
        data = self._load()
        return data.get(filename, {}).get("group", "未分组")

    def get_all_groups(self) -> List[str]:
        """获取所有已使用的分组名称"""
        data = self._load()
        groups: Set[str] = set()
        for meta in data.values():
            if "group" in meta:
                groups.add(meta["group"])
        return list(groups)

    def delete_meta(self, filename: str) -> None:
        """删除文件的元数据"""
        data = self._load()
        if filename in data:
            del data[filename]
            self._save(data)

    def rename_meta(self, old_name: str, new_name: str) -> None:
        """重命名文件时同步更新元数据"""
        data = self._load()
        if old_name in data:
            data[new_name] = data[old_name]
            del data[old_name]
            self._save(data)


# 模块级单例实例
file_manager: FileManager = FileManager()