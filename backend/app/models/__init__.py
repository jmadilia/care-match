# Import every model module here so `Base.metadata` sees all tables —
# Alembic autogenerate relies on this for detecting schema changes.
from app.models.item import Item  # noqa: F401
