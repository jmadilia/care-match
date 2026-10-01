import uuid

import numpy as np
from scipy.optimize import linear_sum_assignment
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.matching.constraints import is_eligible
from app.matching.scoring import score_pair
from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.metrics import provider_utilization_std
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.schemas.match import MatchStatus
from app.schemas.strategy_run import StrategyRunSummary

STRATEGY_NAME = "optimal"
_INELIGIBLE_COST = 1_000.0


def run_optimal(db: Session, run_id: uuid.UUID) -> StrategyRunSummary:
  """Globally optimal assignment: maximizes total match score across the whole batch at
  once, via the Hungarian algorithm (scipy's linear_sum_assignment), rather than deciding
  client by client like greedy or proposal by proposal like stable matching.

  linear_sum_assignment only solves one-to-one assignment, so a provider's weekly_capacity
  becomes that many identical "slot" columns, turning many-to-one into plain one-to-one.
  Each client also gets a zero-cost "stay unmatched" column so the solver can leave a
  client unmatched rather than being forced into an ineligible slot (which is costed high
  enough to only ever be chosen if every dummy column were somehow gone, which never
  happens since there's always one dummy per client).

  This is the ceiling the other two strategies are measured against: no reassignment of
  the whole batch could score higher. It says nothing about fairness or wait time, and it
  only makes sense as a batch operation with the whole population known up front, not
  something a real system could run online as clients arrive one at a time.

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
  providers = list(
    db.scalars(
      select(Provider).where(Provider.simulation_run_id == run_id).order_by(Provider.created_at)
    )
  )

  client_count = len(clients)
  slot_ranges: list[tuple[int, int]] = []
  cursor = 0
  for provider in providers:
    slot_ranges.append((cursor, cursor + provider.weekly_capacity))
    cursor += provider.weekly_capacity
  total_real_slots = cursor
  slot_providers = [provider for provider in providers for _ in range(provider.weekly_capacity)]

  # One dummy "stay unmatched" column per client: always enough that the solver never has
  # to force a client into an ineligible slot just because every column is taken.
  cost_matrix = np.zeros((client_count, total_real_slots + client_count))
  for i, client in enumerate(clients):
    for provider, (start, end) in zip(providers, slot_ranges, strict=True):
      if start == end:
        continue
      cost = -score_pair(client, provider) if is_eligible(client, provider) else _INELIGIBLE_COST
      cost_matrix[i, start:end] = cost

  row_ind, col_ind = linear_sum_assignment(cost_matrix)

  matched_count = 0
  scores: list[float] = []
  matched_count_by_provider: dict[uuid.UUID, int] = {}
  for row, col in zip(row_ind, col_ind, strict=True):
    if col >= total_real_slots:
      continue  # matched to a dummy column: stays unmatched

    client = clients[int(row)]
    provider = slot_providers[int(col)]
    score = score_pair(client, provider)
    db.add(
      Match(
        client_id=client.id,
        provider_id=provider.id,
        strategy=STRATEGY_NAME,
        score=score,
        status=MatchStatus.PROPOSED.value,
      )
    )
    matched_count += 1
    scores.append(score)
    matched_count_by_provider[provider.id] = matched_count_by_provider.get(provider.id, 0) + 1

  db.commit()

  return StrategyRunSummary(
    strategy=STRATEGY_NAME,
    client_count=client_count,
    matched_count=matched_count,
    unmatched_count=client_count - matched_count,
    fill_rate=round(matched_count / client_count, 4) if client_count else 0.0,
    mean_match_score=round(sum(scores) / len(scores), 4) if scores else 0.0,
    provider_utilization_std=provider_utilization_std(providers, matched_count_by_provider),
  )
