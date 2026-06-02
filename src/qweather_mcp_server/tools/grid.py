"""Grid weather tools: high-resolution numerical forecast for any coordinates."""

import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from qweather_mcp_server.core.config import api_host
from qweather_mcp_server.core.http import api_get

logger = logging.getLogger("qweather_mcp_server")


def _validate_coords(location: str) -> Optional[str]:
    """Validate and format 'lon,lat' coords. Returns formatted string or None."""
    loc = location.strip()
    if "," not in loc:
        return None
    try:
        lon, lat = [float(s) for s in loc.split(",", 1)]
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return None
        return f"{lon:.2f},{lat:.2f}"
    except Exception:
        return None


def register_grid_tools(mcp: FastMCP) -> None:
    """Register all grid-weather tools."""

    @mcp.tool()
    def get_grid_weather_now(location: str, lang: str = "zh", unit: str = "m") -> Dict[str, Any]:
        """获取格点实时天气（3-5公里分辨率）。

        Args:
            location: "经度,纬度" 坐标。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        coords = _validate_coords(location)
        if not coords:
            return {"code": "error", "error": f"Invalid coords: {location}"}
        return api_get(
            f"https://{api_host}/v7/grid-weather/now",
            params={"location": coords, "lang": lang, "unit": unit},
        )

    @mcp.tool()
    def get_grid_weather_daily(
        location: str, days: str = "3d", lang: str = "zh", unit: str = "m"
    ) -> Dict[str, Any]:
        """获取格点每日天气预报。

        Args:
            location: "经度,纬度" 坐标。
            days: 预报天数，支持 3d/7d，默认 3d。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if days not in {"3d", "7d"}:
            return {"code": "error", "error": f"Invalid days: {days}"}
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        coords = _validate_coords(location)
        if not coords:
            return {"code": "error", "error": f"Invalid coords: {location}"}
        return api_get(
            f"https://{api_host}/v7/grid-weather/{days}",
            params={"location": coords, "lang": lang, "unit": unit},
        )

    @mcp.tool()
    def get_grid_weather_hourly(
        location: str, hours: str = "24h", lang: str = "zh", unit: str = "m"
    ) -> Dict[str, Any]:
        """获取格点逐小时天气预报。

        Args:
            location: "经度,纬度" 坐标。
            hours: 预报时长，支持 24h/72h，默认 24h。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if hours not in {"24h", "72h"}:
            return {"code": "error", "error": f"Invalid hours: {hours}"}
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        coords = _validate_coords(location)
        if not coords:
            return {"code": "error", "error": f"Invalid coords: {location}"}
        return api_get(
            f"https://{api_host}/v7/grid-weather/{hours}",
            params={"location": coords, "lang": lang, "unit": unit},
        )
