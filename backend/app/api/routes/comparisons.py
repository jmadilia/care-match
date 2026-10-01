from fastapi import APIRouter

from app.evaluation.comparison import run_comparison
from app.schemas.comparison import ComparisonRequest, ComparisonResult

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("", response_model=ComparisonResult, status_code=201)
def create_comparison(request: ComparisonRequest) -> ComparisonResult:
  return run_comparison(request)
