# api/app/routers/scenarios.py
from fastapi import APIRouter

from .. import services
from ..schemas import ScenarioOut

router = APIRouter(tags=["scenarios"])


@router.get("/scenarios", response_model=list[ScenarioOut])
def list_scenarios() -> list[ScenarioOut]:
    return services.list_scenarios()
