from fastapi import APIRouter

router = APIRouter(prefix="/mcp", tags=["mcp_tools"])

@router.get("/list",operation_id="list_mcp_operations", summary="查询当前 MCP 可用的接口")
async def list_mcp_operations():
    """
    查询当前 MCP 可用的接口有哪些  
    
    Returns:
    ```json
    [
        {
            "url": "/mcp/info",                                     # 接口地址
            "tools": [                                              # 可用的工具列表
                {
                    "name": "list_mcp",                             # 工具名称
                    "description": "查询当前 MCP 可用的接口有哪些." # 工具描述
                }
            ]
        }
    ]
    ```
    """
    result = []
    utils = {
        "url": "/mcp/list",
        "tools": [
            {
                "name": "list_mcp",
                "description": "查询当前 MCP 可用的接口有哪些.",
            },
            {
                "name": "resolve_domain",
                "description": "解析域名并获取其 IP 地址信息",
            }
        ]
    }
    
    result.append(utils)
    
    return result