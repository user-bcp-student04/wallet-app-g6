# api/app/schemas.py
"""Modelos Pydantic de entrada y salida. Fuente del contrato que el frontend debe espejar."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class KycScenario(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class VerificationStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class KycDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class WalletStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    KYC_PENDING = "KYC_PENDING"
    KYC_FAILED = "KYC_FAILED"
    ACTIVE = "ACTIVE"


class StepStatus(str, Enum):
    COMPLETED = "COMPLETED"
    CURRENT = "CURRENT"
    LOCKED = "LOCKED"


# ---------- Requests (rechazan campos desconocidos, p. ej. un "owner" enviado por el cliente) ----------
class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KycVerificationRequest(_StrictModel):
    document_number: str = Field(min_length=1, max_length=64)
    scenario: KycScenario


class KycDecisionRequest(_StrictModel):
    decision: KycDecision


class StepRequest(_StrictModel):
    document_number: Optional[str] = Field(default=None, min_length=1, max_length=64)


# ---------- Responses ----------
class ErrorResponse(BaseModel):
    code: str
    message: str


class HealthResponse(BaseModel):
    status: str


class ScenarioItem(BaseModel):
    name: KycScenario
    description: str


class ScenariosResponse(BaseModel):
    scenarios: list[ScenarioItem]


class SupportCase(BaseModel):
    verification_id: str
    status: VerificationStatus
    message: str


class SupportCasesResponse(BaseModel):
    cases: list[SupportCase]


class VerificationResponse(BaseModel):
    verification_id: str
    document_number: str
    scenario: KycScenario
    status: VerificationStatus
    created_at: datetime
    decided_at: Optional[datetime] = None


class StepInfo(BaseModel):
    id: str
    order: int
    status: StepStatus


class OnboardingStateResponse(BaseModel):
    wallet_status: WalletStatus
    current_step: Optional[str] = None
    steps: list[StepInfo]
    low_amount_payments_enabled: bool
    duration_seconds: Optional[float] = None


class ResetResponse(BaseModel):
    status: str


class MonthlyAnalyticsRow(BaseModel):
    month: str  # "YYYY-MM" en UTC
    new_active_users: int
    attributed_spend_cents: int


# Documentación OpenAPI de los errores comunes (todos con el formato único).
ERROR_RESPONSES: dict[int, dict] = {
    401: {"model": ErrorResponse, "description": "Sin identidad válida"},
    404: {"model": ErrorResponse, "description": "Recurso inexistente"},
    409: {"model": ErrorResponse, "description": "Conflicto de estado"},
    413: {"model": ErrorResponse, "description": "Cuerpo demasiado grande"},
    422: {"model": ErrorResponse, "description": "Entrada inválida"},
    500: {"model": ErrorResponse, "description": "Error interno"},
}
