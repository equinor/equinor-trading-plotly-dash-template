from typing import List

from pydantic import BaseModel
from pydantic.fields import Field


class Role(BaseModel):
    allowed_member_types: List[str] = Field(alias="allowedMemberTypes")
    description: str
    display_name: str = Field(alias="displayName")
    id: str
    is_enabled: bool = Field(alias="isEnabled")
    origin: str
    value: str


class DeployConfig(BaseModel):
    roles: List[Role]
    redirect_path: str = Field(alias="redirectPath")
