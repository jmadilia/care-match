# Import every model module here so `Base.metadata` sees all tables.
# Alembic autogenerate relies on this for detecting schema changes.
from app.models.provider import Provider  # noqa: F401
