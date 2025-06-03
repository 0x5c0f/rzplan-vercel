from sqlmodel import SQLModel,Field

class WorkFlowNodeInfo(SQLModel):
    node_input_name : str = Field(description="节点中 inputs 下的 key")
    node_input_value: str = Field(description="节点中 inputs 下的 value")

class ComfyUIWorkflow(SQLModel):
    id : int = Field(description="工作流 id")
    inputs: list[WorkFlowNodeInfo]
    
class ComfyUIWorkflowPublic(SQLModel):
    data: list[ComfyUIWorkflow]