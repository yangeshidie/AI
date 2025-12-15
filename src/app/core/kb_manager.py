import json
import uuid
import datetime
from app.config import KB_META_FILE


class KBManager:
    def __init__(self):
        self.file_path = KB_META_FILE
        if not self.file_path.exists(): self._save({})

    def _load(self):
        with open(self.file_path, 'r', encoding='utf-8') as f: return json.load(f)

    def _save(self, data):
        with open(self.file_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

    def create_kb(self, name: str, description: str, files: list):
        data = self._load()
        kb_id = str(uuid.uuid4())[:8]
        data[kb_id] = {
            "id": kb_id, "name": name, "description": description,
            "files": files, "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self._save(data)
        return data[kb_id]

    def list_kbs(self):
        return self._load()

    def get_kb(self, kb_id):
        return self._load().get(kb_id)

    def delete_kb(self, kb_id):
        data = self._load()
        if kb_id in data:
            del data[kb_id]
            self._save(data)

    def find_kbs_using_file(self, filename: str) -> list:
        data = self._load()
        affected_kbs = []
        for kb_id, kb_data in data.items():
            if filename in kb_data.get("files", []):
                affected_kbs.append(kb_data["name"])
        return affected_kbs

    def remove_file_from_all_kbs(self, filename: str):
        data = self._load()
        for kb_id, kb_data in data.items():
            if filename in kb_data.get("files", []):
                kb_data["files"].remove(filename)
        self._save(data)

    def rename_file_in_kbs(self, old_name: str, new_name: str):
        data = self._load()
        for kb_id, kb_data in data.items():
            files = kb_data.get("files", [])
            if old_name in files:
                files = [new_name if f == old_name else f for f in files]
                kb_data["files"] = files
        self._save(data)


# 单例模式
kb_manager = KBManager()