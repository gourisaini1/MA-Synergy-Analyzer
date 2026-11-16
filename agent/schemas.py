from typing import Literal

from pydantic import BaseModel, Field


ClaimType = Literal[
    "management_synergy_target",
    "management_qualitative_claim",
    "integration_milestone",
    "integration_risk",
    "customer_overlap",
    "financial_metric",
]


class ExtractedClaim(BaseModel):
    claim_type: ClaimType
    claim: str = Field(min_length=12)
    supporting_excerpt: str = Field(min_length=8)
    classification: Literal[
        "management_statement", "observed_fact", "analyst_assumption"
    ]
    confidence: Literal["high", "medium", "low"]
    analyst_comment: str = ""


class ClaimsEnvelope(BaseModel):
    claims: list[ExtractedClaim]


class EvidenceClaim(BaseModel):
    deal_id: str
    claim_type: ClaimType
    claim: str
    source_id: str
    source_url: str
    document_date: str | None = None
    page_or_section: str
    supporting_excerpt: str = Field(min_length=8)
    classification: Literal[
        "management_statement", "observed_fact", "analyst_assumption"
    ]
    confidence: Literal["high", "medium", "low"]
    analyst_comment: str = ""
