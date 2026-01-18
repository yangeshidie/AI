# app/workflow/engine.py
"""
工作流执行引擎
负责解析和执行工作流定义
"""
import json
import os
import uuid
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

from openai import OpenAI

from app.workflow.schemas import (
    WorkflowDefinition,
    WorkflowExecutionResult,
    NodeType,
    Edge
)
from app.core.rag_engine import query_rag_with_filter
from app.core.kb_manager import kb_manager

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    工作流执行引擎
    支持节点编排、变量传递、条件分支等功能
    """

    def __init__(self):
        self.execution_context: Dict[str, Any] = {}
        self.node_results: Dict[str, Any] = {}
        self.visited_nodes: Set[str] = set()

    async def execute(
        self,
        workflow: WorkflowDefinition,
        inputs: Dict[str, Any],
        stream: bool = False
    ) -> WorkflowExecutionResult:
        """
        执行工作流

        Args:
            workflow: 工作流定义
            inputs: 输入变量
            stream: 是否流式输出

        Returns:
            执行结果
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            logger.info(f"开始执行工作流: {workflow.name} (ID: {execution_id})")

            # 初始化执行上下文
            self.execution_context = {
                "inputs": inputs,
                "variables": workflow.variables.copy(),
                "outputs": {}
            }
            self.node_results = {}
            self.visited_nodes = set()

            # 构建节点邻接表
            adjacency = self._build_adjacency_list(workflow.edges)

            # 找到起始节点
            start_node = self._find_start_node(workflow.nodes)
            if not start_node:
                raise ValueError("未找到起始节点")

            # 执行工作流
            await self._execute_node(start_node, workflow, adjacency, stream)

            # 收集最终输出
            outputs = self._collect_outputs(workflow)

            execution_time = time.time() - start_time

            result = WorkflowExecutionResult(
                execution_id=execution_id,
                status="completed",
                outputs=outputs,
                execution_time=execution_time,
                node_results=self.node_results
            )

            logger.info(f"工作流执行完成: {workflow.name}, 耗时: {execution_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"工作流执行失败: {e}", exc_info=True)
            execution_time = time.time() - start_time

            return WorkflowExecutionResult(
                execution_id=execution_id,
                status="failed",
                error=str(e),
                execution_time=execution_time,
                node_results=self.node_results
            )

    def _build_adjacency_list(self, edges: List[Edge]) -> Dict[str, List[Dict[str, Any]]]:
        """构建节点邻接表"""
        adjacency = defaultdict(list)
        for edge in edges:
            adjacency[edge.source].append({
                "target": edge.target,
                "condition": edge.condition
            })
        return dict(adjacency)

    def _find_start_node(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """查找起始节点"""
        for node in nodes:
            if node.get("node_type") == NodeType.START:
                return node
        return None

    def _resolve_variables(self, text: str) -> str:
        """解析变量引用 {{variable_name}}"""
        if not text:
            return text

        def replace_var(match):
            var_name = match.group(1)
            # 优先从节点结果中查找
            if var_name in self.node_results:
                return str(self.node_results[var_name])
            # 从输入中查找
            if var_name in self.execution_context.get("inputs", {}):
                return str(self.execution_context["inputs"][var_name])
            # 从全局变量中查找
            if var_name in self.execution_context.get("variables", {}):
                return str(self.execution_context["variables"][var_name])
            return match.group(0)

        import re
        pattern = r'\{\{([^}]+)\}\}'
        return re.sub(pattern, replace_var, text)

    async def _execute_node(
        self,
        node: Dict[str, Any],
        workflow: WorkflowDefinition,
        adjacency: Dict[str, List[Dict[str, Any]]],
        stream: bool
    ) -> Any:
        """
        执行单个节点

        Args:
            node: 节点数据
            workflow: 工作流定义
            adjacency: 邻接表
            stream: 是否流式输出

        Returns:
            节点执行结果
        """
        node_id = node.get("node_id")

        # 防止循环
        if node_id in self.visited_nodes:
            logger.warning(f"节点 {node_id} 已访问过，跳过")
            return None

        self.visited_nodes.add(node_id)
        node_type = node.get("node_type")

        logger.info(f"执行节点: {node_id} (类型: {node_type})")

        # 执行节点
        result = None
        if node_type == NodeType.START:
            result = await self._execute_start_node(node)
        elif node_type == NodeType.END:
            result = await self._execute_end_node(node)
        elif node_type == NodeType.LLM:
            result = await self._execute_llm_node(node, stream)
        elif node_type == NodeType.RAG:
            result = await self._execute_rag_node(node)
        elif node_type == NodeType.CODE:
            result = await self._execute_code_node(node)
        elif node_type == NodeType.CONDITION:
            result = await self._execute_condition_node(node)
        elif node_type == NodeType.HTTP_REQUEST:
            result = await self._execute_http_node(node)
        elif node_type == NodeType.VARIABLE:
            result = await self._execute_variable_node(node)
        elif node_type == NodeType.TEMPLATE:
            result = await self._execute_template_node(node)
        else:
            raise ValueError(f"未知的节点类型: {node_type}")

        # 保存节点结果
        self.node_results[node_id] = result

        # 执行后续节点
        if node_type != NodeType.END:
            next_edges = adjacency.get(node_id, [])
            for edge_info in next_edges:
                next_node_id = edge_info["target"]
                condition = edge_info.get("condition")

                # 检查条件
                if condition:
                    if self._evaluate_condition(condition):
                        next_node = self._find_node_by_id(workflow.nodes, next_node_id)
                        if next_node:
                            await self._execute_node(next_node, workflow, adjacency, stream)
                else:
                    next_node = self._find_node_by_id(workflow.nodes, next_node_id)
                    if next_node:
                        await self._execute_node(next_node, workflow, adjacency, stream)

        return result

    def _find_node_by_id(self, nodes: List[Dict[str, Any]], node_id: str) -> Optional[Dict[str, Any]]:
        """根据ID查找节点"""
        for node in nodes:
            if node.get("node_id") == node_id:
                return node
        return None

    async def _execute_start_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """执行起始节点"""
        return {"status": "started"}

    async def _execute_end_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """执行结束节点"""
        return {"status": "completed"}

    async def _execute_llm_node(self, node: Dict[str, Any], stream: bool) -> str:
        """执行 LLM 节点"""
        data = node.get("data", {})
        config_id = data.get("config_id", "")
        
        # 从配置预设加载配置
        if config_id:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            
            base_url = os.getenv(f"PROXY_BASE_URL_{config_id}")
            api_key = os.getenv(f"PROXY_API_KEY_{config_id}", "")
            
            if base_url:
                model = data.get("model", "gpt-3.5-turbo")
                api_url = base_url
            else:
                model = data.get("model", "gpt-3.5-turbo")
                api_url = data.get("api_url", "https://api.openai.com/v1")
                api_key = data.get("api_key", "")
        else:
            model = data.get("model", "gpt-3.5-turbo")
            api_url = data.get("api_url", "https://api.openai.com/v1")
            api_key = data.get("api_key", "")
        
        system_prompt = data.get("system_prompt", "")
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens")
        enable_structured_output = data.get("enable_structured_output", False)
        structured_output_schema = data.get("structured_output_schema")

        # 解析变量
        if system_prompt:
            system_prompt = self._resolve_variables(system_prompt)

        user_message = data.get("user_message", "")
        if user_message:
            user_message = self._resolve_variables(user_message)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if user_message:
            messages.append({"role": "user", "content": user_message})

        client = OpenAI(base_url=api_url, api_key=api_key)

        # 构建请求参数
        request_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        # 支持结构化输出
        if enable_structured_output and structured_output_schema:
            try:
                schema = json.loads(structured_output_schema)
                request_params["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_response",
                        "strict": True,
                        "schema": schema
                    }
                }
            except json.JSONDecodeError as e:
                logger.warning(f"结构化输出 Schema 解析失败: {e}")

        if stream:
            # 流式输出
            full_content = ""
            stream_response = client.chat.completions.create(
                **request_params,
                stream=True
            )
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
            return full_content
        else:
            response = client.chat.completions.create(**request_params)
            return response.choices[0].message.content

    async def _execute_rag_node(self, node: Dict[str, Any]) -> str:
        """执行 RAG 节点"""
        data = node.get("data", {})
        kb_ids = data.get("kb_ids", [])
        query_template = data.get("query", "")
        top_k = data.get("top_k", 3)

        # 解析查询变量
        query = self._resolve_variables(query_template)

        # 收集知识库文件
        all_files = []
        for kb_id in kb_ids:
            kb_info = kb_manager.get_kb(kb_id)
            if kb_info:
                all_files.extend(kb_info.get("files", []))

        # 执行 RAG 查询
        if all_files:
            context = query_rag_with_filter(query, all_files, n_results=top_k)
            return context
        else:
            return ""

    async def _execute_code_node(self, node: Dict[str, Any]) -> Any:
        """执行代码节点"""
        data = node.get("data", {})
        code = data.get("code", "")
        timeout = data.get("timeout", 30)

        # 准备执行环境
        exec_globals = {
            "__builtins__": {},
            "context": self.execution_context,
            "results": self.node_results,
            "inputs": self.execution_context.get("inputs", {})
        }

        try:
            # 执行代码
            exec(code, exec_globals)
            return exec_globals.get("output")
        except Exception as e:
            logger.error(f"代码节点执行失败: {e}")
            raise

    async def _execute_condition_node(self, node: Dict[str, Any]) -> str:
        """执行条件节点"""
        data = node.get("data", {})
        conditions = data.get("conditions", [])
        default_branch = data.get("default_branch")

        for condition in conditions:
            condition_expr = condition.get("condition", "")
            branch = condition.get("branch")

            if self._evaluate_condition(condition_expr):
                return branch

        return default_branch

    def _evaluate_condition(self, condition: str) -> bool:
        """评估条件表达式"""
        try:
            # 解析变量
            resolved_condition = self._resolve_variables(condition)

            # 简单的条件评估
            # 注意：生产环境应该使用更安全的表达式评估器
            return bool(eval(resolved_condition, {"__builtins__": {}}))
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False

    async def _execute_http_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """执行 HTTP 请求节点"""
        import requests

        data = node.get("data", {})
        url = self._resolve_variables(data.get("url", ""))
        method = data.get("method", "GET").upper()
        headers = data.get("headers", {})
        body = data.get("body")
        timeout = data.get("timeout", 30)

        # 解析变量
        headers = {k: self._resolve_variables(v) for k, v in headers.items()}
        if body:
            body = json.loads(self._resolve_variables(json.dumps(body)))

        # 发送请求
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
            timeout=timeout
        )

        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        }

    async def _execute_variable_node(self, node: Dict[str, Any]) -> Any:
        """执行变量节点"""
        data = node.get("data", {})
        variable_name = data.get("variable_name", "")
        default_value = data.get("default_value")

        # 优先从上下文中获取
        if variable_name in self.execution_context.get("inputs", {}):
            return self.execution_context["inputs"][variable_name]
        if variable_name in self.execution_context.get("variables", {}):
            return self.execution_context["variables"][variable_name]

        return default_value

    async def _execute_template_node(self, node: Dict[str, Any]) -> str:
        """执行模板节点"""
        data = node.get("data", {})
        template = data.get("template", "")

        return self._resolve_variables(template)

    def _collect_outputs(self, workflow: WorkflowDefinition) -> Dict[str, Any]:
        """收集最终输出"""
        outputs = {}

        # 从结束节点收集输出
        end_node = self._find_node_by_id(workflow.nodes, "end")
        if end_node:
            end_data = end_node.get("data", {})
            output_mapping = end_data.get("output_mapping", {})
            for key, value in output_mapping.items():
                outputs[key] = self._resolve_variables(value)

        # 如果没有输出映射，返回所有节点结果
        if not outputs:
            outputs = self.node_results.copy()

        return outputs


# 模块级单例
workflow_engine = WorkflowEngine()
