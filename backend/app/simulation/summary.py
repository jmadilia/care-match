from app.schemas.simulation_run import PopulationSummary
from app.simulation.generator import Population


def summarize_population(population: Population) -> PopulationSummary:
    """Describe how hard the marketplace is: unservable share, eligibility spread, state balance."""
    raise NotImplementedError
