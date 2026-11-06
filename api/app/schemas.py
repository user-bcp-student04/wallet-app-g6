# api/app/schemas.py
"""Modelos Pydantic de entrada y salida. No exponen estructuras internas."""
from datetime import datetime
from typing import Annotated, Literal, Optional

from fastapi import Path
from pydantic import BaseModel, ConfigDict, StringConstraints

from . import config

Scenario = Literal["APPROVED", "REJECTED", "MANUAL_REVIEW", "KYC_UNAVAILABLE"]
VerificationStatus = Literal["APPROVED", "REJECTED", "MANUAL_REVIEW"]
DecisionStatus = Literal["PENDING", "DECIDED", "NOT_REQUIRED"]

DocumentNumber = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=config.DOCUMENT_MAX_LENGTH,
        pattern=r"^[A-Za-z0-9-]+$",
    ),
]

ResourceId = Annotated[str, Path(pattern=config.RESOURCE_ID_PATTERN)]


class VerificationCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    documentNumber: DocumentNumber
    scenario: Scenario


class DecisionIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    decision: Literal["APPROVED", "REJECTED"]


class VerificationOut(BaseModel):
    id: str
    status: VerificationStatus
    decisionStatus: DecisionStatus
    walletId: Optional[str] = None
    createdAt: datetime


class Balances(BaseModel):
    available: int
    pending: int


class WalletOut(BaseModel):
    id: str
    balances: Balances


class SupportCaseOut(BaseModel):
    id: str
    type: Literal["KYC_REVIEW"]
    status: Literal["OPEN", "CLOSED"]
    verificationId: str
    createdAt: datetime


class ScenarioOut(BaseModel):
    id: Scenario
    label: str


class HealthOut(BaseModel):
    status: Literal["ok"]


class ResetOut(BaseModel):
    status: Literal["reset"]


class ErrorOut(BaseModel):
    code: str
    message: str
