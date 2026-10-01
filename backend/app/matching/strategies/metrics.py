import statistics
import uuid
from collections.abc import Mapping, Sequence

from app.models.provider import Provider


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
