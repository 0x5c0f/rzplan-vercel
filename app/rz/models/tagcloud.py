from pydantic import BaseModel, Field

class TagCloudData(BaseModel):
    tag: str
    count: int = Field(..., gt=0)

class TagCloudPublic(BaseModel):
    font: str = Field(default="msyhl")
    width: int = Field(default=800)
    height: int = Field(default=400)
    background_color: str = Field(default="white")
    
    tags: list[TagCloudData]