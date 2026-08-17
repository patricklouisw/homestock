"""Entrypoint to invoke FastAPI application service with."""
import uvicorn
from fastapi import FastAPI, status

from homestock_backend.schemas.health_check import HealthCheck
from homestock_backend.api.routes import spaces

app = FastAPI(
    title="Home Inventory App",
    version="1.0.0",
)

app.include_router(
    spaces.router,
    prefix="/api/v1/spaces",
    tags=["Spaces"]
)

# ============ HEALTH CHECK ROUTE ============
@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck
)
def health_check() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on.
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")

# ============ Main ============
def main() -> None:
    """Entry point to invole when this module is invoked on the remote server."""
    uvicorn.run("homestock_backend.main:app", host="127.0.0.1", reload=True)


if __name__ == "__main__":
    main()
