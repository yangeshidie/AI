import json
import datetime
import os
from app.config import HISTORY_DIR

def save_history(messages, filename):
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    save_dir = HISTORY_DIR / date_str
    save_dir.mkdir(parents=True, exist_ok=True)
    if not filename.endswith('.json'): filename += '.json'
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def get_all_history():
    if not HISTORY_DIR.exists(): return {}
    result = {}
    for date_dir in sorted(HISTORY_DIR.iterdir(), reverse=True):
        if date_dir.is_dir():
            files = [f.name for f in sorted(date_dir.glob("*.json"), key=os.path.getmtime, reverse=True)]
            if files: result[date_dir.name] = files
    return result

def load_history_file(filepath_str: str):
    file_path = HISTORY_DIR / filepath_str
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)