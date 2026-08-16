"""Pydantic schemas for request and response bodies."""

from typing import Annotated, Optional

from pydantic import BaseModel, Field


class HealthCheck(BaseModel):
    """Response model returned by the health check endpoint."""
    status: str = "OK"


class Space(BaseModel):
    """Response model for a single Space."""
    id: str
    name: str


class SpaceRequest(BaseModel):
    """Request model for a Space. The server assigns the id."""
    name: str = Field(min_length=1, max_length=100)


class SpacePatchRequest(BaseModel):
    """Patch Request model for a Space. The server assigns the id."""
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None


class SpaceListResponse(BaseModel):
    """Response model for a collection of Spaces."""
    spaces: list[Space]
