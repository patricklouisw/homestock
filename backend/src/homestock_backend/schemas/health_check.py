from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Response model returned by the health check endpoint."""
    status: str = "OK"