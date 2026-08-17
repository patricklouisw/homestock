from fastapi import APIRouter, Depends, status, Query

from homestock_backend.schemas.space import (
    SpaceResponse,
    SpaceRequest,
    SpacePatchRequest,
    SpaceListResponse
)
from homestock_backend.models.space import Space
from homestock_backend.services.space_service import SpaceService
from homestock_backend.api.dependencies import get_space_service

router = APIRouter()

@router.get(
    "",
    summary="Get all spaces",
    response_description="Return all available spaces",
    status_code=status.HTTP_200_OK,
    response_model=SpaceListResponse
)
def get_all_spaces(
    limit:int = Query(50, ge=1, le=100),
    offset:int = Query(0, ge=0),
    service: SpaceService = Depends(get_space_service)
    ) -> SpaceListResponse:
    """
    ## Get all the Spaces
    Endpoint to get all spaces
    Returns:
        Space: Returns a SpaceListResponse
    """
    all_spaces = service.get_all_spaces(limit, offset)
    count_all = service.count_all_spaces()
    return SpaceListResponse(
        spaces=[SpaceResponse.model_validate(space) for space in all_spaces],
        total=count_all
    )


@router.get(
        "/{space_id}",
        summary="Get a space based on the space_id",
        response_description="Return a space based on the space_id",
        status_code=status.HTTP_200_OK,
        response_model=SpaceResponse
    )
def get_a_space(space_id: str, service: SpaceService = Depends(get_space_service)) -> Space:
    """
    ## Get a Space
    Endpoint to get a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    return service.get_space_by_id(space_id)


@router.post(
        "",
        summary="Create a new space",
        response_description="Return the newly create space",
        status_code=status.HTTP_201_CREATED,
        response_model=SpaceResponse
    )
def create_a_space(
    payload: SpaceRequest,
    service: SpaceService = Depends(get_space_service)
    ) -> Space:
    """Create a new space with a server-assigned id."""
    return service.create_space(payload)


@router.patch(
        "/{space_id}",
        summary="Patch a space based on the space_id",
        response_description="Return a space after patching",
        status_code=status.HTTP_200_OK,
        response_model=SpaceResponse
    )
def patch_a_space(space_id: str, payload: SpacePatchRequest, service: SpaceService=Depends(get_space_service)) -> Space:
    """
    ## Patch a Space
    Endpoint to patch a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    return service.patch_space_by_id(space_id=space_id, payload=payload)

@router.put(
        "/{space_id}",
        summary="Put a space based on the space_id",
        response_description="Return a space after putting",
        status_code=status.HTTP_200_OK,
        response_model=SpaceResponse
    )
def put_a_space(space_id: str, payload: SpaceRequest, service: SpaceService = Depends(get_space_service)) -> Space:
    """
    ## Put a Space by Id
    Endpoint to put a singular space based on space_id
    Returns:
        Space: Returns a JSON response with Space
    """
    return service.put_space_by_id(space_id=space_id, payload=payload)


@router.delete(
        "/{space_id}",
        summary="Delete a space based on the space_id",
        response_description="No content returned",
        status_code=status.HTTP_204_NO_CONTENT
    )
def delete_a_space(space_id: str, service: SpaceService = Depends(get_space_service)) -> None:
    """
    ## Delete a Space
    Endpoint to get a singular space based on space_id
    """
    return service.delete_space_by_id(space_id=space_id)
