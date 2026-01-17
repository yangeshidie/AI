# app/workflow/schemas.py
"""
工作流相关的数据模型定义
"""
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class NodeType(str, Enum):
    """节点类型枚举"""
    START = "start"
    END = "end"
    LLM = "llm"
    RAG = "rag"
    CODE = "code"
    CONDITION = "condition"
    HTTP_REQUEST = "http_request"
    VARIABLE = "variable"
    TEMPLATE = "template"


class NodeData(BaseModel):
    """节点数据基类"""
    node_id: str = Field(..., description="节点ID")
    node_type: NodeType = Field(..., description="节点类型")
    position: Dict[str, float] = Field(default={"x": 0, "y": 0}, description="节点位置")
    data: Dict[str, Any] = Field(default_factory=dict, description="节点配置数据")


class LLMNodeData(NodeData):
    """LLM 节点数据"""
    node_type: NodeType = NodeType.LLM
    model: str = Field(..., description="模型名称")
    api_url: str = Field(..., description="API URL")
    api_key: str = Field(..., description="API Key")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    stream: bool = Field(default=False, description="是否流式输出")


class RAGNodeData(NodeData):
    """RAG 节点数据"""
    node_type: NodeType = NodeType.RAG
    kb_ids: List[str] = Field(default_factory=list, description="知识库ID列表")
    query: str = Field(..., description="查询模板，支持变量引用如 {{user_input}}")
    top_k: int = Field(default=3, description="返回结果数量")


class CodeNodeData(NodeData):
    """代码执行节点数据"""
    node_type: NodeType = NodeType.CODE
    code: str = Field(..., description="Python 代码")
    timeout: int = Field(default=30, description="超时时间（秒）")


class ConditionNodeData(NodeData):
    """条件判断节点数据"""
    node_type: NodeType = NodeType.CONDITION
    conditions: List[Dict[str, Any]] = Field(..., description="条件列表")
    default_branch: Optional[str] = Field(None, description="默认分支节点ID")


class HTTPRequestNodeData(NodeData):
    """HTTP 请求节点数据"""
    node_type: NodeType = NodeType.HTTP_REQUEST
    url: str = Field(..., description="请求URL")
    method: str = Field(default="GET", description="请求方法")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    body: Optional[Dict[str, Any]] = Field(None, description="请求体")
    timeout: int = Field(default=30, description="超时时间（秒）")


class VariableNodeData(NodeData):
    """变量节点数据"""
    node_type: NodeType = NodeType.VARIABLE
    variable_name: str = Field(..., description="变量名称")
    default_value: Any = Field(None, description="默认值")
    variable_type: str = Field(default="string", description="变量类型")


class TemplateNodeData(NodeData):
    """模板节点数据"""
    node_type: NodeType = NodeType.TEMPLATE
    template: str = Field(..., description="模板内容，支持变量引用")


class Edge(BaseModel):
    """连接边"""
    id: str = Field(..., description="边ID")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    source_handle: Optional[str] = Field(None, description="源节点输出端口")
    target_handle: Optional[str] = Field(None, description="目标节点输入端口")
    condition: Optional[str] = Field(None, description="条件表达式")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(None, description="工作流描述")
    nodes: List[Dict[str, Any]] = Field(..., description="节点列表")
    edges: List[Edge] = Field(..., description="连接边列表")
    variables: Dict[str, Any] = Field(default_factory=dict, description="全局变量")
    version: int = Field(default=1, description="版本号")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class WorkflowExecutionRequest(BaseModel):
    """工作流执行请求"""
    workflow_id: str = Field(..., description="工作流ID")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="输入变量")
    stream: bool = Field(default=False, description="是否流式输出")


class WorkflowExecutionResult(BaseModel):
    """工作流执行结果"""
    execution_id: str = Field(..., description="执行ID")
    status: str = Field(..., description="执行状态: running, completed, failed")
    outputs: Dict[str, Any] = Field(default_factory=dict, description="输出结果")
    error: Optional[str] = Field(None, description="错误信息")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    node_results: Dict[str, Any] = Field(default_factory=dict, description="各节点执行结果")
