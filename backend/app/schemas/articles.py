"""Article-related schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ArticleSummaryItem(BaseModel):
    """Article row used in overview and list pages."""

    id: int
    title: str
    slug: str
    quality_score: int
    publish_status: int
    dim_subject: str | None = None
    dim_action: str | None = None
    dim_attribute: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ArticleDetailItem(ArticleSummaryItem):
    """Detailed article payload."""

    meta_json: dict[str, Any] | list[Any] | None = None
    content_markdown: str | None = None
    target_keywords: list[str] = Field(default_factory=list)
    outgoing_links_count: int = 0
    incoming_links_count: int = 0
    related_run_id: int | None = None
    related_run_status: str | None = None


class ArticleListPayload(BaseModel):
    """Paginated article list."""

    items: list[ArticleSummaryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    warning: str | None = None


class ArticleSummaryPayload(BaseModel):
    """Aggregated article counts."""

    total_articles: int
    draft_articles: int
    approved_articles: int
    published_articles: int
    average_quality_score: float | None = None
    warning: str | None = None


class ArticleDetailPayload(BaseModel):
    """Single article response."""

    article: ArticleDetailItem | None = None
    warning: str | None = None


class ArticlePublishRequest(BaseModel):
    """Request body for manual article publishing."""

    channels: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    go_live: bool = False

    @model_validator(mode="after")
    def validate_channels(self) -> "ArticlePublishRequest":
        allowed = {"longform_channel", "mobile_channel", "zhihu", "wechat"}
        cleaned = []
        for item in [*(self.channels or []), *(self.platforms or [])]:
            normalized = str(item).strip().lower()
            if normalized in allowed and normalized not in cleaned:
                cleaned.append(normalized)
        self.channels = cleaned
        self.platforms = cleaned
        return self
