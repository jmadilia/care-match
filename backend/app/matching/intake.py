from app.db.scratch import scratch_session
from app.matching.service import recommend_candidates
from app.models.client import Client
from app.models.simulation_run import SimulationRun
from app.schemas.client import ClientUrgency
from app.schemas.intake import IntakeRequest, IntakeResult
from app.simulation.service import generate_for_run

POOL_PROVIDERS = 20
POOL_CLIENTS = 100


def find_candidates(request: IntakeRequest) -> IntakeResult:
  """Rank a generated provider pool for one client's answers, then discard everything.

  The pool is a pure function of (scenario, seed), so the same request always returns the same
  candidates, and the whole thing happens in a scratch session that is always rolled back:
  visitors never write a row. The client is created inside the pool's run only so the existing
  recommend_candidates path (which scopes providers to the client's run) can be reused as is.
  """
  with scratch_session() as db:
    run = SimulationRun(
      name="intake",
      scenario=request.scenario,
      seed=request.seed,
      provider_count=POOL_PROVIDERS,
      client_count=POOL_CLIENTS,
    )
    db.add(run)
    db.flush()
    generate_for_run(db, run)

    client = Client(
      name="intake",
      state=request.state,
      insurance_payer=request.insurance_payer,
      needed_specialties=request.needed_specialties,
      preferred_modality=request.preferred_modality,
      preferred_language=request.preferred_language,
      urgency=ClientUrgency.ROUTINE.value,
      arrival_day=0,
      simulation_run_id=run.id,
    )
    db.add(client)
    db.flush()

    candidates = recommend_candidates(db, client, None, request.limit)

  return IntakeResult(
    scenario=request.scenario,
    seed=request.seed,
    pool_provider_count=POOL_PROVIDERS,
    candidates=candidates,
  )
