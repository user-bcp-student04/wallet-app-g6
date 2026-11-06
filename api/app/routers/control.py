# api/app/routers/control.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import ErrorOut, ResetOut

router = APIRouter(prefix="/control", tags=["control"])


@router.post("/reset", response_model=ResetOut, responses={404: {"model": ErrorOut}})
def reset(store: InMemoryStore = Depends(get_store)) -> ResetOut:
    services.reset_state(store)
    return ResetOut(status="reset")
