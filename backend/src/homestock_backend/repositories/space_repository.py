from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from homestock_backend.models.space import Space

class SpaceRepository():
    def __init__(self, db: Session) -> None:
        self.db = db


    def get_all(
            self,
            limit: int,
            offset: int
            ) -> list[Space]:
        stmt = select(Space).limit(limit).offset(offset)
        return list(self.db.scalars(stmt).all())


    def count_all(self) -> int:
        count = self.db.scalar(select(func.count(Space.id)))
        return count if count is not None else 0


    def get_by_id(self, space_id: str) -> Space | None:
        return self.db.get(Space, space_id)


    def create(self, name: str) -> Space:
        new_space = Space(name=name)

        self.db.add(new_space)
        self.db.flush()  # Pushes to DB so constraints/IDs generate, but doesn't commit yet

        return new_space


    def update(self, space_id: str, **kwargs: Any) -> Space | None:
        found_space = self.get_by_id(space_id)

        if found_space is None:
            return None

        # Loop through dictionary items and update attributes dynamically
        for key, value in kwargs.items():
            setattr(found_space, key, value)

        self.db.flush()  # Syncs memory changes down to the database transaction
        return found_space


    def delete(self, space_id:str) -> bool:
        space = self.get_by_id(space_id=space_id)

        if space is None:
            return False

        self.db.delete(space)
        self.db.flush()

        return True