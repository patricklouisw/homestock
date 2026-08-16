"""In-memory storage for spaces."""

from homestock_backend.schemas import Space

spaces: list[Space] = [
    Space(id="1", name="Kitchen"),
    Space(id="2", name="Living Room"),
]
