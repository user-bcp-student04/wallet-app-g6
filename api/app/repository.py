# api/app/repository.py
"""Acceso a datos: almacén en memoria con bloqueo para operaciones atómicas."""
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VerificationRecord:
    id: str
    status: str
    decision_status: str
    wallet_id: str | None
    created_at: datetime


@dataclass
class WalletRecord:
    id: str
    available: int
    pending: int


@dataclass
class CaseRecord:
    id: str
    type: str
    status: str
    verification_id: str
    created_at: datetime


class InMemoryStore:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.verifications: dict[str, VerificationRecord] = {}
        self.wallets: dict[str, WalletRecord] = {}
        self.cases: dict[str, CaseRecord] = {}

    def reset(self) -> None:
        with self.lock:
            self.verifications.clear()
            self.wallets.clear()
            self.cases.clear()


_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _store
