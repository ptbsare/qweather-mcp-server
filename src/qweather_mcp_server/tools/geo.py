"""Geo tools: city lookup, top cities, POI search."""

import logging
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from qweather_mcp_server.core.cache import geo_cache
from qweather_mcp_server.core.config import api_host
from qweather_mcp_server.core.http import api_get

logger = logging.getLogger("qweather_mcp_server")

POI_TYPES = {"scenic": "景点", "TSTA": "潮汐站点"}


def _resolve_city(city: str, as_coords: bool = False) -> Optional[str]:
    """Resolve city name to LocationID (default) or 'lon,lat' coords.

    Uses geo_cache to avoid repeated API calls.
    """
    cache_key = f"city:{city}:{'coords' if as_coords else 'id'}"
    cached = geo_cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"https://{api_host}/geo/v2/city/lookup"
    data = api_get(url, params={"location": city})
    if not data or not data.get("location"):
        logger.warning(f"City '{city}' not found via GeoAPI")
        return None

    loc = data["location"][0]
    if as_coords:
        result = f"{float(loc['lon']):.2f},{float(loc['lat']):.2f}"
    else:
        result = loc["id"]

    geo_cache.set(cache_key, result)
    logger.info(f"Resolved '{city}' → {result}")
    return result


def register_geo_tools(mcp: FastMCP) -> None:
    """Register all geo-related tools."""

    @mcp.tool()
    def get_top_cities(
        number: int = 10, city_type: str = "cn", lang: str = "zh"
    ) -> Dict[str, Any]:
        """获取热门城市列表。

        Args:
            number: 返回数量，1-100，默认 10。
            city_type: 城市类型，cn/world/overseas，默认 cn。
            lang: 语言，默认 "zh"。
        """
        if not 1 <= number <= 100:
            return {"code": "error", "error": f"Invalid number: {number}"}
        if city_type not in {"cn", "world", "overseas"}:
            return {"code": "error", "error": f"Invalid city_type: {city_type}"}
        return api_get(
            f"https://{api_host}/geo/v2/city/top",
            params={"number": str(number), "type": city_type, "lang": lang},
        )

    @mcp.tool()
    def search_poi(
        location: str,
        keyword: str,
        poi_type: str,
        city: Optional[str] = None,
        radius: int = 5000,
        page: int = 1,
        lang: str = "zh",
    ) -> Dict[str, Any]:
        """关键词搜索兴趣点（POI）。

        Args:
            location: "经度,纬度" 坐标或城市名称。
            keyword: 搜索关键词。
            poi_type: POI 类型，scenic（景点）或 TSTA（潮汐站点）。
            city: 限定城市（可选）。
            radius: 搜索半径（米），100-50000，默认 5000。
            page: 页码，默认 1。
            lang: 语言，默认 "zh"。
        """
        if poi_type not in POI_TYPES:
            return {"code": "error", "error": f"Invalid poi_type: {poi_type}"}
        if not 100 <= radius <= 50000:
            return {"code": "error", "error": f"Invalid radius: {radius}"}

        loc = location.strip()
        if "," in loc:
            try:
                lon, lat = [float(s) for s in loc.split(",", 1)]
                loc = f"{lon:.2f},{lat:.2f}"
            except Exception:
                return {"code": "error", "error": f"Bad coords: {loc}"}
        elif loc.isdigit():
            return {"code": "error", "error": "POI lookup requires coords, not LocationID"}
        else:
            resolved = _resolve_city(loc, as_coords=True)
            if not resolved:
                return {"code": "error", "error": f"Cannot resolve city: {loc}"}
            loc = resolved

        params: Dict[str, Any] = {
            "location": loc,
            "keyword": keyword.strip(),
            "type": poi_type,
            "radius": str(radius),
            "page": str(page),
            "lang": lang,
        }
        if city and city.strip():
            c = city.strip()
            params["city"] = c if c.isdigit() else (_resolve_city(c) or c)

        return api_get(f"https://{api_host}/geo/v2/poi/lookup", params=params)

    @mcp.tool()
    def search_poi_range(
        location: str,
        poi_type: str,
        radius: int = 5,
        city: Optional[str] = None,
        page: int = 1,
        lang: str = "zh",
    ) -> Dict[str, Any]:
        """范围搜索 POI，按距离排序。

        Args:
            location: "经度,纬度" 坐标。
            poi_type: POI 类型，scenic（景点）或 TSTA（潮汐站点）。
            radius: 搜索半径（公里），1-50，默认 5。
            city: 限定城市（可选）。
            page: 页码，默认 1。
            lang: 语言，默认 "zh"。
        """
        if poi_type not in POI_TYPES:
            return {"code": "error", "error": f"Invalid poi_type: {poi_type}"}
        if not 1 <= radius <= 50:
            return {"code": "error", "error": f"Invalid radius: {radius}"}

        loc = location.strip()
        if "," not in loc:
            return {"code": "error", "error": "POI range search requires lon,lat coords"}
        try:
            lon, lat = [float(s) for s in loc.split(",", 1)]
            loc = f"{lon:.2f},{lat:.2f}"
        except Exception:
            return {"code": "error", "error": f"Bad coords: {loc}"}

        params: Dict[str, Any] = {
            "location": loc,
            "type": poi_type,
            "radius": str(radius),
            "page": str(page),
            "lang": lang,
        }
        if city and city.strip():
            c = city.strip()
            params["city"] = c if c.isdigit() else (_resolve_city(c) or c)

        return api_get(f"https://{api_host}/geo/v2/poi/range", params=params)
