import hashlib
import logging
import os
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.evaluation.comparison import run_comparison
from app.models.comparison_cache import ComparisonCacheEntry
from app.schemas.comparison import ComparisonRequest, ComparisonResult
from app.simulation.config import ScenarioName

logger = logging.getLogger(__name__)

# Results are a pure function of the request, since every strategy is deterministic for a
# given seed, so caching them is exact rather than approximate. Three layers, cheapest first:
#
# 1. The default request (the one the comparison page and the README results use) is served
#    from a committed snapshot, so a cold host answers it instantly.
# 2. A small in-memory LRU per process.
# 3. An optional shared table, so every serverless instance reuses a result any of them
#    computed, instead of each paying the full minute once.
#
# Identical concurrent requests on one process share a single computation.
SNAPSHOT_PATH = Path(__file__).with_name("default_comparison.json")
DEFAULT_REQUEST = ComparisonRequest(
  scenario=ScenarioName.BALANCED,
  seeds=list(range(1, 11)),
  provider_count=60,
  client_count=300,
)
_MAX_ENTRIES = 32
# The request space is large (seeds are arbitrary integers), so the shared table keeps only
# the newest rows. Stored results are small, but nothing else bounds them.
MAX_SHARED_ENTRIES = 200

# Part of the shared key, so a deploy that changes matching behavior can't serve results the
# previous code computed. Vercel sets the commit SHA; elsewhere the value is a fixed label.
CODE_VERSION = os.environ.get("VERCEL_GIT_COMMIT_SHA", "local")

_lock = Lock()
_entries: OrderedDict[str, ComparisonResult] = OrderedDict()
_default: ComparisonResult | None = None
_default_loaded = False


class _Flight:
  def __init__(self) -> None:
    self.lock = Lock()
    self.waiters = 0


_inflight: dict[str, _Flight] = {}


def _key(request: ComparisonRequest) -> str:
  return request.model_dump_json()


def _shared_key(request: ComparisonRequest) -> str:
  return hashlib.sha256(f"{CODE_VERSION}:{_key(request)}".encode()).hexdigest()


def _load_default() -> ComparisonResult | None:
  global _default, _default_loaded
  if not _default_loaded:
    _default_loaded = True
    if SNAPSHOT_PATH.exists():
      _default = ComparisonResult.model_validate_json(SNAPSHOT_PATH.read_text(encoding="utf-8"))
  return _default


def _remember(key: str, result: ComparisonResult) -> None:
  with _lock:
    _entries[key] = result
    _entries.move_to_end(key)
    while len(_entries) > _MAX_ENTRIES:
      _entries.popitem(last=False)


@contextmanager
def _single_flight(key: str) -> Iterator[None]:
  with _lock:
    flight = _inflight.setdefault(key, _Flight())
    flight.waiters += 1
  try:
    with flight.lock:
      yield
  finally:
    with _lock:
      flight.waiters -= 1
      if flight.waiters == 0:
        _inflight.pop(key, None)


def _read_shared(db: Session, shared_key: str) -> ComparisonResult | None:
  # The shared layer is an optimization, so any failure here (table missing, database
  # unreachable, a stored shape the schema no longer accepts) falls back to computing.
  try:
    row = db.get(ComparisonCacheEntry, shared_key)
    result = ComparisonResult.model_validate(row.result) if row is not None else None
    # Ends the read transaction now: the computation that may follow takes up to a minute
    # and shouldn't hold a database connection open for it.
    db.commit()
    return result
  except (SQLAlchemyError, ValueError):
    db.rollback()
    logger.warning("Shared comparison cache read failed", exc_info=True)
    return None


def _write_shared(db: Session, shared_key: str, result: ComparisonResult) -> None:
  try:
    db.execute(
      pg_insert(ComparisonCacheEntry)
      .values(key=shared_key, result=result.model_dump(mode="json"))
      .on_conflict_do_nothing()
    )
    newest = (
      select(ComparisonCacheEntry.key)
      .order_by(ComparisonCacheEntry.created_at.desc())
      .limit(MAX_SHARED_ENTRIES)
    )
    db.execute(delete(ComparisonCacheEntry).where(ComparisonCacheEntry.key.not_in(newest)))
    db.commit()
  except SQLAlchemyError:
    db.rollback()
    logger.warning("Shared comparison cache write failed", exc_info=True)


def get_comparison(request: ComparisonRequest, db: Session | None = None) -> ComparisonResult:
  """Return the comparison for `request`, computing it only if no layer has it.

  Pass `db` to use the shared table as well as the in-memory layers.
  """
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

  with _single_flight(key):
    # A request that was waiting on the same computation finds its result here.
    with _lock:
      cached = _entries.get(key)
    if cached is not None:
      return cached

    shared_key = _shared_key(request)
    if db is not None:
      shared = _read_shared(db, shared_key)
      if shared is not None:
        _remember(key, shared)
        return shared

    result = run_comparison(request)
    _remember(key, result)
    if db is not None:
      _write_shared(db, shared_key, result)
    return result


def clear_cache() -> None:
  global _default, _default_loaded
  with _lock:
    _entries.clear()
    _default = None
    _default_loaded = False
