from sqlmodel import SQLModel,Field

class WorkFlowNodeInfo(SQLModel):
    """工作流 inputs 节点信息"""
    node_input_key : str = Field(description="节点中 inputs 下的 key")
    node_input_value: str = Field(description="节点中 inputs 下的 value")

class ComfyUIWorkflow(SQLModel):
    """工作流 inputs 节点组信息"""
    node_id : int = Field(description="工作流 id")
    inputs: list[WorkFlowNodeInfo]
    
class ComfyUIWorkflowPublic(SQLModel):
    """工作流节点组信息"""
    data: list[ComfyUIWorkflow]