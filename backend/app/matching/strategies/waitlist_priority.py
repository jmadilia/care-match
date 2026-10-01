import uuid
from collections import deque
from datetime import UTC, datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.matching.candidates import Candidate, rank_candidates
from app.matching.strategies.errors import StrategyAlreadyRunError
from app.matching.strategies.metrics import fill_rate_by_urgency, provider_utilization_std
from app.models.client import Client
from app.models.match import Match
from app.models.provider import Provider
from app.models.simulation_run import SimulationRun
from app.models.waitlist_entry import WaitlistEntry
from app.schemas.client import ClientUrgency
from app.schemas.match import MatchStatus
from app.schemas.strategy_run import StrategyRunSummary
from app.schemas.waitlist_entry import WaitlistStatus
from app.simulation.config import ScenarioName, get_scenario

STRATEGY_NAME = "waitlist_priority"
_UNLIMITED = 10**9

# Priority = urgency baseline + aging. Tuned, not sourced: a routine client's priority
# catches an elevated client's baseline after 6 days waiting (0.5 * 6 = 3.0), and an
# urgent client's after 14 (0.5 * 14 = 7.0), so nobody waits forever regardless of how
# their case was triaged on arrival.
_URGENCY_PRIORITY: dict[ClientUrgency, float] = {
  ClientUrgency.ROUTINE: 0.0,
  ClientUrgency.ELEVATED: 3.0,
  ClientUrgency.URGENT: 7.0,
}
_AGING_PER_DAY = 0.5


def _priority(client: Client, day: int) -> float:
  urgency = _URGENCY_PRIORITY[ClientUrgency(client.urgency)]
  days_waited = day - (client.arrival_day or 0)
  return urgency + _AGING_PER_DAY * days_waited


def run_waitlist_priority(db: Session, run_id: uuid.UUID) -> StrategyRunSummary:
  """Simulates clients arriving over the run's horizon rather than treating the whole
  population as known up front, the gap the other three strategies share. Clients still
  rank providers by fit score and propose to their best remaining option, same as stable
  matching, but a provider's admission decision is not the mutual fit score. It's priority:
  urgency plus how long the client has been waiting. A provider holds its highest-priority
  proposals up to capacity and bumps the lowest-priority holder when a higher-priority
  proposal arrives; the bumped client keeps their place in line for whichever provider
  they'd try next (never re-proposing to one that already rejected them, same termination
  guarantee as stable matching) and re-enters the pool the next day aged one day further.

  A held client's priority is frozen at the moment they're admitted for bump comparisons:
  once someone is being served, recomputing their priority against the calendar would let
  pure elapsed time bump them out of care they're already receiving, which isn't what aging
  is for. Aging only applies to clients still actually waiting.

  Each client gets a WaitlistEntry on arrival, flipped to WAITING again if bumped, and
  resolved to MATCHED or EXPIRED once the run ends.

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

  run = db.get(SimulationRun, run_id)
  assert run is not None  # noqa: S101 -- guaranteed by the route before calling this
  horizon_days = get_scenario(ScenarioName(run.scenario)).horizon_days

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

  preferences: dict[uuid.UUID, list[Candidate[Provider]]] = {
    client.id: rank_candidates(client, [(provider, _UNLIMITED) for provider in providers])
    for client in clients
  }
  next_choice = dict.fromkeys(preferences, 0)
  capacity = {provider.id: provider.weekly_capacity for provider in providers}
  # Each hold is (client, score, priority_at_admission); priority drives bump decisions,
  # score is what ends up on the Match row.
  holds: dict[uuid.UUID, list[tuple[Client, float, float]]] = {
    provider.id: [] for provider in providers
  }
  waitlist_entries: dict[uuid.UUID, WaitlistEntry] = {}

  arrivals_by_day: dict[int, list[Client]] = {}
  for client in clients:
    arrivals_by_day.setdefault(client.arrival_day or 0, []).append(client)

  free_clients: deque[Client] = deque()

  for day in range(horizon_days):
    for client in arrivals_by_day.get(day, []):
      entry = WaitlistEntry(client_id=client.id, status=WaitlistStatus.WAITING.value)
      db.add(entry)
      db.flush()
      waitlist_entries[client.id] = entry
      if preferences[client.id]:
        free_clients.append(client)
      # else: no eligible provider at all; stays WAITING until the run ends and expires

    while free_clients:
      client = free_clients.popleft()
      choices = preferences[client.id]
      if next_choice[client.id] >= len(choices):
        continue  # exhausted every eligible provider for good

      candidate = choices[next_choice[client.id]]
      next_choice[client.id] += 1
      provider_holds = holds[candidate.provider.id]
      client_priority = _priority(client, day)

      if len(provider_holds) < capacity[candidate.provider.id]:
        provider_holds.append((client, candidate.score, client_priority))
        waitlist_entries[client.id].status = WaitlistStatus.MATCHED.value
      elif client_priority > provider_holds[-1][2]:
        bumped_client, _, _ = provider_holds[-1]
        provider_holds[-1] = (client, candidate.score, client_priority)
        waitlist_entries[bumped_client.id].status = WaitlistStatus.WAITING.value
        free_clients.append(bumped_client)
        waitlist_entries[client.id].status = WaitlistStatus.MATCHED.value
      else:
        free_clients.append(client)
        continue

      provider_holds.sort(key=lambda held: held[2], reverse=True)

  now = datetime.now(UTC)
  for entry in waitlist_entries.values():
    if entry.status == WaitlistStatus.WAITING.value:
      entry.status = WaitlistStatus.EXPIRED.value
    entry.resolved_at = now

  matched_count = 0
  scores: list[float] = []
  matched_count_by_provider: dict[uuid.UUID, int] = {}
  matched_client_ids: set[uuid.UUID] = set()
  for provider_id, provider_holds in holds.items():
    for client, score, _ in provider_holds:
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
      matched_count_by_provider[provider_id] = matched_count_by_provider.get(provider_id, 0) + 1
      matched_client_ids.add(client.id)

  db.commit()

  client_count = len(clients)
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
