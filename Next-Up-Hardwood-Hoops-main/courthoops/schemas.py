from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class UniverseConfigSchema(BaseModel):
    database_url: str = Field(default="sqlite:///courthoops.db")
    universe_id: str = Field(default="UNIVERSE")
    world_id: Optional[str] = None


class SaveSlotSchema(BaseModel):
    save_id: str
    universe_id: str
    name: Optional[str] = None
    world_id: Optional[str] = None
    created_at: Optional[str] = None
    last_played_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
