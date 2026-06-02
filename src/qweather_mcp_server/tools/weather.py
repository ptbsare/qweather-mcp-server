"""Weather tools: current, forecast, hourly, minutely, history, warnings, indices, astronomy."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from qweather_mcp_server.core.config import api_host
from qweather_mcp_server.core.http import api_get
from qweather_mcp_server.tools.geo import _resolve_city

logger = logging.getLogger("qweather_mcp_server")

_DEFAULT_EXECUTOR = ThreadPoolExecutor(max_workers=4)


def _resolve_location(location: Optional[str], city: Optional[str]) -> Optional[str]:
    """Resolve *location* or *city* to a LocationID / coords string."""
    if location and location.strip():
        loc = location.strip()
        if "," in loc:
            return loc
        if loc.isdigit():
            return loc
        resolved = _resolve_city(loc)
        return resolved or loc
    if city and city.strip():
        return _resolve_city(city.strip())
    logger.error("Neither location nor city provided")
    return None


def register_weather_tools(mcp: FastMCP) -> None:
    """Register all weather-related tools."""

    @mcp.tool()
    def get_weather_now(
        location: Optional[str] = None,
        city: Optional[str] = None,
        lang: str = "zh",
        unit: str = "m",
    ) -> Dict[str, Any]:
        """获取实时天气。

        Args:
            location: LocationID 或 "经度,纬度" 坐标。与 city 二选一。
            city: 城市名称，如 "北京"。与 location 二选一。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        loc = _resolve_location(location, city)
        if not loc:
            return {"code": "error", "error": "Cannot resolve location"}
        return api_get(
            f"https://{api_host}/v7/weather/now",
            params={"location": loc, "lang": lang, "unit": unit},
        )

    @mcp.tool()
    def get_weather(city: str, days: str = "3d") -> Dict[str, Any]:
        """获取逐天天气预报。

        Args:
            city: 城市名称。
            days: 预报天数，支持 3d/7d/10d/15d/30d，默认 3d。
        """
        valid = {"3d", "7d", "10d", "15d", "30d"}
        if days not in valid:
            return {"code": "error", "error": f"Invalid days: {days}"}
        loc = _resolve_city(city.strip())
        if not loc:
            return {"code": "error", "error": f"Cannot resolve city: {city}"}
        return api_get(f"https://{api_host}/v7/weather/{days}", params={"location": loc})

    @mcp.tool()
    def get_hourly_weather(
        hours: str = "24h",
        location: Optional[str] = None,
        city: Optional[str] = None,
        lang: str = "zh",
        unit: str = "m",
    ) -> Dict[str, Any]:
        """获取逐小时天气预报。

        Args:
            hours: 预报时长，支持 24h/72h/168h，默认 24h。
            location: LocationID 或 "经度,纬度" 坐标。与 city 二选一。
            city: 城市名称。与 location 二选一。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if hours not in {"24h", "72h", "168h"}:
            return {"code": "error", "error": f"Invalid hours: {hours}"}
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        loc = _resolve_location(location, city)
        if not loc:
            return {"code": "error", "error": "Cannot resolve location"}
        return api_get(
            f"https://{api_host}/v7/weather/{hours}",
            params={"location": loc, "lang": lang, "unit": unit},
        )

    @mcp.tool()
    def get_minutely_5m(location: str, lang: str = "zh") -> Dict[str, Any]:
        """获取分钟级降水预报（未来2小时，5分钟间隔）。

        Args:
            location: "经度,纬度" 坐标或城市名称。
            lang: 语言，默认 "zh"。
        """
        loc = location.strip()
        if "," not in loc:
            resolved = _resolve_city(loc, as_coords=True)
            if not resolved:
                return {"code": "error", "error": f"Cannot resolve city: {loc}"}
            loc = resolved
        else:
            try:
                parts = [s.strip() for s in loc.split(",", 1)]
                lon, lat = float(parts[0]), float(parts[1])
                loc = f"{lon:.2f},{lat:.2f}"
            except Exception:
                return {"code": "error", "error": f"Bad coords: {loc}"}
        return api_get(
            f"https://{api_host}/v7/minutely/5m",
            params={"location": loc, "lang": lang},
        )

    @mcp.tool()
    def get_warning(city: str) -> Dict[str, Any]:
        """获取气象预警信息。

        Args:
            city: 城市名称。
        """
        loc = _resolve_city(city.strip())
        if not loc:
            return {"code": "error", "error": f"Cannot resolve city: {city}"}
        return api_get(
            f"https://{api_host}/v7/warning/now",
            params={"location": loc, "lang": "zh"},
        )

    @mcp.tool()
    def get_indices(
        city: str,
        days: str = "1d",
        index_types: str = "1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16",
    ) -> Dict[str, Any]:
        """获取生活指数预报（16种）。

        Args:
            city: 城市名称。
            days: 预报天数，支持 1d/3d，默认 1d。
            index_types: 指数类型 ID，逗号分隔，默认全部。
                1-运动 2-洗车 3-穿衣 4-感冒 5-紫外线 6-旅游
                7-过敏 8-舒适度 9-交通 10-防晒 11-化妆 12-空调
                13-晾晒 14-钓鱼 15-太阳镜 16-空气污染扩散
        """
        if days not in {"1d", "3d"}:
            return {"code": "error", "error": f"Invalid days: {days}"}
        loc = _resolve_city(city.strip())
        if not loc:
            return {"code": "error", "error": f"Cannot resolve city: {city}"}
        return api_get(
            f"https://{api_host}/v7/indices/{days}",
            params={"location": loc, "type": index_types.strip(), "lang": "zh"},
        )

    @mcp.tool()
    def get_astronomy_sun(location: str, date: str, lang: str = "zh") -> Dict[str, Any]:
        """获取日出日落时间。

        Args:
            location: 城市名称、LocationID 或 "经度,纬度" 坐标。
            date: 日期，格式 yyyyMMdd，支持未来60天。
            lang: 语言，默认 "zh"。
        """
        loc = _resolve_astronomy_location(location)
        if not loc:
            return {"code": "error", "error": "Cannot resolve location"}
        if not _validate_astronomy_date(date):
            return {"code": "error", "error": f"Invalid date: {date}"}
        return api_get(
            f"https://{api_host}/v7/astronomy/sun",
            params={"location": loc, "date": date, "lang": lang},
        )

    @mcp.tool()
    def get_astronomy_moon(location: str, date: str, lang: str = "zh") -> Dict[str, Any]:
        """获取月升月落时间和月相。

        Args:
            location: 城市名称、LocationID 或 "经度,纬度" 坐标。
            date: 日期，格式 yyyyMMdd，支持未来60天。
            lang: 语言，默认 "zh"。
        """
        loc = _resolve_astronomy_location(location)
        if not loc:
            return {"code": "error", "error": "Cannot resolve location"}
        if not _validate_astronomy_date(date):
            return {"code": "error", "error": f"Invalid date: {date}"}
        return api_get(
            f"https://{api_host}/v7/astronomy/moon",
            params={"location": loc, "date": date, "lang": lang},
        )

    @mcp.tool()
    def get_weather_history(
        *,
        location: Optional[str] = None,
        city: Optional[str] = None,
        days: int = 10,
        lang: str = "zh",
        unit: str = "m",
    ) -> Dict[str, Any]:
        """获取历史天气数据（并发请求）。

        Args:
            location: LocationID 或 "经度,纬度" 坐标。与 city 二选一。
            city: 城市名称。与 location 二选一。
            days: 天数，1-10，默认 10。
            lang: 语言，默认 "zh"。
            unit: 单位，"m" 公制（默认）或 "i" 英制。
        """
        if not 1 <= days <= 10:
            return {"code": "error", "error": f"Invalid days: {days}"}
        if unit not in {"m", "i"}:
            return {"code": "error", "error": f"Invalid unit: {unit}"}
        loc = _resolve_location(location, city)
        if not loc:
            return {"code": "error", "error": "Cannot resolve location"}

        beijing_now = datetime.now(timezone.utc) + timedelta(hours=8)
        dates = [
            (beijing_now - timedelta(days=o)).strftime("%Y%m%d")
            for o in range(days, 0, -1)
        ]

        results: Dict[str, Any] = {}

        def _fetch(date: str) -> tuple:
            data = api_get(
                f"https://{api_host}/v7/historical/weather",
                params={"location": loc, "date": date, "lang": lang, "unit": unit},
            )
            return date, data

        futures = {_DEFAULT_EXECUTOR.submit(_fetch, d): d for d in dates}
        for fut in as_completed(futures):
            d, data = fut.result()
            results[d] = data or {"error": "no data"}

        logger.info(f"History weather fetched for {city or location}: {len(results)} days")
        return results


def _resolve_astronomy_location(location: str) -> Optional[str]:
    """Resolve location for astronomy APIs (accepts coords, LocationID, or city name)."""
    loc = location.strip()
    if "," in loc:
        try:
            a, b = [float(s) for s in loc.split(",", 1)]
            return f"{a:.2f},{b:.2f}"
        except Exception:
            logger.error(f"Bad coords: {loc}")
            return None
    if loc.isdigit():
        return loc
    resolved = _resolve_city(loc)
    return resolved or loc


def _validate_astronomy_date(date: str) -> bool:
    """Validate yyyyMMdd format and range (today … today+60 days)."""
    try:
        target = datetime.strptime(date, "%Y%m%d").date()
    except Exception:
        logger.error(f"Bad date format: {date}")
        return False
    today = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
    if target < today or target > today + timedelta(days=60):
        logger.error(f"Date {date} out of range [{today}, {today + timedelta(days=60)}]")
        return False
    return True
