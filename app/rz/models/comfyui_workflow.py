from sqlmodel import SQLModel,Field

class WorkFlowNodeInput(SQLModel):
    """工作流 inputs 节点信息"""
    node_input_key : str = Field(description="节点中 inputs 下的 key")
    node_input_value: str = Field(description="节点中 inputs 下的 value")

class WorkFlowNodeInputs(SQLModel):
    """工作流 inputs 节点组信息"""
    node_id : int = Field(description="工作流 id")
    inputs: list[WorkFlowNodeInput]
    
class WorkFlowNode(SQLModel):
    """工作流节点组信息"""
    data: list[WorkFlowNodeInputs]