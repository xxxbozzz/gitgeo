"""Capability repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import (
    CapabilityProfile,
    CapabilitySource,
    CapabilitySpec,
    CapabilitySpecSource,
    Article,
)


class CapabilityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_profile_by_code(self, code: str) -> Optional[CapabilityProfile]:
        stmt = select(CapabilityProfile).where(CapabilityProfile.profile_code == code)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_specs(
        self, *, profile_code: str, active: Optional[bool] = None,
        group_code: Optional[str] = None, query_text: Optional[str] = None,
        limit: int = 20, offset: int = 0,
    ) -> tuple[list[dict], int]:
        from backend.app.db.models import CapabilitySpec, CapabilitySpecSource
        stmt = select(
            CapabilitySpec.id, CapabilitySpec.group_code, CapabilitySpec.group_name,
            CapabilitySpec.capability_code, CapabilitySpec.capability_name,
            CapabilitySpec.category, CapabilitySpec.public_claim, CapabilitySpec.claim_level,
            CapabilitySpec.confidence_score, CapabilitySpec.is_active,
            CapabilitySpec.application_tags_json, CapabilitySpec.updated_at,
            func.count(func.distinct(CapabilitySpecSource.source_id)).label("source_count"),
        ).join(CapabilityProfile, CapabilityProfile.id == CapabilitySpec.profile_id).outerjoin(
            CapabilitySpecSource, CapabilitySpecSource.spec_id == CapabilitySpec.id
        ).where(CapabilityProfile.profile_code == profile_code)

        if active is not None:
            stmt = stmt.where(CapabilitySpec.is_active.is_(True) if active else CapabilitySpec.is_active.is_(False))
        if group_code:
            stmt = stmt.where((CapabilitySpec.group_code == group_code) | (CapabilitySpec.group_name == group_code))
        if query_text:
            like = f"%{query_text.strip()}%"
            stmt = stmt.where(
                (CapabilitySpec.capability_name.ilike(like))
                | (CapabilitySpec.capability_code.ilike(like))
                | (CapabilitySpec.public_claim.ilike(like))
                | (CapabilitySpec.group_name.ilike(like))
            )

        stmt = stmt.group_by(CapabilitySpec.id)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(
            CapabilitySpec.is_active.desc(), CapabilitySpec.group_name.asc(),
            CapabilitySpec.capability_name.asc()
        ).offset(offset).limit(limit)

        rows = (await self.session.execute(stmt)).all()
        items = [
            {
                "id": r.id, "group_code": r.group_code, "group_name": r.group_name,
                "capability_code": r.capability_code, "capability_name": r.capability_name,
                "category": r.category, "public_claim": r.public_claim,
                "claim_level": r.claim_level or "public_safe",
                "confidence_score": float(r.confidence_score) if r.confidence_score else 0,
                "is_active": bool(r.is_active), "source_count": int(r.source_count or 0),
                "application_tags": r.application_tags_json or [],
                "updated_at": r.updated_at,
            }
            for r in rows
        ]
        return items, total

    async def active_count(self, *, profile_code: str) -> int:
        stmt = select(func.count()).select_from(CapabilitySpec).join(
            CapabilityProfile, CapabilityProfile.id == CapabilitySpec.profile_id
        ).where(CapabilityProfile.profile_code == profile_code, CapabilitySpec.is_active.is_(True))
        return (await self.session.execute(stmt)).scalar() or 0

    async def inactive_count(self, *, profile_code: str) -> int:
        stmt = select(func.count()).select_from(CapabilitySpec).join(
            CapabilityProfile, CapabilityProfile.id == CapabilitySpec.profile_id
        ).where(CapabilityProfile.profile_code == profile_code, CapabilitySpec.is_active.is_(False))
        return (await self.session.execute(stmt)).scalar() or 0

    async def groups_count(self, *, profile_code: str) -> int:
        stmt = select(func.count(func.distinct(CapabilitySpec.group_code))).select_from(
            CapabilitySpec
        ).join(CapabilityProfile).where(CapabilityProfile.profile_code == profile_code)
        return (await self.session.execute(stmt)).scalar() or 0

    async def get_spec_detail(self, *, profile_code: str, spec_id: int) -> Optional[dict]:
        stmt = select(
            CapabilitySpec.id, CapabilitySpec.group_code, CapabilitySpec.group_name,
            CapabilitySpec.capability_code, CapabilitySpec.capability_name,
            CapabilitySpec.category, CapabilitySpec.metric_type, CapabilitySpec.unit,
            CapabilitySpec.comparator, CapabilitySpec.conservative_value_num,
            CapabilitySpec.conservative_value_text, CapabilitySpec.advanced_value_num,
            CapabilitySpec.advanced_value_text, CapabilitySpec.public_claim,
            CapabilitySpec.internal_note, CapabilitySpec.conditions_text,
            CapabilitySpec.application_tags_json, CapabilitySpec.claim_level,
            CapabilitySpec.confidence_score, CapabilitySpec.is_active,
            CapabilitySpec.updated_at,
            func.count(func.distinct(CapabilitySpecSource.source_id)).label("source_count"),
        ).join(CapabilityProfile, CapabilityProfile.id == CapabilitySpec.profile_id).outerjoin(
            CapabilitySpecSource, CapabilitySpecSource.spec_id == CapabilitySpec.id
        ).where(CapabilityProfile.profile_code == profile_code, CapabilitySpec.id == spec_id).group_by(
            CapabilitySpec.id
        )
        row = (await self.session.execute(stmt)).first()
        if not row:
            return None
        return {c._metadata.label: getattr(row, c._metadata.label) for c in stmt.selected_columns}

    async def list_spec_sources(self, *, profile_code: str, spec_id: int) -> list[dict]:
        stmt = select(
            CapabilitySource.id, CapabilitySource.source_code, CapabilitySource.source_vendor,
            CapabilitySource.source_title, CapabilitySource.source_type, CapabilitySource.source_url,
            CapabilitySource.publish_org, CapabilitySource.observed_on,
            CapabilitySource.reliability_score,
            CapabilitySpecSource.citation_note, CapabilitySpecSource.priority_weight,
        ).select_from(CapabilitySpec).join(
            CapabilityProfile, CapabilityProfile.id == CapabilitySpec.profile_id
        ).outerjoin(
            CapabilitySpecSource, CapabilitySpecSource.spec_id == CapabilitySpec.id
        ).outerjoin(
            CapabilitySource, CapabilitySource.id == CapabilitySpecSource.source_id
        ).where(
            CapabilityProfile.profile_code == profile_code, CapabilitySpec.id == spec_id
        ).order_by(CapabilitySpecSource.priority_weight.asc())

        rows = (await self.session.execute(stmt)).all()
        return [
            {
                "id": r.id, "source_code": r.source_code, "source_vendor": r.source_vendor,
                "source_title": r.source_title, "source_type": r.source_type,
                "source_url": r.source_url, "publish_org": r.publish_org,
                "observed_on": r.observed_on.isoformat() if r.observed_on else None,
                "reliability_score": float(r.reliability_score) if r.reliability_score else 0,
                "citation_note": r.citation_note,
                "priority_weight": int(r.priority_weight) if r.priority_weight else 0,
            }
            for r in rows if r.id is not None
        ]

    async def disable_spec(self, *, profile_code: str, spec_id: int) -> int:
        sub = select(CapabilityProfile.id).where(CapabilityProfile.profile_code == profile_code).scalar_subquery()
        stmt = update(CapabilitySpec).where(
            CapabilitySpec.profile_id == sub, CapabilitySpec.id == spec_id, CapabilitySpec.is_active.is_(True)
        ).values(is_active=False)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def find_articles_by_term(self, term: str, *, limit: int = 5) -> list[dict]:
        like = f"%{term}%"
        stmt = select(Article.id, Article.title, Article.slug, Article.publish_status,
                      Article.quality_score, Article.updated_at).where(
            (Article.title.ilike(like)) | (Article.slug.ilike(like))
            | (Article.content_markdown.ilike(like)) | (Article.dim_subject.ilike(like))
        ).order_by(Article.updated_at.desc()).limit(limit)
        rows = (await self.session.execute(stmt)).all()
        return [
            {"id": r.id, "title": r.title, "slug": r.slug,
             "publish_status": r.publish_status or 0, "quality_score": r.quality_score or 0,
             "updated_at": r.updated_at}
            for r in rows
        ]
