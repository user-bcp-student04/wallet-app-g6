# api/app/routers/onboarding.py
from typing import Optional

from fastapi import APIRouter, Depends, Path

from app.schemas import ERROR_RESPONSES, OnboardingStateResponse, StepRequest
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("", response_model=OnboardingStateResponse, responses=ERROR_RESPONSES)
def get_onboarding(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStateResponse:
    return service.get_state(owner_id)


@router.post("/steps/{step_id}", response_model=OnboardingStateResponse, responses=ERROR_RESPONSES)
def submit_step(
    body: Optional[StepRequest] = None,
    step_id: str = Path(min_length=1, max_length=32),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingStateResponse:
    document_number = body.document_number if body is not None else None
    return service.submit_step(owner_id, step_id, document_number)
