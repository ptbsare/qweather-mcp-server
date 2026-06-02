# 和风天气 MCP 服务 (qweather-mcp-server)

基于 Model Context Protocol (MCP) 的和风天气服务，提供天气预报、气象预警、空气质量、历史数据、天文信息等气象数据查询功能。

## 快速开始

使用 `uvx` 直接运行（无需安装）：

```bash
HEFENG_API_HOST=你的API主机地址 HEFENG_API_KEY=你的API密钥 uvx --from git+https://github.com/ptbsare/qweather-mcp-server.git qweather-mcp-server stdio
```

## 配置

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `HEFENG_API_HOST` | ✅ | - | API 主机地址 |
| `HEFENG_API_KEY` | ✅* | - | API KEY |
| `HEFENG_PROJECT_ID` | - | - | 项目 ID（JWT 模式） |
| `HEFENG_KEY_ID` | - | - | 凭据 ID（JWT 模式） |
| `HEFENG_PRIVATE_KEY_PATH` | - | - | 私钥文件路径（JWT 模式） |
| `HEFENG_MAX_RETRIES` | - | 3 | 最大重试次数 |
| `HEFENG_CACHE_TTL` | - | 600 | 城市缓存 TTL（秒） |

*API KEY 和 JWT 认证二选一，推荐 API KEY。

### 客户端配置

```json
{
  "qweather-mcp-server": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/ptbsare/qweather-mcp-server.git", "qweather-mcp-server", "stdio"],
    "env": {
      "HEFENG_API_HOST": "你的API主机地址",
      "HEFENG_API_KEY": "你的API密钥"
    }
  }
}
```

## 数据覆盖

覆盖和风天气 API 以下全部数据类别（不含海洋和热带气旋）：

### 天气类

| 数据项目 | MCP 工具 | 时间范围 | 地理范围 |
|---|---|---|---|
| 实况天气 | `get_weather_now` | 实时 | 全球 |
| 逐天预报 | `get_weather` | 1-30天 | 全球 |
| 逐小时预报 | `get_hourly_weather` | 1-168小时 | 全球 |
| 格点实况天气 | `get_grid_weather_now` | 实时 | 全球 |
| 格点逐天预报 | `get_grid_weather_daily` | 1-7天 | 全球 |
| 格点逐小时预报 | `get_grid_weather_hourly` | 1-72小时 | 全球 |
| 分钟级降水 | `get_minutely_5m` | 1-2小时 | 中国 |

### 天气指数

| 数据项目 | MCP 工具 |
|---|---|
| 16种生活指数 | `get_indices` |

### 空气类

| 数据项目 | MCP 工具 | 时间范围 | 地理范围 |
|---|---|---|---|
| 空气质量实况 | `get_air_quality` | 实时 | 全球 |
| 空气质量每日预报 | `get_air_quality_daily` | 1-7天 | 全球 |
| 空气质量每小时预报 | `get_air_quality_hourly` | 1-72小时 | 全球 |
| 监测站数据 | `get_air_quality_stations` | 实时 | 全球 |

### 预警类

| 数据项目 | MCP 工具 |
|---|---|
| 灾害预警 | `get_warning` |

### 天文类

| 数据项目 | MCP 工具 | 时间范围 |
|---|---|---|
| 日出日落时间 | `get_astronomy_sun` | 1-60天 |
| 月升月落时间/月相 | `get_astronomy_moon` | 1-60天 |

### 时光机（历史数据）

| 数据项目 | MCP 工具 | 时间范围 |
|---|---|---|
| 历史天气 | `get_weather_history` | 最多10天 |
| 历史空气质量 | `get_air_quality_history` | 最多10天 |

### GeoAPI

| 数据项目 | MCP 工具 |
|---|---|
| 热门城市 | `get_top_cities` |
| POI关键词搜索 | `search_poi` |
| POI范围搜索 | `search_poi_range` |

## MCP 工具

### get_weather_now - 实时天气

```
get_weather_now(city="北京")
get_weather_now(location="101010100")
```

### get_weather - 逐天预报

```
get_weather("北京", "3d")
get_weather("上海", "7d")
```

### get_hourly_weather - 逐小时预报

```
get_hourly_weather(hours="24h", city="北京")
get_hourly_weather(hours="72h", city="上海")
```

### get_minutely_5m - 分钟级降水

```
get_minutely_5m("北京")
get_minutely_5m("116.41,39.92")
```

### get_warning - 气象预警

```
get_warning("北京")
```

### get_indices - 生活指数

```
get_indices("北京")
get_indices("上海", "3d")
get_indices("广州", "1d", "1,2,3")
```

指数类型：1-运动 2-洗车 3-穿衣 4-感冒 5-紫外线 6-旅游 7-过敏 8-舒适度 9-交通 10-防晒 11-化妆 12-空调 13-晾晒 14-钓鱼 15-太阳镜 16-空气污染扩散

### get_astronomy_sun - 日出日落

```
get_astronomy_sun("北京", "20260615")
```

### get_astronomy_moon - 月相月升月落

```
get_astronomy_moon("北京", "20260615")
```

### get_air_quality - 实时空气质量

```
get_air_quality("北京")
```

### get_air_quality_hourly - 空气质量小时预报

```
get_air_quality_hourly("39.92,116.41", "24h")
```

### get_air_quality_daily - 空气质量每日预报

```
get_air_quality_daily("39.92,116.41", "3d")
```

### get_air_quality_stations - 监测站数据

```
get_air_quality_stations("P58911")
```

### get_air_quality_history - 历史空气质量

```
get_air_quality_history("北京", days=3)
```

### get_grid_weather_now - 格点实时天气

```
get_grid_weather_now("116.41,39.92")
```

### get_grid_weather_daily - 格点每日预报

```
get_grid_weather_daily("116.41,39.92", "3d")
```

### get_grid_weather_hourly - 格点逐小时预报

```
get_grid_weather_hourly("116.41,39.92", "24h")
```

### get_weather_history - 历史天气

```
get_weather_history(city="北京", days=7)
```

### get_top_cities - 热门城市

```
get_top_cities(10, "cn")
```

### search_poi - POI关键词搜索

```
search_poi("北京", "故宫", "scenic")
search_poi("116.41,39.92", "博物馆", "scenic", radius=5000)
```

### search_poi_range - POI范围搜索

```
search_poi_range("116.41,39.92", "scenic", radius=5)
```

## 项目结构

```
qweather-mcp-server/
├── pyproject.toml
├── LICENSE
├── README.md
├── .env.example
└── src/qweather_mcp_server/
    ├── __init__.py
    ├── main.py
    ├── core/
    │   ├── config.py
    │   ├── http.py
    │   └── cache.py
    ├── tools/
    │   ├── weather.py
    │   ├── air.py
    │   ├── grid.py
    │   └── geo.py
    └── utils/
```

## 相关链接

- [和风天气官网](https://www.qweather.com/)
- [和风天气开发者控制台](https://console.qweather.com/project/)
- [和风天气 API 文档](https://dev.qweather.com/docs/api/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

## 许可证

GPL-3.0
