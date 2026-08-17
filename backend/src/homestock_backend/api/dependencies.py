from fastapi import Depends

from sqlalchemy.orm import Session

from homestock_backend.database.session import get_db
from homestock_backend.repositories.space_repository import SpaceRepository
from homestock_backend.services.space_service import SpaceService

def get_space_service(
    db: Session = Depends(get_db)
) -> SpaceService:
    repository = SpaceRepository(db=db)
    return SpaceService(
        db=db,
        repository=repository)
