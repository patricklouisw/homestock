from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from homestock_backend.repositories.space_repository import SpaceRepository
from homestock_backend.schemas.space import SpaceRequest, SpacePatchRequest
from homestock_backend.models.space import Space

class SpaceService():
    def __init__(self, db: Session, repository:SpaceRepository) -> None:
        self.db = db
        self.repository = repository

    def create_space(self, payload: SpaceRequest) -> Space:
        space = self.repository.create(name=payload.name)
        self.db.commit()
        self.db.refresh(space)
        return space

    def get_all_spaces(self, limit, offset) -> list[Space]:
        return self.repository.get_all(limit, offset)

    def count_all_spaces(self) -> int:
        return self.repository.count_all()

    def get_space_by_id(self, space_id: str) -> Space:
        space = self.repository.get_by_id(space_id)

        if space is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found"
            )

        return space

    def patch_space_by_id(self, space_id:str, payload:SpacePatchRequest) -> Space:
        space = self.repository.update(
            space_id,
            **payload.model_dump(exclude_unset=True, exclude_none=True)
        )
        if space is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found"
            )
        self.db.commit()
        self.db.refresh(space)
        return space


    def put_space_by_id(self, space_id:str, payload:SpaceRequest) -> Space:
        space = self.repository.update(space_id, **payload.model_dump())
        if space is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found"
            )
        self.db.commit()
        self.db.refresh(space)
        return space


    def delete_space_by_id(self, space_id:str) -> None:
        if not self.repository.delete(space_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        self.db.commit()
        return None