# app/core/history.py
"""
聊天历史管理模块
负责保存、加载和列出历史会话记录
"""
import json
import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.config import HISTORY_DIR


def save_history(messages: List[Dict[str, Any]], filename: str) -> None:
    """
    保存聊天历史到按日期组织的目录中

    Args:
        messages: 消息列表
        filename: 文件名或完整路径（如 "chat_123.json" 或 "2025-12-27/chat_123.json"）
    """
    # 如果 filename 包含日期目录，直接使用；否则创建新的日期目录
    if '/' in filename:
        file_path = HISTORY_DIR / filename
    else:
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        save_dir = HISTORY_DIR / date_str
        save_dir.mkdir(parents=True, exist_ok=True)

        if not filename.endswith('.json'):
            filename += '.json'

        file_path = save_dir / filename

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def get_all_history() -> Dict[str, List[str]]:
    """
    获取所有历史记录，按日期分组

    Returns:
        日期 -> 文件名列表 的字典，按日期降序排列
    """
    if not HISTORY_DIR.exists():
        return {}

    result: Dict[str, List[str]] = {}
    for date_dir in sorted(HISTORY_DIR.iterdir(), reverse=True):
        if date_dir.is_dir():
            files = [
                f.name
                for f in sorted(date_dir.glob("*.json"), key=os.path.getmtime, reverse=True)
            ]
            if files:
                result[date_dir.name] = files
    return result


def load_history_file(filepath_str: str) -> Optional[List[Dict[str, Any]]]:
    """
    加载指定的历史文件

    Args:
        filepath_str: 相对于 HISTORY_DIR 的文件路径

    Returns:
        消息列表，如果文件不存在则返回 None
    """
    file_path = HISTORY_DIR / filepath_str
    if not file_path.exists():
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)