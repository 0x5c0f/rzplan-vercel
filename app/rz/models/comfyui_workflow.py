from sqlmodel import SQLModel,Field

from pydantic import ConfigDict

from app.core.config import settings

from uuid import UUID

class ComfyUIServer(SQLModel):
    """工作流服务器信息"""
    server_host: str = Field(alias="comfyui_server_host",description="服务器名称", default=settings.COMFYUI_SERVER_HOST)
    server_port: str = Field(alias="comfyui_server_port",description="服务器端口", default=settings.COMFYUI_SERVER_PORT) 
    
    model_config = ConfigDict(extra='forbid')

class WorkFlowNodeInput(SQLModel):
    """工作流 inputs 节点信息"""
    node_input_key : str = Field(description="节点中 inputs 下的 key")
    node_input_value: str = Field(description="节点中 inputs 下的 value")

class WorkFlowNodeInputs(SQLModel):
    """工作流 inputs 节点组信息"""
    node_id : int = Field(description="工作流 id")
    inputs: list[WorkFlowNodeInput]
    
# class WorkFlowNode(SQLModel):
#     """工作流节点组信息"""
#     data: list[WorkFlowNodeInputs]

class WorkFlowImageUploadPublic(SQLModel):
    """工作流图片上传"""
    server_info: ComfyUIServer = Field(alias="server_info",description="服务器信息", default_factory=ComfyUIServer)

class WorkFlowNodePublic(SQLModel):
    """工作流队列提交内容"""
    server_info: ComfyUIServer = Field(alias="server_info",description="服务器信息", default_factory=ComfyUIServer)
    node_info: list[WorkFlowNodeInputs] = Field(description="节点信息",default_factory=list)

class ComfyUITaskPublic(SQLModel):
    """工作流任务提交内容"""
    task_id: UUID = Field(...,alias="task_id",description="任务 id",default_factory=UUID)
    server_info: ComfyUIServer = Field(alias="server_info",description="服务器信息", default_factory=ComfyUIServer)