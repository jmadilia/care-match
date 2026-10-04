from fastapi import APIRouter

from app.matching.intake import find_candidates
from app.schemas.intake import IntakeRequest, IntakeResult

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("", response_model=IntakeResult)
def intake(request: IntakeRequest) -> IntakeResult:
  return find_candidates(request)
