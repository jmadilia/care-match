from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.config import settings
from app.evaluation.cache import get_comparison
from app.schemas.comparison import ComparisonRequest, ComparisonResult

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonResult, status_code=201)
def create_comparison(request: ComparisonRequest, db: DbSession) -> ComparisonResult:
  # Deployed instances share computed results through the database. Locally the cache stays
  # in memory, so running the API by hand leaves no rows behind.
  return get_comparison(request, db if settings.ENVIRONMENT != "local" else None)
