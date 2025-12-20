# app/routers/settings.py
"""
设置管理 API 路由
负责读取和更新 .env 文件中的动态配置
"""
import os
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import set_key, load_dotenv

router = APIRouter(prefix="/api/settings", tags=["settings"])

ENV_PATH = Path(".env")

class ConfigItem(BaseModel):
    name: str
    base_url: str
    api_key: str

class ConfigResponse(BaseModel):
    configs: List[str]

@router.get("/configs", response_model=ConfigResponse)
async def list_configs():
    """列出所有保存的 API 配置名称"""
    load_dotenv(override=True) # 重新加载以确保获取最新值
    configs = []
    for key in os.environ:
        if key.startswith("PROXY_BASE_URL_"):
            config_name = key.replace("PROXY_BASE_URL_", "")
            # 确保对应的 API KEY 也存在 (可选检查)
            configs.append(config_name)
    return {"configs": sorted(configs)}

@router.get("/config/{name}")
async def get_config(name: str):
    """获取指定配置的详细信息"""
    load_dotenv(override=True)
    base_url = os.getenv(f"PROXY_BASE_URL_{name}")
    api_key = os.getenv(f"PROXY_API_KEY_{name}")
    
    if not base_url:
        raise HTTPException(status_code=404, detail="Config not found")
        
    return {
        "name": name,
        "base_url": base_url,
        "api_key": api_key
    }

@router.post("/configs")
async def save_config(config: ConfigItem):
    """保存或更新 API 配置到 .env"""
    try:
        # 转换为大写名称作为后缀
        suffix = config.name.strip()
        if not suffix:
            raise HTTPException(status_code=400, detail="Config name cannot be empty")
            
        base_url_key = f"PROXY_BASE_URL_{suffix}"
        api_key_key = f"PROXY_API_KEY_{suffix}"
        
        # 如果 .env 不存在，创建一个
        if not ENV_PATH.exists():
            ENV_PATH.touch()
            
        # 使用 dotenv set_key 写入文件
        set_key(ENV_PATH, base_url_key, config.base_url)
        set_key(ENV_PATH, api_key_key, config.api_key)
        
        # 重新加载环境变量
        load_dotenv(override=True)
        
        return {"status": "success", "message": f"Config '{suffix}' saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
