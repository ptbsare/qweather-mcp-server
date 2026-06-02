"""Air quality tools: current, hourly, daily, stations, history."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from qweather_mcp_server.core.config import api_host
from qweather_mcp_server.core.http import api_get
from qweather_mcp_server.tools.geo import _resolve_city

logger = logging.getLogger("qweather_mcp_server")

_DEFAULT_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _resolve_coords(city: str) -> Optional[str]:
    """Resolve city name to 'lat,lon' string for air quality APIs."""
    raw = _resolve_city(city.strip(), as_coords=True)
    if not raw:
        return None
    lon, lat = raw.split(",")
    return f"{lat},{lon}"


def register_air_tools(mcp: FastMCP) -> None:
    """Register all air-quality-related tools."""

    @mcp.tool()
    def get_air_quality(city: str) -> Dict[str, Any]:
        """获取实时空气质量（AQI、污染物浓度、健康建议）。

        Args:
            city: 城市名称。
        """
        coords = _resolve_coords(city)
        if not coords:
            return {"code": "error", "error": f"Cannot resolve city: {city}"}
        lat, lon = coords.split(",")
        return api_get(f"https://{api_host}/airquality/v1/current/{lat}/{lon}", params={"lang": "zh"})

    @mcp.tool()
    def get_air_quality_hourly(
        location: str, hours: str = "24h", lang: str = "zh"
    ) -> Dict[str, Any]:
        """获取逐小时空气质量预报。

        Args:
            location: "纬度,经度" 坐标或城市名称。
            hours: 预报时长，支持 24h/72h/168h，默认 24h。
            lang: 语言，默认 "zh"。
        """
        if hours not in {"24h", "72h", "168h"}:
            return {"code": "error", "error": f"Invalid hours: {hours}"}
        coords = location.strip()
        if "," not in coords:
            coords = _resolve_coords(coords)
            if not coords:
                return {"code": "error", "error": f"Cannot resolve city: {location}"}
        lat, lon = coords.split(",")
        return api_get(
            f"https://{api_host}/airquality/v1/hourly/{lat}/{lon}",
            params={"hours": hours, "lang": lang},
        )

    @mcp.tool()
    def get_air_quality_daily(
        location: str, days: str = "3d", lang: str = "zh"
    ) -> Dict[str, Any]:
        """获取逐日空气质量预报。

        Args:
            location: "纬度,经度" 坐标或城市名称。
            days: 预报天数，支持 3d/7d/15d，默认 3d。
            lang: 语言，默认 "zh"。
        """
        if days not in {"3d", "7d", "15d"}:
            return {"code": "error", "error": f"Invalid days: {days}"}
        coords = location.strip()
        if "," not in coords:
            coords = _resolve_coords(coords)
            if not coords:
                return {"code": "error", "error": f"Cannot resolve city: {location}"}
        lat, lon = coords.split(",")
        return api_get(
            f"https://{api_host}/airquality/v1/daily/{lat}/{lon}",
            params={"days": days, "lang": lang},
        )

    @mcp.tool()
    def get_air_quality_stations(station_id: str, lang: str = "zh") -> Dict[str, Any]:
        """获取空气质量监测站污染物数据。

        Args:
            station_id: 监测站 ID，如 "P58911"。
            lang: 语言，默认 "zh"。
        """
        return api_get(
            f"https://{api_host}/airquality/v1/station/{station_id.strip()}",
            params={"lang": lang},
        )

    @mcp.tool()
    def get_air_quality_history(city: str, days: int = 10, lang: str = "zh") -> Dict[str, Any]:
        """获取历史空气质量数据（并发请求）。

        Args:
            city: 城市名称。
            days: 天数，1-10，默认 10。
            lang: 语言，默认 "zh"。
        """
        if not 1 <= days <= 10:
            return {"code": "error", "error": f"Invalid days: {days}"}
        loc = _resolve_city(city.strip())
        if not loc:
            return {"code": "error", "error": f"Cannot resolve city: {city}"}

        beijing_now = datetime.now(timezone.utc) + timedelta(hours=8)
        dates = [
            (beijing_now - timedelta(days=o)).strftime("%Y%m%d")
            for o in range(days, 0, -1)
        ]

        results: Dict[str, Any] = {}

        def _fetch(date: str) -> tuple:
            data = api_get(
                f"https://{api_host}/v7/historical/air",
                params={"location": loc, "date": date, "lang": lang},
            )
            return date, data

        futures = {_DEFAULT_EXECUTOR.submit(_fetch, d): d for d in dates}
        for fut in as_completed(futures):
            d, data = fut.result()
            results[d] = data or {"error": "no data"}

        logger.info(f"History air quality fetched for {city}: {len(results)} days")
        return results
