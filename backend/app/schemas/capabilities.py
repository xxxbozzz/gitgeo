"""Capability-related schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CapabilityArticleReference(BaseModel):
    """Recent article related to a capability."""

    id: int
    title: str
    slug: str
    publish_status: int
    quality_score: int
    updated_at: datetime | None = None


class CapabilitySummaryItem(BaseModel):
    """Single capability row for list pages."""

    id: int
    group_code: str
    group_name: str
    capability_code: str
    capability_name: str
    category: str | None = None
    public_claim: str | None = None
    claim_level: str
    confidence_score: float
    is_active: bool = True
    source_count: int = 0
    application_tags: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class CapabilityDetailItem(CapabilitySummaryItem):
    """Capability detail payload."""

    metric_type: str
    unit: str | None = None
    comparator: str | None = None
    conservative_value_num: float | None = None
    conservative_value_text: str | None = None
    advanced_value_num: float | None = None
    advanced_value_text: str | None = None
    internal_note: str | None = None
    conditions_text: str | None = None
    recent_articles: list[CapabilityArticleReference] = Field(default_factory=list)


class CapabilitySourceItem(BaseModel):
    """Source linked to a capability."""

    id: int
    source_code: str
    source_vendor: str
    source_title: str
    source_type: str
    source_url: str
    publish_org: str | None = None
    observed_on: str | None = None
    reliability_score: float
    citation_note: str | None = None
    priority_weight: int


class CapabilityListPayload(BaseModel):
    """Paginated capability list payload."""

    items: list[CapabilitySummaryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    active_total: int = 0
    inactive_total: int = 0
    groups_total: int = 0
    warning: str | None = None


class CapabilityDetailPayload(BaseModel):
    """Single capability response."""

    capability: CapabilityDetailItem | None = None
    warning: str | None = None


class CapabilitySourcesPayload(BaseModel):
    """Capability sources response."""

    spec_id: int
    items: list[CapabilitySourceItem] = Field(default_factory=list)
    warning: str | None = None
