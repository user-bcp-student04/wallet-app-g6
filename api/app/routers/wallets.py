# api/app/routers/wallets.py
from fastapi import APIRouter, Depends

from .. import services
from ..repository import InMemoryStore, get_store
from ..schemas import ErrorOut, ResourceId, WalletOut

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get(
    "/{wallet_id}",
    response_model=WalletOut,
    responses={400: {"model": ErrorOut}, 404: {"model": ErrorOut}},
)
def get_wallet(
    wallet_id: ResourceId, store: InMemoryStore = Depends(get_store)
) -> WalletOut:
    return services.get_wallet(store, wallet_id)
