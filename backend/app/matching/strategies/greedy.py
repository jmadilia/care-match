import uuid

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.matching.candidates import rank_candidates
from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.metrics import provider_utilization_std
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.schemas.match import MatchStatus
from app.schemas.strategy_run import StrategyRunSummary

STRATEGY_NAME = "greedy"


def run_greedy(db: Session, run_id: uuid.UUID) -> StrategyRunSummary:
  """First-come-first-served: clients in arrival order each take their best eligible,
  available provider. No lookahead, so an early client can take a slot a later,
  better-fitting client needed. That's the baseline the other strategies are compared against.

  Raises StrategyAlreadyRunError if this strategy already has matches for this run.
  """
  already_run = db.scalar(
    select(
      exists().where(
        Match.strategy == STRATEGY_NAME,
        Match.client_id.in_(select(Client.id).where(Client.simulation_run_id == run_id)),
      )
    )
  )
  if already_run:
    raise StrategyAlreadyRunError

  clients = list(
    db.scalars(
      select(Client)
      .where(Client.simulation_run_id == run_id)
      .order_by(Client.arrival_day, Client.created_at)
    )
  )
  providers = list(db.scalars(select(Provider).where(Provider.simulation_run_id == run_id)))
  remaining_capacity = {provider.id: provider.weekly_capacity for provider in providers}

  matched_count = 0
  scores: list[float] = []
  for client in clients:
    candidates = rank_candidates(
      client, [(provider, remaining_capacity[provider.id]) for provider in providers]
    )
    if not candidates:
      continue

    best = candidates[0]
    remaining_capacity[best.provider.id] -= 1
    db.add(
      Match(
        client_id=client.id,
        provider_id=best.provider.id,
        strategy=STRATEGY_NAME,
        score=best.score,
        status=MatchStatus.PROPOSED.value,
      )
    )
    matched_count += 1
    scores.append(best.score)

  db.commit()

  client_count = len(clients)
  matched_count_by_provider = {
    provider.id: provider.weekly_capacity - remaining_capacity[provider.id]
    for provider in providers
  }
  return StrategyRunSummary(
    strategy=STRATEGY_NAME,
    client_count=client_count,
    matched_count=matched_count,
    unmatched_count=client_count - matched_count,
    fill_rate=round(matched_count / client_count, 4) if client_count else 0.0,
    mean_match_score=round(sum(scores) / len(scores), 4) if scores else 0.0,
    provider_utilization_std=provider_utilization_std(providers, matched_count_by_provider),
  )
