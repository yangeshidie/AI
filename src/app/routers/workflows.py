# app/routers/workflows.py
"""
工作流相关 API 路由
"""
import os
import logging
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

from app.workflow import (
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResult,
    workflow_manager,
    workflow_engine
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

logger = logging.getLogger(__name__)


@router.post("/create")
async def create_workflow(
    name: str,
    description: str = None,
    nodes: List[Dict[str, Any]] = None,
    edges: List[Dict[str, Any]] = None,
    variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """创建新工作流"""
    try:
        workflow = workflow_manager.create_workflow(
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            variables=variables
        )
        return {"status": "success", "workflow": workflow.dict()}
    except Exception as e:
        logger.error(f"创建工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_workflows() -> Dict[str, List[Dict[str, Any]]]:
    """列出所有工作流"""
    try:
        workflows = workflow_manager.list_workflows()
        return {"workflows": [wf.dict() for wf in workflows.values()]}
    except Exception as e:
        logger.error(f"列出工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """获取指定工作流的详细信息"""
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return workflow.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    name: str = None,
    description: str = None,
    nodes: List[Dict[str, Any]] = None,
    edges: List[Dict[str, Any]] = None,
    variables: Dict[str, Any] = None
) -> Dict[str, Any]:
    """更新工作流"""
    try:
        workflow = workflow_manager.update_workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            nodes=nodes,
            edges=edges,
            variables=variables
        )
        if workflow is None:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return {"status": "success", "workflow": workflow.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> Dict[str, str]:
    """删除工作流"""
    try:
        success = workflow_manager.delete_workflow(workflow_id)
        if not success:
            raise HTTPException(status_code=404, detail="工作流不存在")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest
) -> Dict[str, Any]:
    """执行工作流"""
    try:
        workflow = workflow_manager.get_workflow(workflow_id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="工作流不存在")

        result = await workflow_engine.execute(
            workflow=workflow,
            inputs=request.inputs,
            stream=request.stream
        )

        return result.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行工作流失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_name}")
async def get_workflow_template(template_name: str) -> Dict[str, Any]:
    """获取工作流模板"""
    templates = {
        "simple_chat": {
            "name": "简单对话",
            "description": "一个简单的 LLM 对话工作流",
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "position": {"x": 100, "y": 100},
                    "data": {}
                },
                {
                    "node_id": "llm_1",
                    "node_type": "llm",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "api_url": "https://api.openai.com/v1",
                        "api_key": "",
                        "system_prompt": "你是一个智能助手",
                        "temperature": 0.7,
                        "user_message": "{{user_input}}"
                    }
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "position": {"x": 500, "y": 100},
                    "data": {
                        "output_mapping": {
                            "response": "{{llm_1}}"
                        }
                    }
                }
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "start",
                    "target": "llm_1"
                },
                {
                    "id": "e2",
                    "source": "llm_1",
                    "target": "end"
                }
            ],
            "variables": {}
        },
        "rag_chat": {
            "name": "RAG 对话",
            "description": "基于知识库的对话工作流",
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "position": {"x": 100, "y": 100},
                    "data": {}
                },
                {
                    "node_id": "rag_1",
                    "node_type": "rag",
                    "position": {"x": 300, "y": 100},
                    "data": {
                        "kb_ids": [],
                        "query": "{{user_input}}",
                        "top_k": 3
                    }
                },
                {
                    "node_id": "template_1",
                    "node_type": "template",
                    "position": {"x": 500, "y": 100},
                    "data": {
                        "template": "基于以下上下文回答问题：\n\n{{rag_1}}\n\n问题：{{user_input}}"
                    }
                },
                {
                    "node_id": "llm_1",
                    "node_type": "llm",
                    "position": {"x": 700, "y": 100},
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "api_url": "https://api.openai.com/v1",
                        "api_key": "",
                        "system_prompt": "你是一个知识库助手",
                        "temperature": 0.7,
                        "user_message": "{{template_1}}"
                    }
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "position": {"x": 900, "y": 100},
                    "data": {
                        "output_mapping": {
                            "response": "{{llm_1}}",
                            "context": "{{rag_1}}"
                        }
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "rag_1"},
                {"id": "e2", "source": "rag_1", "target": "template_1"},
                {"id": "e3", "source": "template_1", "target": "llm_1"},
                {"id": "e4", "source": "llm_1", "target": "end"}
            ],
            "variables": {}
        },
        "conditional_flow": {
            "name": "条件分支",
            "description": "包含条件判断的工作流",
            "nodes": [
                {
                    "node_id": "start",
                    "node_type": "start",
                    "position": {"x": 100, "y": 200},
                    "data": {}
                },
                {
                    "node_id": "condition_1",
                    "node_type": "condition",
                    "position": {"x": 300, "y": 200},
                    "data": {
                        "conditions": [
                            {
                                "condition": "{{user_type}} == 'admin'",
                                "branch": "llm_admin"
                            },
                            {
                                "condition": "{{user_type}} == 'user'",
                                "branch": "llm_user"
                            }
                        ],
                        "default_branch": "llm_default"
                    }
                },
                {
                    "node_id": "llm_admin",
                    "node_type": "llm",
                    "position": {"x": 500, "y": 100},
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "api_url": "https://api.openai.com/v1",
                        "api_key": "",
                        "system_prompt": "你是管理员助手",
                        "user_message": "{{user_input}}"
                    }
                },
                {
                    "node_id": "llm_user",
                    "node_type": "llm",
                    "position": {"x": 500, "y": 200},
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "api_url": "https://api.openai.com/v1",
                        "api_key": "",
                        "system_prompt": "你是普通用户助手",
                        "user_message": "{{user_input}}"
                    }
                },
                {
                    "node_id": "llm_default",
                    "node_type": "llm",
                    "position": {"x": 500, "y": 300},
                    "data": {
                        "model": "gpt-3.5-turbo",
                        "api_url": "https://api.openai.com/v1",
                        "api_key": "",
                        "system_prompt": "你是通用助手",
                        "user_message": "{{user_input}}"
                    }
                },
                {
                    "node_id": "end",
                    "node_type": "end",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "output_mapping": {
                            "response": "{{condition_1}}"
                        }
                    }
                }
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "condition_1"},
                {"id": "e2", "source": "condition_1", "target": "llm_admin"},
                {"id": "e3", "source": "condition_1", "target": "llm_user"},
                {"id": "e4", "source": "condition_1", "target": "llm_default"},
                {"id": "e5", "source": "llm_admin", "target": "end"},
                {"id": "e6", "source": "llm_user", "target": "end"},
                {"id": "e7", "source": "llm_default", "target": "end"}
            ],
            "variables": {}
        }
    }

    if template_name not in templates:
        raise HTTPException(status_code=404, detail="模板不存在")

    return templates[template_name]


@router.get("/configs")
async def get_configs() -> Dict[str, List[Dict[str, Any]]]:
    """获取所有配置预设"""
    try:
        load_dotenv(override=True)
        configs = []
        for key in os.environ:
            if key.startswith("PROXY_BASE_URL_"):
                config_name = key.replace("PROXY_BASE_URL_", "")
                base_url = os.getenv(key)
                api_key = os.getenv(f"PROXY_API_KEY_{config_name}", "")
                
                configs.append({
                    "name": config_name,
                    "api_url": base_url,
                    "api_key": api_key
                })
        
        return {"configs": sorted(configs, key=lambda x: x["name"])}
    except Exception as e:
        logger.error(f"获取配置列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
