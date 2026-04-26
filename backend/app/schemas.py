from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class NodeStatus(str, Enum):
    OK = "OK"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"
    ACCESS_DENIED = "ACCESS_DENIED"
    SKIPPED = "SKIPPED"


class ConsensusVerdict(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ResolutionDraft(BaseModel):
    background: str = Field(..., min_length=1)
    core_request: str = Field(..., min_length=1)
    constraints: List[str] = Field(default_factory=list)


class ResolveRequest(BaseModel):
    user_input: Optional[str] = None
    resolution_draft: Optional[ResolutionDraft] = None
    tokens: Dict[str, str] = Field(default_factory=dict)
    models: Dict[str, str] = Field(default_factory=dict)
    allow_minimal_draft: bool = False
    locale: str = "zh"

    @model_validator(mode="after")
    def validate_payload(self) -> "ResolveRequest":
        if self.user_input or self.resolution_draft:
            return self
        raise ValueError("Either user_input or resolution_draft must be provided.")


class ArchitectResult(BaseModel):
    requires_clarification: bool = False
    questions: List[str] = Field(default_factory=list)
    resolution_draft: Optional[ResolutionDraft] = None
    confirmation_required: bool = False
    confirmation_prompt: Optional[str] = None


class NodeReport(BaseModel):
    node: str
    provider: str
    status: NodeStatus
    opinion: Optional[bool] = None
    summary: str
    key_points: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None


class SynthesisResult(BaseModel):
    verdict: ConsensusVerdict
    vote_ratio: str
    consensus_summary: str
    disagreement_summary: str
    ruling_explanation: str
    degraded_mode: bool = False


class ResolveResponse(BaseModel):
    status: str
    architect: ArchitectResult
    reports: List[NodeReport] = Field(default_factory=list)
    synthesis: Optional[SynthesisResult] = None
