from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun
from app.schemas.simulation_run import PopulationSummary
from app.simulation.config import ScenarioName, get_scenario
from app.simulation.generator import generate_population
from app.simulation.summary import summarize_population


class RunAlreadyGeneratedError(Exception):
    pass


def generate_for_run(db: Session, run: SimulationRun) -> PopulationSummary:
    """Generate the run's population, bulk-insert it, and return its summary.

    Raises RunAlreadyGeneratedError if the run already has clients or providers.
    """
    has_clients = db.scalar(select(exists().where(Client.simulation_run_id == run.id)))
    has_providers = db.scalar(select(exists().where(Provider.simulation_run_id == run.id)))
    if has_clients or has_providers:
        raise RunAlreadyGeneratedError

    config = get_scenario(ScenarioName(run.scenario))
    population = generate_population(run.seed, run.provider_count, run.client_count, config)

    db.add_all(
        Provider(
            name=provider.name,
            license_states=provider.license_states,
            specialties=provider.specialties,
            modalities=provider.modalities,
            languages=provider.languages,
            insurance_panels=provider.insurance_panels,
            weekly_capacity=provider.weekly_capacity,
            simulation_run_id=run.id,
        )
        for provider in population.providers
    )
    db.add_all(
        Client(
            name=client.name,
            state=client.state,
            insurance_payer=client.insurance_payer,
            needed_specialties=client.needed_specialties,
            preferred_modality=client.preferred_modality,
            preferred_language=client.preferred_language,
            urgency=client.urgency.value,
            arrival_day=client.arrival_day,
            simulation_run_id=run.id,
        )
        for client in population.clients
    )
    db.commit()
    return summarize_population(population)
