# api/app/services.py
"""Lógica de negocio del onboarding de wallet."""
import dataclasses
from datetime import datetime, timezone
from uuid import uuid4

from . import config
from .errors import ApiError
from .repository import (
    CaseRecord,
    InMemoryStore,
    VerificationRecord,
    WalletRecord,
)
from .schemas import (
    Balances,
    ScenarioOut,
    SupportCaseOut,
    VerificationCreate,
    VerificationOut,
    WalletOut,
)

SCENARIOS: list[ScenarioOut] = [
    ScenarioOut(id="APPROVED", label="Verificación aprobada"),
    ScenarioOut(id="REJECTED", label="Verificación rechazada"),
    ScenarioOut(id="MANUAL_REVIEW", label="Revisión manual"),
    ScenarioOut(id="KYC_UNAVAILABLE", label="Servicio KYC no disponible"),
]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_verification_out(record: VerificationRecord) -> VerificationOut:
    return VerificationOut(
        id=record.id,
        status=record.status,  # type: ignore[arg-type]
        decisionStatus=record.decision_status,  # type: ignore[arg-type]
        walletId=record.wallet_id,
        createdAt=record.created_at,
    )


def _open_wallet(store: InMemoryStore) -> str:
    wallet = WalletRecord(id=_new_id("wlt"), available=0, pending=0)
    store.wallets[wallet.id] = wallet
    return wallet.id


def list_scenarios() -> list[ScenarioOut]:
    return list(SCENARIOS)


def create_verification(
    store: InMemoryStore, payload: VerificationCreate
) -> VerificationOut:
    if config.ENFORCE_TEST_DOC_PREFIX and not payload.documentNumber.startswith("TEST-"):
        raise ApiError(
            400, "BAD_REQUEST", "El documento de prueba debe comenzar con TEST-."
        )
    if payload.scenario == "KYC_UNAVAILABLE":
        raise ApiError(
            503,
            "KYC_UNAVAILABLE",
            "El servicio de verificación no está disponible. Intente de nuevo más tarde.",
        )

    with store.lock:
        record = VerificationRecord(
            id=_new_id("ver"),
            status=payload.scenario,
            decision_status="PENDING" if payload.scenario == "MANUAL_REVIEW" else "NOT_REQUIRED",
            wallet_id=None,
            created_at=_now(),
        )
        if payload.scenario == "APPROVED":
            record.wallet_id = _open_wallet(store)
        if payload.scenario == "MANUAL_REVIEW":
            case = CaseRecord(
                id=_new_id("case"),
                type="KYC_REVIEW",
                status="OPEN",
                verification_id=record.id,
                created_at=record.created_at,
            )
            store.cases[case.id] = case
        store.verifications[record.id] = record
        return _to_verification_out(dataclasses.replace(record))


def get_verification(store: InMemoryStore, verification_id: str) -> VerificationOut:
    with store.lock:
        record = store.verifications.get(verification_id)
        if record is None:
            raise ApiError(404, "NOT_FOUND", "La verificación solicitada no existe.")
        return _to_verification_out(dataclasses.replace(record))


def decide_verification(
    store: InMemoryStore, verification_id: str, decision: str
) -> VerificationOut:
    # Comprobación de PENDING y cambio de estado dentro del mismo lock (atómico).
    with store.lock:
        record = store.verifications.get(verification_id)
        if record is None:
            raise ApiError(404, "NOT_FOUND", "La verificación solicitada no existe.")
        if record.decision_status != "PENDING":
            raise ApiError(
                409,
                "DECISION_CONFLICT",
                "La verificación ya fue decidida y no puede modificarse.",
            )
        record.status = decision
        record.decision_status = "DECIDED"
        if decision == "APPROVED":
            record.wallet_id = _open_wallet(store)
        for case in store.cases.values():
            if case.verification_id == record.id:
                case.status = "CLOSED"
        return _to_verification_out(dataclasses.replace(record))


def get_wallet(store: InMemoryStore, wallet_id: str) -> WalletOut:
    with store.lock:
        wallet = store.wallets.get(wallet_id)
        if wallet is None:
            raise ApiError(404, "NOT_FOUND", "La wallet solicitada no existe.")
        return WalletOut(
            id=wallet.id,
            balances=Balances(available=wallet.available, pending=wallet.pending),
        )


def list_support_cases(store: InMemoryStore) -> list[SupportCaseOut]:
    with store.lock:
        cases = sorted(store.cases.values(), key=lambda c: c.created_at)
        return [
            SupportCaseOut(
                id=c.id,
                type=c.type,  # type: ignore[arg-type]
                status=c.status,  # type: ignore[arg-type]
                verificationId=c.verification_id,
                createdAt=c.created_at,
            )
            for c in cases
        ]


def reset_state(store: InMemoryStore) -> None:
    if not config.ENABLE_CONTROL_RESET:
        raise ApiError(404, "NOT_FOUND", "El recurso solicitado no existe.")
    store.reset()
