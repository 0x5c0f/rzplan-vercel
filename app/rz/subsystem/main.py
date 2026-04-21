from fastapi_mcp import FastApiMCP
from fastapi import FastAPI

from app.core.config import settings

def register_mcp_server(app: FastAPI):
    """
    Register the MCP server with the FastAPI app.
    """
    mcp = FastApiMCP(
        app,
        name=f"{settings.PROJECT_NAME} API MCP",
        description=f"MCP server for the {settings.PROJECT_NAME} API",
        include_operations=["list_mcp_operations"],
    )

    mcp.mount_http(mount_path=f"{settings.API_V1_STR}/mcp/http")
    
    # all = FastApiMCP(
    #     app,
    #     name=f"{settings.PROJECT_NAME} API MCP",
    #     description=f"MCP server for the {settings.PROJECT_NAME} API",
    # )
    
    # all.mount_http(mount_path="/mcp/all")
