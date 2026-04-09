"""Publication-related schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PublicationSummaryItem(BaseModel):
    """Single publication audit row for list pages."""

    id: int
    article_id: int
    article_title: str | None = None
    article_slug: str | None = None
    article_publish_status: int | None = None
    channel_key: str
    channel_label: str
    adapter_key: str
    adapter_label: str
    publish_mode: str
    status: str
    trigger_mode: str
    attempt_no: int
    retry_of_publication_id: int | None = None
    retryable: bool = False
    external_id: str | None = None
    external_url: str | None = None
    message: str | None = None
    error_message: str | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicationDetailItem(PublicationSummaryItem):
    """Detailed publication payload."""

    request_payload_json: dict[str, Any] | list[Any] | None = None
    response_payload_json: dict[str, Any] | list[Any] | None = None
    retry_attempts_total: int = 0


class PublicationListPayload(BaseModel):
    """Paginated publication list payload."""

    items: list[PublicationSummaryItem] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
    warning: str | None = None


class PublicationDetailPayload(BaseModel):
    """Single publication response."""

    publication: PublicationDetailItem | None = None
    warning: str | None = None
