"""LLM 接入层：通义千问（Qwen），带 Mock 兜底。

USE_REAL_LLM=false 时返回一个规则化的 MockChatModel，
在没有 DashScope Key 的情况下也能跑通整条 ReAct 工具调用链路，
便于本地开发与演示；USE_REAL_LLM=true 时通过 DashScope 的
OpenAI 兼容接口调用真实的通义千问模型。
"""
from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.config import get_settings


class MockQwenChatModel(BaseChatModel):
    """极简 Mock 模型：不真正理解语义，仅用于跑通链路/演示。

    真实场景请设置 USE_REAL_LLM=true 并配置 DASHSCOPE_API_KEY。
    """

    @property
    def _llm_type(self) -> str:
        return "mock-qwen"

    def bind_tools(self, tools, **kwargs):
        # Mock 模型不做真实的工具选择，直接忽略绑定的工具列表，
        # 仅用于让 create_react_agent 的 bind_tools 调用跑通。
        return self

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs) -> ChatResult:
        last_user_text = ""
        for m in reversed(messages):
            if m.type == "human":
                last_user_text = m.content if isinstance(m.content, str) else str(m.content)
                break
        reply = (
            "[Mock 回复] 已收到你的问题："
            f"{last_user_text}\n"
            "（当前使用的是 Mock LLM，未接入真实通义千问。"
            "设置 USE_REAL_LLM=true 并配置 DASHSCOPE_API_KEY 后即可切换为真实模型。）"
        )
        message = AIMessage(content=reply)
        return ChatResult(generations=[ChatGeneration(message=message)])


def get_llm():
    """按配置返回可绑定工具的 Chat 模型实例。"""
    settings = get_settings()

    if not settings.use_real_llm:
        return MockQwenChatModel()

    # 通义千问 DashScope OpenAI 兼容模式
    from langchain_openai import ChatOpenAI

    if not settings.dashscope_api_key:
        raise ValueError(
            "USE_REAL_LLM=true 但未配置 DASHSCOPE_API_KEY，请检查 .env 文件。"
        )

    return ChatOpenAI(
        model=settings.qwen_model,
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        temperature=0.3,
    )
