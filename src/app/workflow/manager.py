# app/workflow/manager.py
"""
工作流管理器
负责工作流的创建、查询、删除和持久化
"""
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.workflow.schemas import WorkflowDefinition

WORKFLOW_DIR = Path("workflows")
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)


class WorkflowManager:
    """
    工作流管理类
    使用 JSON 文件存储工作流定义
    """

    def __init__(self) -> None:
        self.workflow_dir: Path = WORKFLOW_DIR

    def _get_workflow_path(self, workflow_id: str) -> Path:
        """获取工作流文件路径"""
        return self.workflow_dir / f"{workflow_id}.json"

    def create_workflow(
        self,
        name: str,
        description: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> WorkflowDefinition:
        """
        创建新工作流

        Args:
            name: 工作流名称
            description: 工作流描述
            nodes: 节点列表
            edges: 边列表
            variables: 全局变量

        Returns:
            创建的工作流定义
        """
        workflow_id = str(uuid.uuid4())[:8]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            nodes=nodes or [],
            edges=edges or [],
            variables=variables or {},
            version=1,
            created_at=now,
            updated_at=now
        )

        self._save_workflow(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        获取工作流定义

        Args:
            workflow_id: 工作流ID

        Returns:
            工作流定义，不存在则返回 None
        """
        file_path = self._get_workflow_path(workflow_id)
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return WorkflowDefinition(**data)

    def list_workflows(self) -> Dict[str, WorkflowDefinition]:
        """
        列出所有工作流

        Returns:
            工作流ID到工作流定义的映射
        """
        workflows = {}
        for file_path in self.workflow_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                workflow = WorkflowDefinition(**data)
                workflows[workflow.workflow_id] = workflow

        return workflows

    def update_workflow(
        self,
        workflow_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        edges: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowDefinition]:
        """
        更新工作流

        Args:
            workflow_id: 工作流ID
            name: 新名称
            description: 新描述
            nodes: 新节点列表
            edges: 新边列表
            variables: 新变量

        Returns:
            更新后的工作流定义，不存在则返回 None
        """
        workflow = self.get_workflow(workflow_id)
        if workflow is None:
            return None

        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if nodes is not None:
            workflow.nodes = nodes
        if edges is not None:
            workflow.edges = edges
        if variables is not None:
            workflow.variables = variables

        workflow.version += 1
        workflow.updated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        self._save_workflow(workflow)
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        删除工作流

        Args:
            workflow_id: 工作流ID

        Returns:
            是否删除成功
        """
        file_path = self._get_workflow_path(workflow_id)
        if not file_path.exists():
            return False

        file_path.unlink()
        return True

    def _save_workflow(self, workflow: WorkflowDefinition) -> None:
        """保存工作流到文件"""
        file_path = self._get_workflow_path(workflow.workflow_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(workflow.dict(), f, ensure_ascii=False, indent=2)


# 模块级单例
workflow_manager = WorkflowManager()
