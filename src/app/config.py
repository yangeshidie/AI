# app/config.py
"""
应用程序配置模块
负责加载环境变量、定义基础路径和默认配置
"""
import os
import socket
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def setup_network() -> None:
    """
    智能网络配置：检测代理可用性
    - 如果代理可用（端口7890），设置代理直接访问 Hugging Face
    - 如果代理不可用，使用国内镜像
    """
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 7890

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((proxy_host, proxy_port))
        sock.close()

        if result == 0:
            proxy_url = f"http://{proxy_host}:{proxy_port}"
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            print(f"🌐 检测到代理 ({proxy_url})，使用代理访问 Hugging Face")
        else:
            raise ConnectionError("Proxy not available")
    except Exception:
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("🪞 未检测到代理，使用 Hugging Face 镜像 (hf-mirror.com)")


# 在加载其他模块前执行网络配置
setup_network()

load_dotenv()

# =============================================================================
# 基础路径配置
# =============================================================================
BASE_DIR: Path = Path(".")
HISTORY_DIR: Path = BASE_DIR / "history"
UPLOAD_DIR: Path = BASE_DIR / "data_uploads"
KB_META_FILE: Path = BASE_DIR / "kb_metadata.json"
CHROMA_PATH: str = "chroma_db"

# 确保必要目录存在
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# 默认 API 配置
# =============================================================================
DEFAULT_API_URL: str = os.getenv("PROXY_BASE_URL", "https://api.openai.com/v1")
DEFAULT_API_KEY: str = os.getenv("PROXY_API_KEY", "")
DEFAULT_MODEL: str = os.getenv("TARGET_MODEL", "gpt-3.5-turbo")