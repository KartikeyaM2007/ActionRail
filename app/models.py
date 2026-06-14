from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


Decision = Literal["allow", "approval_required", "blocked", "needs_more_evidence"]
TransactionStatus = Literal["preflighted", "approved", "rejected", "executed", "blocked"]


class InvoiceInput(BaseModel):
    invoice_id: str = Field(..., min_length=1)
    vendor: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    invoice_date: str | None = None
    due_date: str | None = None
    gst_number: str | None = None
    contract_id: str | None = None
    evidence_urls: list[str] = Field(default_factory=list)
    line_items: list[str] = Field(default_factory=list)


class PreflightRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    intent: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    invoice: InvoiceInput
    constraints: dict[str, Any] = Field(default_factory=dict)


class CheckResult(BaseModel):
    name: str
    status: Literal["passed", "failed", "warning", "needs_evidence"]
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class PreflightResponse(BaseModel):
    transaction_id: str
    decision: Decision
    risk: Literal["low", "medium", "high", "critical"]
    checks: list[CheckResult]
    allowed_next_action: str
    blocked_actions: list[str] = Field(default_factory=list)
    expires_at: datetime


class ApprovalDecision(BaseModel):
    approver_id: str = Field(..., min_length=1)
    note: str | None = None


class Receipt(BaseModel):
    receipt_id: str
    transaction_id: str
    action: str
    agent_id: str
    user_id: str
    status: str
    executed_at: datetime
    receipt_signature: str
    payload: dict[str, Any]
