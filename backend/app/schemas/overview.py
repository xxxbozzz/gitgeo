"""Overview-related schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from backend.app.schemas.articles import ArticleSummaryItem


class OverviewKpisPayload(BaseModel):
    """Top-level KPI payload."""

    articles_total: int
    passed_articles: int
    pending_keywords: int
    average_quality_score: float | None = None
    internal_links: int
    latest_article_at: str | None = None
    warning: str | None = None


class OverviewTrendPoint(BaseModel):
    """Single trend data point."""

    day: date | None = None
    count: int


class OverviewTrendPayload(BaseModel):
    """Trend payload."""

    days: int
    items: list[OverviewTrendPoint] = Field(default_factory=list)
    warning: str | None = None


class PendingKeywordItem(BaseModel):
    """Pending keyword card item."""

    id: int
    keyword: str
    search_volume: int
    difficulty: int


class OverviewBoardPayload(BaseModel):
    """Overview board columns."""

    pending_keywords: list[PendingKeywordItem] = Field(default_factory=list)
    draft_articles: list[ArticleSummaryItem] = Field(default_factory=list)
    ready_articles: list[ArticleSummaryItem] = Field(default_factory=list)
    warning: str | None = None


class LatestArticlesPayload(BaseModel):
    """Latest article cards."""

    items: list[ArticleSummaryItem] = Field(default_factory=list)
    limit: int
    warning: str | None = None
