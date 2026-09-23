# Import every model module here so `Base.metadata` sees all tables.
# Alembic autogenerate relies on this for detecting schema changes.
from app.models.client import Client  # noqa: F401
from app.models.match import Match  # noqa: F401
from app.models.provider import Provider  # noqa: F401
from app.models.simulation_run import SimulationRun  # noqa: F401
from app.models.waitlist_entry import WaitlistEntry  # noqa: F401
