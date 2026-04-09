"""Keyword-related schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class KeywordSummaryItem(BaseModel):
    """Single keyword row for list pages."""

    id: int
    keyword: str
    target_article_id: int | None = None
    target_article_title: str | None = None
    target_article_slug: str | None = None
    search_volume: int = 0
    difficulty: int = 0
    cannibalization_risk: bool = False
    status: str
    created_at: datetime | None = None


class KeywordListPayload(BaseModel):
    """Paginated keyword list response."""

    items: list[KeywordSummaryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    warning: str | None = None


class KeywordClusterItem(BaseModel):
    """Aggregated keyword cluster item."""

    cluster_name: str
    keywords_total: int
    pending_keywords: int
    consumed_keywords: int
    average_difficulty: float | None = None


class KeywordClustersPayload(BaseModel):
    """Keyword cluster distribution response."""

    items: list[KeywordClusterItem] = Field(default_factory=list)
    limit: int
    warning: str | None = None
