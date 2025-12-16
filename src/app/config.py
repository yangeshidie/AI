import os
import socket
from pathlib import Path
from dotenv import load_dotenv

# 智能网络配置：检测代理可用性
def setup_network():
    """
    检测代理是否可用：
    - 如果代理可用（端口7890），直接访问 Hugging Face
    - 如果代理不可用，使用国内镜像
    """
    proxy_host = "127.0.0.1"
    proxy_port = 7890
    
    try:
        # 尝试连接代理端口
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((proxy_host, proxy_port))
        sock.close()
        
        if result == 0:
            # 代理可用，设置代理环境变量
            proxy_url = f"http://{proxy_host}:{proxy_port}"
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            print(f"🌐 检测到代理 ({proxy_url})，使用代理访问 Hugging Face")
        else:
            raise Exception("Proxy not available")
    except:
        # 代理不可用，使用镜像
        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
        print("🪞 未检测到代理，使用 Hugging Face 镜像 (hf-mirror.com)")

# 在加载其他模块前执行网络配置
setup_network()

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