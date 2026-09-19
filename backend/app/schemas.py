from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入的自然语言消息")
    thread_id: str = Field(
        default="default",
        description="会话标识，用于隔离多轮对话上下文，前端每个会话生成一个唯一值",
    )


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


class HealthResponse(BaseModel):
    status: str
    agent_ready: bool
