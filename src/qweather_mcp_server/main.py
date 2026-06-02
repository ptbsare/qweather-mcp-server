"""qweather-mcp-server — entry point & CLI."""

import logging

import typer
from mcp.server.fastmcp import FastMCP

from qweather_mcp_server.core.config import api_host, api_key, project_id, key_id
from qweather_mcp_server.tools.air import register_air_tools
from qweather_mcp_server.tools.geo import register_geo_tools
from qweather_mcp_server.tools.grid import register_grid_tools
from qweather_mcp_server.tools.weather import register_weather_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("qweather_mcp_server")

# ------------------------------------------------------------------ #
#  MCP server instance & tool registration
# ------------------------------------------------------------------ #
mcp = FastMCP("qweather_mcp_server")

register_weather_tools(mcp)
register_air_tools(mcp)
register_grid_tools(mcp)
register_geo_tools(mcp)

# ------------------------------------------------------------------ #
#  CLI
# ------------------------------------------------------------------ #
app = typer.Typer()


@app.command()
def http() -> None:
    """Start MCP server in HTTP (streamable-http) mode."""
    logger.info("Starting qweather-mcp-server …")
    logger.info(f"API host: {api_host}")
    if api_key:
        logger.info(f"API key: {api_key[:10]}…")
    else:
        logger.info(f"Project: {project_id}, Key: {key_id}")
    mcp.run(transport="streamable-http")


@app.command()
def stdio() -> None:
    """Start MCP server in STDIO mode."""
    logger.info("Starting qweather-mcp-server (stdio) …")
    logger.info(f"API host: {api_host}")
    mcp.run(transport="stdio")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
