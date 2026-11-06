# api/app/services.py
"""Lógica de negocio del onboarding y KYC, y dependencia de identidad get_current_owner."""
import re
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import Header

from app import config
from app.errors import ApiError
from app.schemas import (
    KycDecision,
    KycScenario,
    MonthlyAnalyticsRow,
    OnboardingStateResponse,
    ScenarioItem,
    ScenariosResponse,
    StepInfo,
    StepStatus,
    SupportCase,
    SupportCasesResponse,
    VerificationResponse,
    VerificationStatus,
    WalletStatus,
)
from app.storage import OwnerStore

STEP_ORDER: tuple[str, ...] = ("registro", "kyc", "activacion")
TEST_PREFIX = "TEST-"

EVENT_STARTED = "ONBOARDING_STARTED"
EVENT_STEP = "STEP_COMPLETED"
EVENT_CLOSED = "ONBOARDING_CLOSED"

_OWNER_RE = re.compile(config.OWNER_ID_PATTERN)
_DOCUMENT_SUFFIX_RE = re.compile(r"[A-Za-z0-9-]{1,59}")

_SCENARIO_STATUS: dict[KycScenario, VerificationStatus] = {
    KycScenario.APPROVED: VerificationStatus.APPROVED,
    KycScenario.REJECTED: VerificationStatus.REJECTED,
    KycScenario.PENDING: VerificationStatus.PENDING,
    KycScenario.EXPIRED: VerificationStatus.EXPIRED,
}

_SCENARIO_DESCRIPTIONS: dict[KycScenario, str] = {
    KycScenario.APPROVED: "La verificación se aprueba de inmediato.",
    KycScenario.REJECTED: "La verificación se rechaza de inmediato.",
    KycScenario.PENDING: "La verificación queda pendiente hasta que se registre una decisión.",
    KycScenario.EXPIRED: "La verificación expira sin resolverse.",
}

_SUPPORT_MESSAGES: dict[str, str] = {
    VerificationStatus.PENDING.value: "Verificación pendiente: registra una decisión en /kyc/verifications/{id}/decision.",
    VerificationStatus.REJECTED.value: "Verificación rechazada: crea una nueva con un documento TEST- válido.",
    VerificationStatus.EXPIRED.value: "Verificación expirada: crea una nueva verificación.",
}


def get_current_owner(
    x_owner_id: Optional[str] = Header(default=None, alias=config.OWNER_HEADER),
) -> str:
    """Identidad del usuario autenticado. Nunca se toma del cuerpo ni de la URL."""
    if x_owner_id is None or _OWNER_RE.fullmatch(x_owner_id) is None:
        raise ApiError(401, "UNAUTHENTICATED", "No se pudo identificar al usuario.")
    return x_owner_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_duration_seconds(started_at: Optional[str], closed_at: Optional[str]) -> Optional[float]:
    if not started_at or not closed_at:
        return None
    delta = datetime.fromisoformat(closed_at) - datetime.fromisoformat(started_at)
    return round(delta.total_seconds(), 3)


def _validate_document(document_number: str) -> None:
    if not document_number.startswith(TEST_PREFIX):
        raise ApiError(
            422,
            "DOCUMENT_NOT_TEST",
            "El documento debe comenzar con 'TEST-' en este entorno de pruebas.",
        )
    if _DOCUMENT_SUFFIX_RE.fullmatch(document_number[len(TEST_PREFIX):]) is None:
        raise ApiError(
            422,
            "VALIDATION_ERROR",
            "Tras 'TEST-' usa de 1 a 59 caracteres: letras, números o guiones.",
        )


def _wallet_status(state: dict[str, Any]) -> WalletStatus:
    completed = state["steps_completed"]
    if STEP_ORDER[-1] in completed:
        return WalletStatus.ACTIVE
    latest = state["verifications"][-1] if state["verifications"] else None
    if "kyc" not in completed and latest is not None:
        if latest["status"] == VerificationStatus.PENDING.value:
            return WalletStatus.KYC_PENDING
        if latest["status"] in (VerificationStatus.REJECTED.value, VerificationStatus.EXPIRED.value):
            return WalletStatus.KYC_FAILED
    if not completed and latest is None:
        return WalletStatus.NOT_STARTED
    return WalletStatus.IN_PROGRESS


def _state_response(state: dict[str, Any]) -> OnboardingStateResponse:
    completed = state["steps_completed"]
    current = next((step for step in STEP_ORDER if step not in completed), None)
    steps: list[StepInfo] = []
    for order, step in enumerate(STEP_ORDER, start=1):
        if step in completed:
            status = StepStatus.COMPLETED
        elif step == current:
            status = StepStatus.CURRENT
        else:
            status = StepStatus.LOCKED
        steps.append(StepInfo(id=step, order=order, status=status))
    wallet_status = _wallet_status(state)
    return OnboardingStateResponse(
        wallet_status=wallet_status,
        current_step=current,
        steps=steps,
        low_amount_payments_enabled=wallet_status == WalletStatus.ACTIVE,
        duration_seconds=compute_duration_seconds(state["started_at"], state["closed_at"]),
    )


def _verification_response(record: dict[str, Any]) -> VerificationResponse:
    return VerificationResponse(**record)


def _find_verification(state: dict[str, Any], verification_id: str) -> dict[str, Any]:
    for record in state["verifications"]:
        if record["verification_id"] == verification_id:
            return record
    raise ApiError(404, "NOT_FOUND", "La verificación no existe.")


class OnboardingService:
    def __init__(self, store: OwnerStore, clock: Callable[[], datetime] = _utcnow) -> None:
        self._store = store
        self._clock = clock

    # ---------- Consola ----------
    @staticmethod
    def list_scenarios() -> ScenariosResponse:
        return ScenariosResponse(
            scenarios=[ScenarioItem(name=s, description=_SCENARIO_DESCRIPTIONS[s]) for s in KycScenario]
        )

    def list_support_cases(self, owner_id: str) -> SupportCasesResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        cases = [
            SupportCase(
                verification_id=record["verification_id"],
                status=VerificationStatus(record["status"]),
                message=_SUPPORT_MESSAGES[record["status"]],
            )
            for record in state["verifications"]
            if record["status"] in _SUPPORT_MESSAGES
        ]
        return SupportCasesResponse(cases=cases)

    def reset(self, owner_id: str) -> None:
        with self._store.locked(owner_id):
            self._store.delete(owner_id)

    # ---------- KYC ----------
    def create_verification(
        self, owner_id: str, document_number: str, scenario: KycScenario
    ) -> VerificationResponse:
        _validate_document(document_number)  # antes de tocar disco
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            if len(state["verifications"]) >= config.MAX_VERIFICATIONS_PER_OWNER:
                raise ApiError(
                    409,
                    "LIMIT_REACHED",
                    "Alcanzaste el máximo de verificaciones de prueba. Usa POST /control/reset para reiniciar.",
                )
            now = self._clock().isoformat()
            status = _SCENARIO_STATUS[scenario]
            record = {
                "verification_id": uuid.uuid4().hex,
                "document_number": document_number,
                "scenario": scenario.value,
                "status": status.value,
                "created_at": now,
                "decided_at": None if status == VerificationStatus.PENDING else now,
            }
            state["verifications"].append(record)
            self._store.write(owner_id, state)
            return _verification_response(record)

    def get_verification(self, owner_id: str, verification_id: str) -> VerificationResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        return _verification_response(_find_verification(state, verification_id))

    def decide_verification(
        self, owner_id: str, verification_id: str, decision: KycDecision
    ) -> VerificationResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            record = _find_verification(state, verification_id)
            if record["status"] != VerificationStatus.PENDING.value:
                raise ApiError(
                    409,
                    "VERIFICATION_NOT_PENDING",
                    "La verificación ya fue resuelta; solo se puede decidir sobre verificaciones en estado PENDING.",
                )
            record["status"] = decision.value
            record["decided_at"] = self._clock().isoformat()
            self._store.write(owner_id, state)
            return _verification_response(record)

    # ---------- Onboarding ----------
    def get_state(self, owner_id: str) -> OnboardingStateResponse:
        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
        return _state_response(state)

    def submit_step(
        self, owner_id: str, step_id: str, document_number: Optional[str]
    ) -> OnboardingStateResponse:
        if step_id not in STEP_ORDER:
            raise ApiError(404, "NOT_FOUND", "El paso no existe. Pasos válidos: registro, kyc, activacion.")
        if step_id == "registro":
            if document_number is None:
                raise ApiError(
                    422,
                    "VALIDATION_ERROR",
                    "El paso 'registro' requiere 'document_number' con prefijo 'TEST-'.",
                )
            _validate_document(document_number)
        elif document_number is not None:
            raise ApiError(422, "VALIDATION_ERROR", "Este paso no admite datos en el cuerpo de la solicitud.")

        with self._store.locked(owner_id):
            state = self._store.read(owner_id)
            completed = state["steps_completed"]
            if step_id in completed:  # idempotente: sin eventos duplicados
                return _state_response(state)
            self._assert_not_blocked(step_id, state)

            now = self._clock().isoformat()
            if state["started_at"] is None:
                state["started_at"] = now
                state["events"].append({"type": EVENT_STARTED, "step": None, "at": now})
            completed.append(step_id)
            state["events"].append({"type": EVENT_STEP, "step": step_id, "at": now})
            if step_id == STEP_ORDER[-1]:
                state["closed_at"] = now
                state["events"].append({"type": EVENT_CLOSED, "step": None, "at": now})
            self._store.write(owner_id, state)
            return _state_response(state)

    @staticmethod
    def _assert_not_blocked(step_id: str, state: dict[str, Any]) -> None:
        index = STEP_ORDER.index(step_id)
        if index > 0 and STEP_ORDER[index - 1] not in state["steps_completed"]:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                f"Completa el paso '{STEP_ORDER[index - 1]}' antes de continuar con '{step_id}'.",
            )
        if step_id != "kyc":
            return
        latest = state["verifications"][-1] if state["verifications"] else None
        if latest is None:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Crea una verificación KYC (POST /kyc/verifications) antes de completar este paso.",
            )
        if latest["status"] == VerificationStatus.PENDING.value:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Tu verificación KYC está pendiente. Espera la decisión y vuelve a intentarlo.",
            )
        if latest["status"] != VerificationStatus.APPROVED.value:
            raise ApiError(
                409,
                "STEP_BLOCKED",
                "Tu verificación KYC no fue aprobada. Crea una nueva verificación con un documento TEST- válido.",
            )

    # ---------- Analítica mensual (2.8) ----------
    def monthly_analytics(self) -> list[MonthlyAnalyticsRow]:
        buckets: dict[str, list[int]] = {}
        for state in self._store.iter_states():
            closed_at = state.get("closed_at")
            if not closed_at:
                continue
            month = datetime.fromisoformat(closed_at).astimezone(timezone.utc).strftime("%Y-%m")
            spend = sum(int(item["amount_cents"]) for item in state.get("spend", []))
            bucket = buckets.setdefault(month, [0, 0])
            bucket[0] += 1
            bucket[1] += spend
        return [
            MonthlyAnalyticsRow(month=month, new_active_users=values[0], attributed_spend_cents=values[1])
            for month, values in sorted(buckets.items())
        ]


@lru_cache(maxsize=1)
def get_onboarding_service() -> OnboardingService:
    return OnboardingService(OwnerStore(Path(config.DATA_DIR)))
