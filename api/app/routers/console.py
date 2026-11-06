# api/app/routers/console.py
from fastapi import APIRouter, Depends

from app.schemas import (
    ERROR_RESPONSES,
    HealthResponse,
    ResetResponse,
    ScenariosResponse,
    SupportCasesResponse,
)
from app.services import OnboardingService, get_current_owner, get_onboarding_service

router = APIRouter(tags=["console"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/scenarios", response_model=ScenariosResponse)
def scenarios(service: OnboardingService = Depends(get_onboarding_service)) -> ScenariosResponse:
    return service.list_scenarios()


@router.get("/support/cases", response_model=SupportCasesResponse, responses=ERROR_RESPONSES)
def support_cases(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> SupportCasesResponse:
    return service.list_support_cases(owner_id)


@router.post("/control/reset", response_model=ResetResponse, responses=ERROR_RESPONSES)
def reset(
    owner_id: str = Depends(get_current_owner),
    service: OnboardingService = Depends(get_onboarding_service),
) -> ResetResponse:
    service.reset(owner_id)
    return ResetResponse(status="reset")
