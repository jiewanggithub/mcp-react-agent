"""
本地 MCP Server #2：文件写入
基于 FastMCP 实现，使用 stdio 协议与 Agent 层通信。

为了安全，写入目录被限制在 FILE_OUTPUT_DIR（默认为 backend/data/output）内，
所有路径都会被规范化并校验，防止路径穿越（../）写入到目录之外。
"""
from __future__ import annotations

import os
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("file-writer-server")

_OUTPUT_DIR = Path(
    os.environ.get("FILE_OUTPUT_DIR", "data/output")
).resolve()
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_safe_path(filename: str) -> Path:
    """将 filename 规范化到 _OUTPUT_DIR 内，拒绝任何路径穿越尝试。"""
    candidate = (_OUTPUT_DIR / filename).resolve()
    if _OUTPUT_DIR not in candidate.parents and candidate != _OUTPUT_DIR:
        raise ValueError(f"非法文件路径，禁止写入到输出目录之外: {filename}")
    return candidate


@mcp.tool()
def write_file(filename: str, content: str, append: bool = False) -> dict:
    """将文本内容写入到服务器输出目录下的指定文件。

    Args:
        filename: 文件名（可包含子目录，例如 "notes/today.md"），
            不允许使用 ".." 进行路径穿越。
        content: 要写入的文本内容。
        append: 为 True 时以追加模式写入，默认为覆盖写入。

    Returns:
        包含写入结果的字典：是否成功、绝对路径、写入字节数。
    """
    path = _resolve_safe_path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    mode = "a" if append else "w"
    with open(path, mode, encoding="utf-8") as f:
        written = f.write(content)

    return {
        "success": True,
        "path": str(path),
        "bytes_written": written,
        "mode": "append" if append else "overwrite",
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
