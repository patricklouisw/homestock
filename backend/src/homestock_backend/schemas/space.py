"""Pydantic schemas for request and response for Space."""
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict


class SpaceRequest(BaseModel):
    """Request model for a Space. The server assigns the id."""
    name: str = Field(min_length=1, max_length=100)


class SpaceResponse(BaseModel):
    """Response model for a single Space."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str


class SpacePatchRequest(BaseModel):
    """Patch Request model for a Space. The server assigns the id."""
    name: Annotated[str, Field(min_length=1, max_length=100)] | None = None


class SpaceListResponse(BaseModel):
    """Response model for a collection of Spaces."""
    spaces: list[SpaceResponse]
    total: int
