"""SQLAlchemy 2.0 ORM models — single source of truth for DB schema."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ═══════════════════════════════════════════
#  Core schema
# ═══════════════════════════════════════════

class Article(Base):
    __tablename__ = "geo_articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="文章H1标题")
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="URL Slug")
    meta_json: Mapped[Optional[dict]] = mapped_column(JSON, comment="JSON-LD 元数据")
    content_markdown: Mapped[Optional[str]] = mapped_column(Text, comment="核心正文内容")
    content_hash: Mapped[str] = mapped_column(String(32), nullable=False, comment="MD5哈希")
    quality_score: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0, comment="质量评分 0-100")
    publish_status: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0, comment="0草稿 1待审 2已发 3归档")
    dim_subject: Mapped[Optional[str]] = mapped_column(String(50))
    dim_action: Mapped[Optional[str]] = mapped_column(String(50))
    dim_attribute: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    publications: Mapped[list["ArticlePublication"]] = relationship(back_populates="article")


class Keyword(Base):
    __tablename__ = "geo_keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="目标关键词")
    target_article_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="唯一指定着陆页ID")
    search_volume: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment="月搜索量")
    difficulty: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0, comment="SEO难度 0-100")
    cannibalization_risk: Mapped[Optional[int]] = mapped_column(SmallInteger, default=0, comment="内耗风险")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Link(Base):
    __tablename__ = "geo_links"

    source_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="来源文章ID")
    target_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="目标文章ID")
    anchor_text: Mapped[str] = mapped_column(String(50), nullable=False, comment="锚文本")
    weight: Mapped[Optional[int]] = mapped_column(SmallInteger, default=1, comment="链接权重")
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ═══════════════════════════════════════════
#  Publication schema
# ═══════════════════════════════════════════

class ArticlePublication(Base):
    __tablename__ = "article_publications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geo_articles.id", ondelete="CASCADE"), nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False, comment="发布平台 zhihu/wechat")
    publish_mode: Mapped[str] = mapped_column(String(20), default="draft", comment="draft/live")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="pending/draft_saved/published/failed")
    trigger_mode: Mapped[str] = mapped_column(String(20), default="manual", comment="manual/retry/auto")
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    retry_of_publication_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("article_publications.id", ondelete="SET NULL")
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(191))
    external_url: Mapped[Optional[str]] = mapped_column(String(500))
    message: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    request_payload_json: Mapped[Optional[dict]] = mapped_column(JSON)
    response_payload_json: Mapped[Optional[dict]] = mapped_column(JSON)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    article: Mapped["Article"] = relationship(back_populates="publications")


# ═══════════════════════════════════════════
#  Job runtime schema
# ═══════════════════════════════════════════

class JobRun(Base):
    __tablename__ = "geo_job_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    run_uid: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    run_type: Mapped[str] = mapped_column(String(40), default="article_generation")
    trigger_mode: Mapped[str] = mapped_column(String(40), default="auto")
    keyword_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    keyword: Mapped[str] = mapped_column(String(191), nullable=False)
    article_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(20), default="running")
    current_step: Mapped[Optional[str]] = mapped_column(String(80))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steps: Mapped[list["JobStep"]] = relationship(back_populates="run")


class JobStep(Base):
    __tablename__ = "geo_job_steps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_run_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geo_job_runs.id", ondelete="CASCADE"), nullable=False)
    step_code: Mapped[str] = mapped_column(String(80), nullable=False)
    step_name: Mapped[str] = mapped_column(String(120), nullable=False)
    attempt_no: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="running")
    article_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("job_run_id", "step_code", "attempt_no", name="idx_run_step_attempt"),
    )

    run: Mapped["JobRun"] = relationship(back_populates="steps")


# ═══════════════════════════════════════════
#  Feedback / Probe schema
# ═══════════════════════════════════════════

class ProbeResult(Base):
    __tablename__ = "geo_probe_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    keyword: Mapped[str] = mapped_column(String(191), nullable=False)
    article_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    platform: Mapped[str] = mapped_column(String(40), nullable=False)
    mentioned: Mapped[bool] = mapped_column(Boolean, default=False)
    cited: Mapped[bool] = mapped_column(Boolean, default=False)
    visibility_rank: Mapped[Optional[int]] = mapped_column(SmallInteger)
    visibility_score: Mapped[Optional[float]] = mapped_column(Float)
    evidence_labels_json: Mapped[Optional[dict]] = mapped_column(JSON)
    source_hits_json: Mapped[Optional[dict]] = mapped_column(JSON)
    snapshot_text: Mapped[Optional[str]] = mapped_column(Text)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON)
    probed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KeywordFeedback(Base):
    __tablename__ = "geo_keyword_feedback"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    keyword_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    keyword: Mapped[str] = mapped_column(String(191), nullable=False, unique=True)
    article_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    citation_score: Mapped[Optional[float]] = mapped_column(Float)
    probe_coverage_score: Mapped[Optional[float]] = mapped_column(Float)
    feedback_labels_json: Mapped[Optional[dict]] = mapped_column(JSON)
    article_signals_json: Mapped[Optional[dict]] = mapped_column(JSON)
    probe_summary_json: Mapped[Optional[dict]] = mapped_column(JSON)
    suggested_keywords_json: Mapped[Optional[dict]] = mapped_column(JSON)
    prompt_guidance: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ═══════════════════════════════════════════
#  Capability schema
# ═══════════════════════════════════════════

class CapabilityProfile(Base):
    __tablename__ = "geo_capability_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    brand_name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    public_brand_name: Mapped[Optional[str]] = mapped_column(String(120))
    positioning: Mapped[str] = mapped_column(String(120), nullable=False)
    claim_scope: Mapped[str] = mapped_column(String(40), default="public_safe")
    version_tag: Mapped[Optional[str]] = mapped_column(String(80))
    source_policy: Mapped[Optional[str]] = mapped_column(String(255))
    brand_aliases_json: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CapabilitySource(Base):
    __tablename__ = "geo_capability_sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    source_vendor: Mapped[str] = mapped_column(String(120), nullable=False)
    source_title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    publish_org: Mapped[Optional[str]] = mapped_column(String(120))
    observed_on: Mapped[Optional[datetime]] = mapped_column(Date)
    reliability_score: Mapped[float] = mapped_column(Float, default=0.80)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapabilitySpec(Base):
    __tablename__ = "geo_capability_specs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geo_capability_profiles.id", ondelete="CASCADE"), nullable=False)
    group_code: Mapped[str] = mapped_column(String(80), nullable=False)
    group_name: Mapped[str] = mapped_column(String(120), nullable=False)
    capability_code: Mapped[str] = mapped_column(String(80), nullable=False)
    capability_name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(80))
    metric_type: Mapped[str] = mapped_column(Enum("min", "max", "range", "option", "boolean", "matrix", "composite", name="metric_type_enum"), default="range")
    unit: Mapped[Optional[str]] = mapped_column(String(40))
    comparator: Mapped[Optional[str]] = mapped_column(String(20))
    conservative_value_num: Mapped[Optional[float]] = mapped_column(Float)
    conservative_value_text: Mapped[Optional[str]] = mapped_column(String(255))
    advanced_value_num: Mapped[Optional[float]] = mapped_column(Float)
    advanced_value_text: Mapped[Optional[str]] = mapped_column(String(255))
    public_claim: Mapped[Optional[str]] = mapped_column(String(500))
    internal_note: Mapped[Optional[str]] = mapped_column(Text)
    conditions_text: Mapped[Optional[str]] = mapped_column(String(500))
    application_tags_json: Mapped[Optional[dict]] = mapped_column(JSON)
    claim_level: Mapped[str] = mapped_column(Enum("public_safe", "advanced_project", "experimental", name="claim_level_enum"), default="public_safe")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.80)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("profile_id", "capability_code", name="idx_profile_capability"),
    )


class CapabilitySpecSource(Base):
    __tablename__ = "geo_capability_spec_sources"

    spec_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geo_capability_specs.id", ondelete="CASCADE"), primary_key=True)
    source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("geo_capability_sources.id", ondelete="CASCADE"), primary_key=True)
    citation_note: Mapped[Optional[str]] = mapped_column(String(255))
    priority_weight: Mapped[Optional[int]] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
