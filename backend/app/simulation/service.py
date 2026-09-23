from sqlalchemy.orm import Session

from app.models.simulation_run import SimulationRun
from app.schemas.simulation_run import PopulationSummary


class RunAlreadyGeneratedError(Exception):
    pass


def generate_for_run(db: Session, run: SimulationRun) -> PopulationSummary:
    """Generate the run's population, bulk-insert it, and return its summary.

    Raises RunAlreadyGeneratedError if the run already has clients or providers.
    """
    raise NotImplementedError
