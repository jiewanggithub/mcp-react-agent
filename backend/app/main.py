from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import agent_service
from app.config import get_settings
from app.routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """统一管理 MCP Client 与 Agent 图的生命周期。

    启动时建立一次 MCP 连接、编译 Agent 图；关闭时统一释放，
    避免每次请求都重新连接 MCP Server 造成的重复初始化与资源泄漏。
    """
    await agent_service.start()
    yield
    await agent_service.stop()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="MCP ReAct Agent API",
        description="基于 MCP 协议的可扩展 ReAct 智能 Agent 系统",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router, prefix="/api")
    return app


app = create_app()
