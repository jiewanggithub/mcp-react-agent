# MCP ReAct Agent

基于 MCP（Model Context Protocol）协议的可扩展 ReAct 智能 Agent 系统。

## 架构

```
前端交互层 (Vue3)  →  FastAPI 服务层  →  LangGraph ReAct Agent 层  →  MCP 工具层
                                                                    ├─ 本地 stdio: 天气查询 / 季节提示
                                                                    ├─ 本地 stdio: 文件写入
                                                                    └─ 远程 SSE: 高德地图
```

- **前端交互层**：Vue3 单页聊天应用，支持 Markdown 渲染、加载状态、异常降级提示、XSS 防护（marked + DOMPurify）。
- **FastAPI 服务层**：异步 `/api/chat` 接口，基于 `lifespan` 统一管理 MCP Client 与 Agent 生命周期。
- **LangGraph Agent 层**：`create_react_agent` 构建理解 → 选工具 → 生成参数 → 调用 → 观察 → 继续判断的 ReAct 循环；`InMemorySaver` + `thread_id` 实现多轮对话上下文隔离。
- **MCP 工具层**：`servers_config.json` 统一声明所有 MCP Server（stdio / SSE），`MultiServerMCPClient` 启动时自动发现加载。**新增工具无需修改 Agent 主流程**——本地 Server 加一个 `@mcp.tool()`，或在配置文件里加一条远程 SSE 服务即可。

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 按需修改（默认 USE_REAL_LLM=false，无需任何 Key 即可跑通）
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 接入真实通义千问

在 `backend/.env` 中设置：

```
USE_REAL_LLM=true
DASHSCOPE_API_KEY=sk-xxxx
```

## 接入高德地图 MCP（SSE）

前往 [高德开放平台 MCP Server](https://lbs.amap.com/api/mcp-server) 申请 Key，写入 `backend/.env` 的 `AMAP_MCP_SSE_URL`。未配置时该工具会被自动跳过，不影响其余工具正常使用。

## 新增一个 MCP 工具

1. 本地工具：在 `backend/mcp_servers/*.py` 中新增一个 `@mcp.tool()` 装饰的函数。
2. 远程/新 Server：在 `backend/servers_config.json` 中新增一条 `{"transport": "stdio"|"sse", ...}` 配置。

重启后端后，Agent 会自动发现并纳入可调用工具集合，无需改动 `app/agent.py` 中的任何推理逻辑。
