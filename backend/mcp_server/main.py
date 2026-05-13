from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from mcp_server.tools.base import DataSourceAdapter


app = Server("financial-data-server")


@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_index_data",
            description="获取股票指数历史数据，支持沪深300、创业板指等",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "指数代码，如 sh000300"},
                    "period": {"type": "string", "description": "时间周期，如 1y, 3y, 5y"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_fund_rating",
            description="获取基金评级和历史业绩数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "fund_id": {"type": "string", "description": "基金代码"}
                },
                "required": ["fund_id"]
            }
        ),
        Tool(
            name="get_macro_indicator",
            description="获取宏观经济指标数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "description": "指标名称，如 CPI, PMI, GDP"}
                },
                "required": ["indicator"]
            }
        ),
        Tool(
            name="get_bond_yield",
            description="获取债券收益率曲线数据",
            inputSchema={
                "type": "object",
                "properties": {
                    "curve_type": {"type": "string", "description": "曲线类型，如 china, us"}
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    # 工具调用逻辑将在下一个任务实现
    return [TextContent(type="text", text=f"Tool {name} called with {arguments}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
