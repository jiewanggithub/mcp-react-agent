"""LangGraph ReAct Agent 层。

核心能力：
  1. 通过 MultiServerMCPClient 在启动时自动发现并加载 servers_config.json
     中声明的所有 MCP Server（无论是 stdio 还是 SSE 协议），统一抽象为
     LangChain 工具列表。
  2. 使用 langgraph.prebuilt.create_react_agent 构建标准 ReAct 循环：
     理解意图 -> 选择工具 -> 生成参数 -> 调用 -> 观察结果 -> 判断是否继续。
  3. 使用 InMemorySaver 作为 checkpointer，以 thread_id 隔离多轮对话状态，
     解决会话串扰问题。

新增工具无需修改本文件：只需在 servers_config.json 中新增一个 MCP Server
条目，或在已有的本地 MCP Server 文件中新增一个 @mcp.tool()，重启服务后
Agent 会自动发现并纳入可选工具集合。
"""
from __future__ import annotations

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from app.config import load_mcp_servers_config
from app.llm import get_llm

SYSTEM_PROMPT = (
    "你是一个可以调用外部工具的智能助手。"
    "请根据用户的意图，自主判断是否需要调用工具、调用哪个工具、"
    "如何生成工具参数；如果一次调用不足以回答问题，可以连续调用多个工具，"
    "并在获得足够信息后，将所有工具的观察结果整合为一句清晰、完整的最终回答。"
)


class AgentService:
    """封装 MCP Client 与 LangGraph Agent 的生命周期。

    与 FastAPI 的 lifespan 配合使用：在应用启动时调用一次 `start()`
    建立所有 MCP 连接并编译 Agent 图，应用关闭时调用 `stop()` 统一释放，
    避免每次请求都重复初始化、造成资源泄漏。
    """

    def __init__(self) -> None:
        self._mcp_client: MultiServerMCPClient | None = None
        self._graph = None
        self._checkpointer = InMemorySaver()

    async def start(self) -> None:
        servers = load_mcp_servers_config()
        self._mcp_client = MultiServerMCPClient(servers)
        tools = await self._mcp_client.get_tools()

        llm = get_llm()
        self._graph = create_react_agent(
            model=llm,
            tools=tools,
            checkpointer=self._checkpointer,
            state_modifier=SYSTEM_PROMPT,
        )
        print(f"[agent] 已加载 {len(tools)} 个工具: {[t.name for t in tools]}")

    async def stop(self) -> None:
        # MultiServerMCPClient 的底层连接随进程退出而释放；
        # 这里预留显式清理钩子，便于未来切换到长连接资源时统一收口。
        self._mcp_client = None
        self._graph = None

    async def ainvoke(self, user_input: str, thread_id: str) -> str:
        if self._graph is None:
            raise RuntimeError("Agent 尚未初始化，请检查 lifespan 启动逻辑。")

        config = {"configurable": {"thread_id": thread_id}}
        result = await self._graph.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config=config,
        )
        final_message = result["messages"][-1]
        content = final_message.content
        return content if isinstance(content, str) else str(content)

    @property
    def is_ready(self) -> bool:
        return self._graph is not None


agent_service = AgentService()
