import uuid
from collections import deque

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.matching.candidates import Candidate, rank_candidates
from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.metrics import fill_rate_by_urgency, provider_utilization_std
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.schemas.match import MatchStatus
from app.schemas.strategy_run import StrategyRunSummary

STRATEGY_NAME = "stable_matching"
_UNLIMITED = 10**9


def run_stable_matching(db: Session, run_id: uuid.UUID) -> StrategyRunSummary:
  """Gale-Shapley deferred acceptance (client-proposing, many-to-one): each free client
  proposes to their best remaining eligible provider; a provider holds its best proposals
  up to capacity and bumps anyone it prefers less when a stronger proposal arrives, who
  then proposes elsewhere. No stated provider preferences exist in this system, so a
  provider ranks clients by the same fit score clients use to rank providers, a mutual
  compatibility score rather than one-sided preferences. The result is stable with respect
  to that shared ranking: no client-provider pair would both rather be matched to each other
  than to their current outcome.

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
      .order_by(Client.arrival_day, Client.name)
    )
  )
  providers = list(
    db.scalars(
      select(Provider).where(Provider.simulation_run_id == run_id).order_by(Provider.name)
    )
  )

  # Preference lists are fixed up front: eligibility and score don't change as capacity
  # fills up, only who's still free to be proposed to does.
  preferences: dict[uuid.UUID, list[Candidate[Provider]]] = {
    client.id: rank_candidates(client, [(provider, _UNLIMITED) for provider in providers])
    for client in clients
  }
  next_choice = dict.fromkeys(preferences, 0)
  holds: dict[uuid.UUID, list[tuple[Client, float]]] = {provider.id: [] for provider in providers}
  capacity = {provider.id: provider.weekly_capacity for provider in providers}

  free_clients = deque(client for client in clients if preferences[client.id])
  while free_clients:
    client = free_clients.popleft()
    choices = preferences[client.id]
    if next_choice[client.id] >= len(choices):
      continue  # exhausted every eligible provider; stays unmatched

    candidate = choices[next_choice[client.id]]
    next_choice[client.id] += 1
    provider_holds = holds[candidate.provider.id]

    if len(provider_holds) < capacity[candidate.provider.id]:
      provider_holds.append((client, candidate.score))
    elif candidate.score > provider_holds[-1][1]:
      bumped_client, _ = provider_holds[-1]
      provider_holds[-1] = (client, candidate.score)
      free_clients.append(bumped_client)
    else:
      free_clients.append(client)
      continue

    provider_holds.sort(key=lambda held: held[1], reverse=True)

  matched_count = 0
  scores: list[float] = []
  matched_client_ids: set[uuid.UUID] = set()
  for provider_id, provider_holds in holds.items():
    for client, score in provider_holds:
      db.add(
        Match(
          client_id=client.id,
          provider_id=provider_id,
          strategy=STRATEGY_NAME,
          score=score,
          status=MatchStatus.PROPOSED.value,
        )
      )
      matched_count += 1
      scores.append(score)
      matched_client_ids.add(client.id)

  db.commit()

  client_count = len(clients)
  matched_count_by_provider = {provider_id: len(held) for provider_id, held in holds.items()}
  return StrategyRunSummary(
    strategy=STRATEGY_NAME,
    client_count=client_count,
    matched_count=matched_count,
    unmatched_count=client_count - matched_count,
    fill_rate=round(matched_count / client_count, 4) if client_count else 0.0,
    mean_match_score=round(sum(scores) / len(scores), 4) if scores else 0.0,
    provider_utilization_std=provider_utilization_std(providers, matched_count_by_provider),
    fill_rate_by_urgency=fill_rate_by_urgency(clients, matched_client_ids),
  )
