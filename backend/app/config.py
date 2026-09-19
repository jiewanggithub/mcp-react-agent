"""全局配置管理。

统一从 .env 读取运行时配置，并提供 servers_config.json 的加载与
环境变量占位符（${VAR_NAME}）替换能力，使 MCP 服务集合可以在不
修改任何 Python 代码的情况下新增/删除/切换。
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
SERVERS_CONFIG_PATH = BACKEND_DIR / "servers_config.json"

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    use_real_llm: bool = False
    dashscope_api_key: str = ""
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_model: str = "qwen-plus"

    amap_mcp_sse_url: str = ""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    file_output_dir: str = "data/output"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _substitute_env(value):
    """递归地将字符串中的 ${VAR} 替换为对应环境变量的值。"""
    if isinstance(value, str):
        def repl(m: re.Match) -> str:
            return os.environ.get(m.group(1), "")

        return _ENV_VAR_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _substitute_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_env(v) for v in value]
    return value


def load_mcp_servers_config() -> dict:
    """加载 servers_config.json，并对其中的 ${ENV_VAR} 占位符做替换。

    这是"工具集合与 Agent 推理逻辑完全解耦"的核心：新增一个 MCP Server
    只需要在这个 JSON 文件里加一条配置，Agent 层通过
    MultiServerMCPClient 在启动时自动发现并加载，完全不需要改动
    agent.py 中的推理主流程代码。
    """
    if not SERVERS_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"未找到 MCP servers 配置文件: {SERVERS_CONFIG_PATH}"
        )
    raw = json.loads(SERVERS_CONFIG_PATH.read_text(encoding="utf-8"))
    resolved = _substitute_env(raw)

    # 跳过缺少必要 URL（例如用户尚未配置高德 Key）的远程 SSE 服务，
    # 避免因为一个可选服务未配置而导致整个 Agent 启动失败。
    servers = {}
    for name, cfg in resolved.items():
        if cfg.get("transport") == "sse" and not cfg.get("url"):
            print(f"[config] 跳过 MCP server '{name}'：未配置 URL（环境变量未设置）")
            continue
        servers[name] = {k: v for k, v in cfg.items() if k != "transport" or True}
    return servers
