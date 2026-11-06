# api/app/routers/kyc.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import (
    DecisionIn,
    ErrorOut,
    ResourceId,
    VerificationCreate,
    VerificationOut,
)

router = APIRouter(prefix="/kyc/verifications", tags=["kyc"])


@router.post(
    "",
    response_model=VerificationOut,
    status_code=201,
    responses={400: {"model": ErrorOut}, 413: {"model": ErrorOut}, 503: {"model": ErrorOut}},
)
def create_verification(
    payload: VerificationCreate, store: InMemoryStore = Depends(get_store)
) -> VerificationOut:
    return services.create_verification(store, payload)


@router.get(
    "/{verification_id}",
    response_model=VerificationOut,
    responses={400: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
def get_verification(
    verification_id: ResourceId, store: InMemoryStore = Depends(get_store)
) -> VerificationOut:
    return services.get_verification(store, verification_id)


@router.post(
    "/{verification_id}/decision",
    response_model=VerificationOut,
    responses={
        400: {"model": ErrorOut},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
        413: {"model": ErrorOut},
    },
)
def decide_verification(
    verification_id: ResourceId,
    payload: DecisionIn,
    store: InMemoryStore = Depends(get_store),
) -> VerificationOut:
    return services.decide_verification(store, verification_id, payload.decision)
