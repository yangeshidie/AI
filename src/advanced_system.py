# advanced_system.py
import datetime
from typing import List, Optional


class SystemPromptBuilder:
    """
    高级 System Prompt 构建器
    支持：动态时间、角色设定、上下文注入、输出约束、思维链引导
    """

    def __init__(self, model_name: str = "default"):
        self.model_name = model_name
        self.role_definition = "你是一个智能、乐于助人的AI助手。"
        self.context_data = ""
        self.constraints = []
        self.output_format = ""
        self.knowledge_base_name = None

    def set_role(self, role_text: str):
        """设定角色人设"""
        self.role_definition = role_text
        return self

    def bind_knowledge_base(self, kb_name: str):
        """绑定知识库名称，增强沉浸感"""
        self.knowledge_base_name = kb_name
        return self

    def inject_context(self, context: str):
        """注入 RAG 检索到的上下文"""
        if context:
            self.context_data = context
        return self

    def add_constraint(self, constraint: str):
        """添加限制条件 (如: 不要编造事实)"""
        self.constraints.append(constraint)
        return self

    def set_output_style(self, style: str):
        """设定输出风格 (如: Markdown, JSON, 简练)"""
        self.output_format = style
        return self

    def build(self) -> dict:
        """生成最终发送给 API 的 system message 对象"""

        # 1. 基础信息构建
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        # 2. 组装 Prompt
        prompt_parts = [
            f"### Role Definition\n{self.role_definition}",
            f"### Current Environment\nTime: {current_time}",
        ]

        # 3. 如果是知识库模式，强化上下文指令
        if self.knowledge_base_name:
            prompt_parts.append(f"### Knowledge Base Context ({self.knowledge_base_name})")
            if self.context_data:
                prompt_parts.append(
                    "You have access to the following local documents. "
                    "Use this information to answer the user's question. "
                    "If the answer is not in the context, strictly state that you don't know.\n"
                    f"```text\n{self.context_data}\n```"
                )
            else:
                prompt_parts.append("No relevant context found in the database for this query.")

        # 4. 添加约束
        default_constraints = [
            "Use Markdown for formatting.",
            "Be concise and professional.",
            "Do not halluciation."
        ]
        all_constraints = default_constraints + self.constraints
        prompt_parts.append("### Constraints\n" + "\n".join([f"- {c}" for c in all_constraints]))

        # 5. 输出格式
        if self.output_format:
            prompt_parts.append(f"### Output Format\n{self.output_format}")

        final_content = "\n\n".join(prompt_parts)

        return {"role": "system", "content": final_content}


# 方便调用的工厂函数
def create_rag_system_prompt(kb_name: str, context: str, role: str = None) -> dict:
    builder = SystemPromptBuilder()
    if role:
        builder.set_role(role)
    else:
        builder.set_role(f"你是 '{kb_name}' 的专属知识库助手。")

    return (builder
            .bind_knowledge_base(kb_name)
            .inject_context(context)
            .add_constraint("优先基于提供的 [Context] 回答问题。")
            .add_constraint("如果 [Context] 中没有答案，请明确告知用户。")
            .build())


def create_chat_system_prompt() -> dict:
    return (SystemPromptBuilder()
            .set_role("你是一个全能型的 AI 助手，擅长编程、写作和分析。")
            .add_constraint("回答要富有逻辑性。")
            .build())