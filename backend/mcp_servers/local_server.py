"""
本地 MCP Server #1：天气查询 + 季节提示
基于 FastMCP 实现，使用 stdio 协议与 Agent 层通信。

新增工具时只需在本文件中新增一个被 @mcp.tool() 装饰的函数，
Agent 主流程无需任何修改即可自动发现并调用新工具。
"""
from __future__ import annotations

import random
from datetime import datetime

from fastmcp import FastMCP

mcp = FastMCP("weather-season-server")

# ---------------------------------------------------------------------------
# Mock 天气数据源。真实项目中这里应替换为对第三方天气 API 的 HTTP 调用，
# 但为了让整个链路在没有外部 API Key 的情况下也能被跑通与演示，
# 这里使用一个简单的伪随机生成器模拟天气数据。
# ---------------------------------------------------------------------------
_WEATHER_CONDITIONS = ["晴", "多云", "阴", "小雨", "中雨", "雷阵雨", "小雪"]


@mcp.tool()
def get_weather(city: str) -> dict:
    """查询指定城市当前的天气情况。

    Args:
        city: 城市名称，例如 "北京"、"上海"。

    Returns:
        包含城市名、天气状况、气温（摄氏度）、湿度（%）的字典。
    """
    rng = random.Random(hash(city) % (2**32))
    condition = rng.choice(_WEATHER_CONDITIONS)
    temperature = rng.randint(-5, 35)
    humidity = rng.randint(20, 95)
    return {
        "city": city,
        "condition": condition,
        "temperature_celsius": temperature,
        "humidity_percent": humidity,
        "queried_at": datetime.now().isoformat(timespec="seconds"),
        "source": "mock-weather-provider",
    }


@mcp.tool()
def get_season_tip(month: int | None = None) -> dict:
    """根据月份给出当前所处季节以及相应的生活提示。

    Args:
        month: 月份 (1-12)。不传时使用服务器当前月份。

    Returns:
        包含季节名称与提示语的字典。
    """
    m = month if month is not None else datetime.now().month
    if m in (3, 4, 5):
        season, tip = "春季", "气温回升，昼夜温差大，注意适当添减衣物、预防花粉过敏。"
    elif m in (6, 7, 8):
        season, tip = "夏季", "天气炎热，注意防晒补水，避免长时间户外暴晒。"
    elif m in (9, 10, 11):
        season, tip = "秋季", "早晚转凉，谨防感冒，是户外活动的好时节。"
    else:
        season, tip = "冬季", "气温较低，注意保暖，出行留意道路结冰情况。"
    return {"month": m, "season": season, "tip": tip}


if __name__ == "__main__":
    mcp.run(transport="stdio")
