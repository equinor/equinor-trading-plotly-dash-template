from typing import List, Optional
from pydantic import BaseModel


class AppSettings(BaseModel):
    client_id: str
    authority: str
    secret_name: str
    is_prod: Optional[str]
    redirect_path: str
    storage_name: str
    roles: List[str]