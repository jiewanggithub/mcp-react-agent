from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agent import agent_service
from app.schemas import ChatRequest, ChatResponse, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", agent_ready=agent_service.is_ready)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """异步 Agent 服务接口。

    出于稳定性考虑（LangGraph 流式返回在部分 Web 集成场景下与
    调用链存在兼容性问题），这里统一使用 ainvoke 的非流式方案：
    等待 ReAct 循环完整跑完（理解 -> 工具调用 -> 观察 -> 继续判断，
    直至产出最终回答）后一次性返回。
    """
    if not agent_service.is_ready:
        raise HTTPException(status_code=503, detail="Agent 尚未就绪，请稍后重试")

    try:
        reply = await agent_service.ainvoke(
            user_input=payload.message,
            thread_id=payload.thread_id,
        )
    except Exception as exc:  # noqa: BLE001 - 统一转换为对前端友好的错误
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {exc}") from exc

    return ChatResponse(reply=reply, thread_id=payload.thread_id)
