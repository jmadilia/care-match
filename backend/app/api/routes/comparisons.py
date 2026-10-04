from fastapi import APIRouter

from app.evaluation.cache import get_comparison
from app.schemas.comparison import ComparisonRequest, ComparisonResult

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonResult, status_code=201)
def create_comparison(request: ComparisonRequest) -> ComparisonResult:
  return get_comparison(request)
