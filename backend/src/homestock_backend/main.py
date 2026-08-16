"""Entrypoint to invoke FastAPI application service with."""
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, status, HTTPException

from homestock_backend.schemas import (
    HealthCheck,
    Space,
    SpaceRequest,
    SpacePatchRequest,
    SpaceListResponse
)
from homestock_backend.store import spaces

app = FastAPI()


# ============ HEALTH CHECK ROUTE ============
@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on.
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")

# ============ Spaces ROUTE ============
@app.get(
        "/spaces",
        tags=["spaces"],
        summary="Get all spaces",
        response_description="Return all available spaces",
        status_code=status.HTTP_200_OK,
        response_model=SpaceListResponse
    )
def get_all_spaces() -> SpaceListResponse:
    """
    ## Get all the Spaces
    Endpoint to get all spaces
    Returns:
        Space: Returns a SpaceListResponse
    """
    return SpaceListResponse(spaces=spaces)

@app.get(
        "/spaces/{space_id}",
        tags=["spaces"],
        summary="Get a space based on the space_id",
        response_description="Return a space based on the space_id",
        status_code=status.HTTP_200_OK,
        response_model=Space
    )
def get_a_space(space_id: str) -> Space:
    """
    ## Get a Space
    Endpoint to get a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    found_space = get_space_by_id(space_id)
    if found_space:
        return found_space

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Space {space_id} not found"
    )

@app.post(
        "/spaces",
        tags=["spaces"],
        summary="Create a new space",
        response_description="Return the newly create space",
        status_code=status.HTTP_201_CREATED,
        response_model=Space
    )
def create_a_space(payload: SpaceRequest) -> Space:
    """Create a new space with a server-assigned id."""
    space = Space(id=str(uuid4()), name=payload.name)
    spaces.append(space)
    return space


@app.patch(
        "/spaces/{space_id}",
        tags=["spaces"],
        summary="Patch a space based on the space_id",
        response_description="Return a space after patching",
        status_code=status.HTTP_200_OK,
        response_model=Space
    )
def patch_a_space(space_id: str, payload: SpacePatchRequest) -> Space:
    """
    ## Patch a Space
    Endpoint to patch a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    updates = payload.model_dump(exclude_unset=True, exclude_none=True)
    found_space = get_space_by_id(space_id)
    if found_space:
        for field, value in updates.items():
            setattr(found_space, field, value)
        return found_space

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Space {space_id} not found"
    )


@app.put(
        "/spaces/{space_id}",
        tags=["spaces"],
        summary="Put a space based on the space_id",
        response_description="Return a space after putting",
        status_code=status.HTTP_200_OK,
        response_model=Space
    )
def put_a_space(space_id: str, payload: SpaceRequest) -> Space:
    """
    ## Put a Space by Id
    Endpoint to put a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    found_space = get_space_by_id(space_id)
    if found_space:
        found_space.name = payload.name
        return found_space

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Space {space_id} not found"
    )


@app.delete(
        "/spaces/{space_id}",
        tags=["spaces"],
        summary="Delete a space based on the space_id",
        response_description="No content returned",
        status_code=status.HTTP_204_NO_CONTENT
    )
def delete_a_space(space_id: str) -> None:
    """
    ## Delete a Space
    Endpoint to get a singular space based on space_id
    """
    space_to_remove = get_space_by_id(space_id)

    if space_to_remove:
        spaces.remove(space_to_remove)
        return None

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Space {space_id} not found"
    )

# ============ Helper ============
def get_space_by_id(space_id: str) -> Optional[Space]:
    """
    Given the space_id, find the space.
    Return Space or None.
    """
    for space in spaces:
        if space.id == space_id:
            return space
    return None


# ============ Main ============
def main() -> None:
    """Entry point to invole when this module is invoked on the remote server."""
    uvicorn.run("homestock_backend.main:app", host="127.0.0.1", reload=True)


if __name__ == "__main__":
    main()
