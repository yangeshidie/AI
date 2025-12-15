# app/core/file_manager.py
import json
from pathlib import Path
from app.config import BASE_DIR

FILE_META_PATH = BASE_DIR / "file_metadata.json"


class FileManager:
    def __init__(self):
        self.path = FILE_META_PATH
        if not self.path.exists():
            self._save({})

    def _load(self):
        with open(self.path, 'r', encoding='utf-8') as f: return json.load(f)

    def _save(self, data):
        with open(self.path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

    def set_group(self, filename: str, group: str):
        data = self._load()
        if filename not in data:
            data[filename] = {}
        data[filename]["group"] = group
        self._save(data)

    def get_group(self, filename: str):
        data = self._load()
        return data.get(filename, {}).get("group", "未分组")

    def get_all_groups(self):
        data = self._load()
        groups = set()
        for meta in data.values():
            if "group" in meta: groups.add(meta["group"])
        return list(groups)

    def delete_meta(self, filename: str):
        data = self._load()
        if filename in data:
            del data[filename]
            self._save(data)

    def rename_meta(self, old_name, new_name):
        data = self._load()
        if old_name in data:
            data[new_name] = data[old_name]
            del data[old_name]
            self._save(data)


file_manager = FileManager()