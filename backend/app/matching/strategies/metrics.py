import statistics
import uuid
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet

from app.models.client import Client
from app.models.provider import Provider


def fill_rate_by_urgency(
  clients: Sequence[Client], matched_client_ids: AbstractSet[uuid.UUID]
) -> dict[str, float]:
  """Fraction matched within each urgency tier. Scoring never looks at urgency, so a
  strategy that doesn't specifically account for it will show roughly the same fill rate
  across tiers regardless of how clinically urgent a client is.
  """
  by_tier: dict[str, list[bool]] = {}
  for client in clients:
    by_tier.setdefault(client.urgency, []).append(client.id in matched_client_ids)
  return {tier: round(sum(matched) / len(matched), 4) for tier, matched in by_tier.items()}


def provider_utilization_std(
  providers: Sequence[Provider], matched_count_by_provider: Mapping[uuid.UUID, int]
) -> float:
  """Population standard deviation of per-provider utilization (matched / weekly_capacity).

  Low: load is spread evenly. High: some providers are overloaded while others sit idle,
  which is the burnout-risk signal a fill-rate number alone can't show.
  """
  if not providers:
    return 0.0
  utilizations = [
    matched_count_by_provider.get(provider.id, 0) / provider.weekly_capacity
    for provider in providers
  ]
  return round(statistics.pstdev(utilizations), 4)
