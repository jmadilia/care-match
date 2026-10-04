from collections import OrderedDict
from pathlib import Path
from threading import Lock

from app.evaluation.comparison import run_comparison
from app.schemas.comparison import ComparisonRequest, ComparisonResult
from app.simulation.config import ScenarioName

# Results are a pure function of the request, since every strategy is deterministic for a
# given seed, so caching them is exact rather than approximate. The default request (the
# one the comparison page and the README results use) is served from a committed snapshot,
# so a cold host answers it instantly instead of spending a minute recomputing it. Any other
# request is computed once and kept in a small LRU.
SNAPSHOT_PATH = Path(__file__).with_name("default_comparison.json")
DEFAULT_REQUEST = ComparisonRequest(
  scenario=ScenarioName.BALANCED,
  seeds=list(range(1, 11)),
  provider_count=60,
  client_count=300,
)
_MAX_ENTRIES = 32

_lock = Lock()
_entries: OrderedDict[str, ComparisonResult] = OrderedDict()
_default: ComparisonResult | None = None
_default_loaded = False


def _key(request: ComparisonRequest) -> str:
  return request.model_dump_json()


def _load_default() -> ComparisonResult | None:
  global _default, _default_loaded
  if not _default_loaded:
    _default_loaded = True
    if SNAPSHOT_PATH.exists():
      _default = ComparisonResult.model_validate_json(SNAPSHOT_PATH.read_text(encoding="utf-8"))
  return _default


def get_comparison(request: ComparisonRequest) -> ComparisonResult:
  key = _key(request)
  with _lock:
    if key == _key(DEFAULT_REQUEST):
      default = _load_default()
      if default is not None:
        return default
    cached = _entries.get(key)
    if cached is not None:
      _entries.move_to_end(key)
      return cached

  # Computed outside the lock: it takes seconds, and two identical concurrent requests
  # computing twice is cheaper than serializing every request behind one lock.
  result = run_comparison(request)

  with _lock:
    _entries[key] = result
    _entries.move_to_end(key)
    while len(_entries) > _MAX_ENTRIES:
      _entries.popitem(last=False)
  return result


def clear_cache() -> None:
  global _default, _default_loaded
  with _lock:
    _entries.clear()
    _default = None
    _default_loaded = False
