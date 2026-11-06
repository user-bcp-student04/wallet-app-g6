# api/app/routers/kyc.py
from fastapi import APIRouter, Depends, Path

from app.schemas import (
    ERROR_RESPONSES,
    KycDecisionRequest,
    KycVerificationRequest,
    VerificationResponse,
)
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(prefix="/kyc", tags=["kyc"])


@router.post(
    "/verifications",
    response_model=VerificationResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def create_verification(
    body: KycVerificationRequest,
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.create_verification(owner_id, body.document_number, body.scenario)


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationResponse,
    responses=ERROR_RESPONSES,
)
def get_verification(
    verification_id: str = Path(min_length=1, max_length=64),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.get_verification(owner_id, verification_id)


@router.post(
    "/verifications/{verification_id}/decision",
    response_model=VerificationResponse,
    responses=ERROR_RESPONSES,
)
def decide_verification(
    body: KycDecisionRequest,
    verification_id: str = Path(min_length=1, max_length=64),
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> VerificationResponse:
    return service.decide_verification(owner_id, verification_id, body.decision)
