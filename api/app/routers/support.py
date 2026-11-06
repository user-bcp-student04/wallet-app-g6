# api/app/routers/support.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import SupportCaseOut

router = APIRouter(prefix="/support", tags=["support"])


@router.get("/cases", response_model=list[SupportCaseOut])
def list_cases(store: InMemoryStore = Depends(get_store)) -> list[SupportCaseOut]:
    return services.list_support_cases(store)
