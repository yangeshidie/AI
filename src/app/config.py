import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 基础路径
BASE_DIR = Path(".")
HISTORY_DIR = BASE_DIR / "history"
UPLOAD_DIR = BASE_DIR / "data_uploads"
KB_META_FILE = BASE_DIR / "kb_metadata.json"
CHROMA_PATH = "chroma_db"

# 确保目录存在
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 默认配置
DEFAULT_API_URL = os.getenv("PROXY_BASE_URL", "https://api.openai.com/v1")
DEFAULT_API_KEY = os.getenv("PROXY_API_KEY", "")
DEFAULT_MODEL = os.getenv("TARGET_MODEL", "gpt-3.5-turbo")