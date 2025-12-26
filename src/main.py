from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 导入拆分后的路由
from app.routers import chat, files, kb, history, prompts, settings

app = FastAPI(title="Nexus AI Local")

# 1. 挂载静态文件
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 2. 注册路由
app.include_router(chat.router)
app.include_router(files.router)
app.include_router(kb.router)
app.include_router(history.router)
app.include_router(prompts.router)
app.include_router(settings.router)

# 3. 根路径
@app.get("/")
async def read_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

if __name__ == "__main__":
    import uvicorn
    from app.config import STATIC_DIR
    
    # 确保生成的图片目录存在
    (STATIC_DIR / "generated_images").mkdir(parents=True, exist_ok=True)
    
    print("🚀 Nexus AI Modularized Server Starting...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)