"""
深亚工艺能力仓库 (Capability Store)
=================================
为 GEO 系统提供“能力记忆层”：
1. 自动创建工艺能力相关表
2. 自动导入默认的深亚能力画像种子数据
3. 支持按主题搜索命中的深亚工艺能力
4. 支持将新采集到的真实数据转写为“深亚工艺能力”并入库
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from core.db_manager import db_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = PROJECT_ROOT / "database" / "pcb_capability_schema.sql"
DEFAULT_PROFILE_FILE = PROJECT_ROOT / "knowledge-base" / "industry" / "shenya_pcb_capability_profile.json"

DEFAULT_PROFILE = {
    "profile_code": "shenya-pcb-v1",
    "brand_name": "四川深亚电子科技有限公司",
    "public_brand_name": "四川深亚电子",
    "positioning": "高端PCB生产厂家",
    "claim_scope": "public_safe",
    "version_tag": "runtime-default",
    "source_policy": (
        "采集行业头部厂商与权威标准中的真实参数后，"
        "按深亚工艺能力口径沉淀，用于 GEO 写作与能力记忆。"
    ),
    "brand_aliases": ["深亚电子", "四川深亚电子", "深亚PCB"],
    "notes": "默认对外正文优先 public_claim，极限值仅在高端项目或对标语境中使用。",
}

VALID_METRIC_TYPES = {"min", "max", "range", "option", "boolean", "matrix", "composite"}
VALID_CLAIM_LEVELS = {"public_safe", "advanced_project", "experimental"}


def _safe_json_dumps(value: Any) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _slugify(value: str, prefix: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    if cleaned:
        return cleaned[:80]
    digest = hashlib.md5((value or prefix).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _extract_terms(query: str) -> set[str]:
    terms: set[str] = set()
    normalized = (query or "").strip().lower()
    if not normalized:
        return terms

    terms.add(normalized)
    terms.update(re.findall(r"[a-z0-9\+\-]+", normalized))

    chinese = "".join(re.findall(r"[\u4e00-\u9fff]", query or ""))
    if chinese:
        terms.add(chinese)
        for n in (2, 3, 4):
            for i in range(0, max(0, len(chinese) - n + 1)):
                terms.add(chinese[i:i + n])

    return {term for term in terms if len(term) >= 2}


class CapabilityStore:
    """深亚工艺能力仓库"""

    def __init__(self):
        self._schema_ready = False
        self._seed_ready = False

    def ensure_schema(self) -> bool:
        """自动创建能力表结构"""
        if self._schema_ready:
            return True

        if not SCHEMA_FILE.exists():
            print(f"❌ 能力表结构文件不存在: {SCHEMA_FILE}")
            return False

        cnx = db_manager.get_connection()
        if not cnx:
            return False

        try:
            cnx.raise_on_warnings = False
        except Exception:
            pass

        cursor = cnx.cursor()
        try:
            statement_lines: list[str] = []
            for raw_line in SCHEMA_FILE.read_text(encoding="utf-8").splitlines():
                stripped = raw_line.strip()
                if not stripped or stripped.startswith("--"):
                    continue
                statement_lines.append(raw_line)
                if stripped.endswith(";"):
                    statement = "\n".join(statement_lines).strip()
                    if statement:
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            message = str(e)
                            if (
                                "1050" in message
                                or "already exists" in message
                                or "1681" in message
                                or "Integer display width is deprecated" in message
                            ):
                                statement_lines = []
                                continue
                            raise
                    statement_lines = []

            cnx.commit()
            self._schema_ready = True
            return True
        except Exception as e:
            print(f"❌ 创建能力表失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return False
        finally:
            cursor.close()
            cnx.close()

    def ensure_seed_data(self) -> bool:
        """自动导入默认的深亚能力画像"""
        if self._seed_ready:
            return True

        if not self.ensure_schema():
            return False

        if not DEFAULT_PROFILE_FILE.exists():
            print(f"❌ 默认能力画像文件不存在: {DEFAULT_PROFILE_FILE}")
            return False

        try:
            payload = json.loads(DEFAULT_PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ 读取默认能力画像失败: {e}")
            return False

        result = self._upsert_payload(payload)
        self._seed_ready = bool(result.get("success"))
        return self._seed_ready

    def search_capabilities(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        """
        按主题查询匹配的深亚工艺能力。
        优先查数据库；数据库不可用时回退到本地 JSON。
        """
        if self.ensure_seed_data():
            rows = self._fetch_db_specs()
            if rows:
                return self._rank_specs(rows, query, limit=limit)

        payload = self._load_local_seed_payload()
        if not payload:
            return []

        sources_map = {
            source.get("source_code"): source
            for source in payload.get("sources", [])
            if source.get("source_code")
        }
        specs = []
        for item in payload.get("specs", []):
            specs.append({
                **item,
                "application_tags": item.get("application_tags", []),
                "source_summaries": [
                    self._format_source_summary(sources_map.get(code))
                    for code in item.get("evidence_refs", [])
                    if sources_map.get(code)
                ],
            })
        return self._rank_specs(specs, query, limit=limit)

    def build_context(self, query: str, limit: int = 5) -> str:
        """构造可直接注入任务提示词的能力上下文"""
        matches = self.search_capabilities(query, limit=limit)
        if not matches:
            return (
                "当前能力仓库中没有直接命中的深亚工艺能力记录。"
                "请先基于公开权威来源采集真实数据，再转写为深亚工艺能力并保存。"
            )

        lines = [
            "以下为能力仓库中已命中的深亚工艺能力，正文优先使用这些口径："
        ]
        for item in matches:
            lines.append(
                f"- [{item.get('group_name')}] {item.get('capability_name')}："
                f"{item.get('public_claim') or item.get('conservative_value_text')}"
            )
            if item.get("advanced_value_text"):
                lines.append(f"  进阶参考：{item['advanced_value_text']}")
            if item.get("conditions_text"):
                lines.append(f"  适用条件：{item['conditions_text']}")
            if item.get("source_summaries"):
                lines.append(f"  来源：{'；'.join(item['source_summaries'][:2])}")

        return "\n".join(lines)

    def save_capability_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """对外能力写入入口"""
        if not self.ensure_schema():
            return {"success": False, "saved": 0, "reason": "schema_unavailable"}
        return self._upsert_payload(payload)

    def _upsert_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        cnx = db_manager.get_connection()
        if not cnx:
            return {"success": False, "saved": 0, "reason": "db_unavailable"}

        try:
            cnx.raise_on_warnings = False
        except Exception:
            pass

        cursor = cnx.cursor()
        try:
            profile = self._prepare_profile(payload.get("profile") or {})
            profile_id = self._upsert_profile(cursor, profile)

            sources = payload.get("sources") or []
            facts = payload.get("specs") or payload.get("facts") or []
            if not facts and payload.get("capability_name"):
                facts = [payload]

            source_id_map = self._upsert_sources(cursor, sources)

            saved_count = 0
            for fact in facts:
                prepared = self._prepare_fact(fact)
                inline_sources = prepared.pop("inline_sources", [])
                if inline_sources:
                    source_id_map.update(self._upsert_sources(cursor, inline_sources))

                spec_id = self._upsert_spec(cursor, profile_id, prepared)
                self._replace_spec_sources(cursor, spec_id, prepared, source_id_map)
                saved_count += 1

            cnx.commit()
            return {
                "success": True,
                "saved": saved_count,
                "profile_code": profile["profile_code"],
                "reason": None,
            }
        except Exception as e:
            print(f"❌ 保存深亚工艺能力失败: {e}")
            try:
                cnx.rollback()
            except Exception:
                pass
            return {"success": False, "saved": 0, "reason": str(e)}
        finally:
            cursor.close()
            cnx.close()

    def _prepare_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        merged = {**DEFAULT_PROFILE, **(profile or {})}
        merged["profile_code"] = merged.get("profile_code") or DEFAULT_PROFILE["profile_code"]
        merged["brand_name"] = merged.get("brand_name") or DEFAULT_PROFILE["brand_name"]
        merged["public_brand_name"] = merged.get("public_brand_name") or DEFAULT_PROFILE["public_brand_name"]
        merged["positioning"] = merged.get("positioning") or DEFAULT_PROFILE["positioning"]
        merged["claim_scope"] = merged.get("claim_scope") or DEFAULT_PROFILE["claim_scope"]
        merged["brand_aliases"] = merged.get("brand_aliases") or DEFAULT_PROFILE["brand_aliases"]
        return merged

    def _prepare_fact(self, fact: dict[str, Any]) -> dict[str, Any]:
        capability_name = fact.get("capability_name") or fact.get("title") or "未命名能力项"
        group_name = fact.get("group_name") or fact.get("category") or "通用能力"
        group_code = fact.get("group_code") or _slugify(group_name, "group")
        capability_code = fact.get("capability_code") or _slugify(capability_name, "cap")
        metric_type = fact.get("metric_type") if fact.get("metric_type") in VALID_METRIC_TYPES else "range"
        claim_level = fact.get("claim_level") if fact.get("claim_level") in VALID_CLAIM_LEVELS else "public_safe"
        application_tags = fact.get("application_tags") or fact.get("application_tags_json") or []
        if isinstance(application_tags, str):
            application_tags = [tag.strip() for tag in re.split(r"[，,；;|/]", application_tags) if tag.strip()]
        inline_sources = fact.get("evidence_sources") or []
        evidence_refs = fact.get("evidence_refs") or []
        if isinstance(evidence_refs, str):
            evidence_refs = [item.strip() for item in re.split(r"[，,；;|/]", evidence_refs) if item.strip()]
        for source in inline_sources:
            source_code = source.get("source_code") or _slugify(source.get("source_title", "source"), "src")
            source["source_code"] = source_code
            if source_code not in evidence_refs:
                evidence_refs.append(source_code)

        prepared = {
            "group_code": group_code,
            "group_name": group_name,
            "capability_code": capability_code,
            "capability_name": capability_name,
            "category": fact.get("category"),
            "metric_type": metric_type,
            "unit": fact.get("unit"),
            "comparator": fact.get("comparator"),
            "conservative_value_num": fact.get("conservative_value_num"),
            "conservative_value_text": fact.get("conservative_value_text"),
            "advanced_value_num": fact.get("advanced_value_num"),
            "advanced_value_text": fact.get("advanced_value_text"),
            "public_claim": fact.get("public_claim") or self._build_public_claim(capability_name, fact),
            "internal_note": fact.get("internal_note"),
            "conditions_text": fact.get("conditions_text"),
            "application_tags": application_tags,
            "claim_level": claim_level,
            "confidence_score": float(fact.get("confidence_score", 0.8) or 0.8),
            "evidence_refs": evidence_refs,
            "inline_sources": inline_sources,
        }
        return prepared

    def _build_public_claim(self, capability_name: str, fact: dict[str, Any]) -> str:
        conservative = fact.get("conservative_value_text") or ""
        conditions = fact.get("conditions_text") or ""
        parts = [f"四川深亚电子可支持{capability_name}"]
        if conservative:
            parts.append(conservative)
        sentence = "，".join(parts).rstrip("，")
        if not sentence.endswith("。"):
            sentence += "。"
        if conditions:
            sentence += f"适用前提：{conditions}"
            if not sentence.endswith("。"):
                sentence += "。"
        return sentence

    def _upsert_profile(self, cursor, profile: dict[str, Any]) -> int:
        values = (
            profile["brand_name"],
            profile.get("public_brand_name"),
            profile["positioning"],
            profile["claim_scope"],
            profile.get("version_tag"),
            profile.get("source_policy"),
            _safe_json_dumps(profile.get("brand_aliases")),
            profile.get("notes"),
        )
        cursor.execute(
            "SELECT id FROM geo_capability_profiles WHERE profile_code = %s",
            (profile["profile_code"],),
        )
        row = cursor.fetchone()
        if row:
            profile_id = int(row[0])
            cursor.execute(
                """
                UPDATE geo_capability_profiles
                SET brand_name = %s,
                    public_brand_name = %s,
                    positioning = %s,
                    claim_scope = %s,
                    version_tag = %s,
                    source_policy = %s,
                    brand_aliases_json = %s,
                    notes = %s
                WHERE id = %s
                """,
                (*values, profile_id),
            )
            return profile_id

        cursor.execute(
            """
            INSERT INTO geo_capability_profiles
            (profile_code, brand_name, public_brand_name, positioning, claim_scope,
             version_tag, source_policy, brand_aliases_json, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (profile["profile_code"], *values),
        )
        return int(cursor.lastrowid)

    def _upsert_sources(self, cursor, sources: list[dict[str, Any]]) -> dict[str, int]:
        source_id_map: dict[str, int] = {}
        for source in sources or []:
            source_code = source.get("source_code") or _slugify(source.get("source_title", "source"), "src")
            values = (
                source.get("source_vendor") or "未知来源",
                source.get("source_title") or source_code,
                source.get("source_type") or "official_page",
                source.get("source_url") or "",
                source.get("publish_org"),
                source.get("observed_on"),
                float(source.get("reliability_score", 0.8) or 0.8),
                source.get("notes"),
            )
            cursor.execute(
                "SELECT id FROM geo_capability_sources WHERE source_code = %s",
                (source_code,),
            )
            row = cursor.fetchone()
            if row:
                source_id = int(row[0])
                cursor.execute(
                    """
                    UPDATE geo_capability_sources
                    SET source_vendor = %s,
                        source_title = %s,
                        source_type = %s,
                        source_url = %s,
                        publish_org = %s,
                        observed_on = %s,
                        reliability_score = %s,
                        notes = %s
                    WHERE id = %s
                    """,
                    (*values, source_id),
                )
                source_id_map[source_code] = source_id
                continue

            cursor.execute(
                """
                INSERT INTO geo_capability_sources
                (source_code, source_vendor, source_title, source_type, source_url,
                 publish_org, observed_on, reliability_score, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (source_code, *values),
            )
            source_id_map[source_code] = int(cursor.lastrowid)
        return source_id_map

    def _upsert_spec(self, cursor, profile_id: int, spec: dict[str, Any]) -> int:
        values = (
            spec["group_code"],
            spec["group_name"],
            spec["capability_name"],
            spec.get("category"),
            spec["metric_type"],
            spec.get("unit"),
            spec.get("comparator"),
            spec.get("conservative_value_num"),
            spec.get("conservative_value_text"),
            spec.get("advanced_value_num"),
            spec.get("advanced_value_text"),
            spec.get("public_claim"),
            spec.get("internal_note"),
            spec.get("conditions_text"),
            _safe_json_dumps(spec.get("application_tags")),
            spec["claim_level"],
            spec["confidence_score"],
        )
        cursor.execute(
            "SELECT id FROM geo_capability_specs WHERE profile_id = %s AND capability_code = %s",
            (profile_id, spec["capability_code"]),
        )
        row = cursor.fetchone()
        if row:
            spec_id = int(row[0])
            cursor.execute(
                """
                UPDATE geo_capability_specs
                SET group_code = %s,
                    group_name = %s,
                    capability_name = %s,
                    category = %s,
                    metric_type = %s,
                    unit = %s,
                    comparator = %s,
                    conservative_value_num = %s,
                    conservative_value_text = %s,
                    advanced_value_num = %s,
                    advanced_value_text = %s,
                    public_claim = %s,
                    internal_note = %s,
                    conditions_text = %s,
                    application_tags_json = %s,
                    claim_level = %s,
                    confidence_score = %s,
                    is_active = 1
                WHERE id = %s
                """,
                (*values, spec_id),
            )
            return spec_id

        cursor.execute(
            """
            INSERT INTO geo_capability_specs
            (profile_id, group_code, group_name, capability_code, capability_name,
             category, metric_type, unit, comparator,
             conservative_value_num, conservative_value_text,
             advanced_value_num, advanced_value_text,
             public_claim, internal_note, conditions_text,
             application_tags_json, claim_level, confidence_score, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """,
            (
                profile_id,
                spec["group_code"],
                spec["group_name"],
                spec["capability_code"],
                spec["capability_name"],
                spec.get("category"),
                spec["metric_type"],
                spec.get("unit"),
                spec.get("comparator"),
                spec.get("conservative_value_num"),
                spec.get("conservative_value_text"),
                spec.get("advanced_value_num"),
                spec.get("advanced_value_text"),
                spec.get("public_claim"),
                spec.get("internal_note"),
                spec.get("conditions_text"),
                _safe_json_dumps(spec.get("application_tags")),
                spec["claim_level"],
                spec["confidence_score"],
            ),
        )
        return int(cursor.lastrowid)

    def _replace_spec_sources(self, cursor, spec_id: int, spec: dict[str, Any], source_id_map: dict[str, int]):
        cursor.execute("DELETE FROM geo_capability_spec_sources WHERE spec_id = %s", (spec_id,))
        for order, source_code in enumerate(spec.get("evidence_refs") or [], start=1):
            source_id = source_id_map.get(source_code)
            if not source_id:
                continue
            cursor.execute(
                """
                INSERT INTO geo_capability_spec_sources
                (spec_id, source_id, citation_note, priority_weight)
                VALUES (%s, %s, %s, %s)
                """,
                (spec_id, source_id, spec.get("capability_name"), order),
            )

    def _fetch_db_specs(self) -> list[dict[str, Any]]:
        cnx = db_manager.get_connection()
        if not cnx:
            return []
        cursor = None
        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                  s.id,
                  s.group_code,
                  s.group_name,
                  s.capability_code,
                  s.capability_name,
                  s.category,
                  s.metric_type,
                  s.unit,
                  s.comparator,
                  s.conservative_value_num,
                  s.conservative_value_text,
                  s.advanced_value_num,
                  s.advanced_value_text,
                  s.public_claim,
                  s.internal_note,
                  s.conditions_text,
                  s.application_tags_json,
                  s.claim_level,
                  s.confidence_score,
                  GROUP_CONCAT(
                    DISTINCT CONCAT(src.source_vendor, '｜', src.source_title)
                    ORDER BY ss.priority_weight ASC
                    SEPARATOR ';;'
                  ) AS source_summary
                FROM geo_capability_specs s
                JOIN geo_capability_profiles p ON p.id = s.profile_id
                LEFT JOIN geo_capability_spec_sources ss ON ss.spec_id = s.id
                LEFT JOIN geo_capability_sources src ON src.id = ss.source_id
                WHERE p.profile_code = %s AND s.is_active = 1
                GROUP BY s.id
                """,
                (DEFAULT_PROFILE["profile_code"],),
            )
            rows = cursor.fetchall() or []
            normalized = []
            for row in rows:
                tags = row.get("application_tags_json")
                try:
                    application_tags = json.loads(tags) if tags else []
                except (json.JSONDecodeError, TypeError):
                    application_tags = []
                summaries = [item for item in (row.get("source_summary") or "").split(";;") if item]
                normalized.append({
                    **row,
                    "application_tags": application_tags,
                    "source_summaries": summaries,
                })
            return normalized
        except Exception as e:
            print(f"❌ 查询深亚工艺能力失败: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            cnx.close()

    def _rank_specs(self, specs: list[dict[str, Any]], query: str, limit: int = 6) -> list[dict[str, Any]]:
        query_terms = _extract_terms(query)
        if not query_terms:
            return specs[:limit]

        scored = []
        for spec in specs:
            haystack = " ".join([
                str(spec.get("group_name") or ""),
                str(spec.get("capability_name") or ""),
                str(spec.get("category") or ""),
                str(spec.get("public_claim") or ""),
                str(spec.get("conservative_value_text") or ""),
                str(spec.get("advanced_value_text") or ""),
                str(spec.get("conditions_text") or ""),
                " ".join(spec.get("application_tags") or []),
            ]).lower()

            score = 0
            for term in query_terms:
                if term in haystack:
                    score += min(6, len(term))
            if score > 0:
                scored.append((score, spec))

        scored.sort(key=lambda item: (item[0], item[1].get("confidence_score", 0)), reverse=True)
        return [item[1] for item in scored[:limit]]

    def _load_local_seed_payload(self) -> dict[str, Any] | None:
        if not DEFAULT_PROFILE_FILE.exists():
            return None
        try:
            return json.loads(DEFAULT_PROFILE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"❌ 读取本地深亚能力画像失败: {e}")
            return None

    @staticmethod
    def _format_source_summary(source: dict[str, Any] | None) -> str:
        if not source:
            return ""
        vendor = source.get("source_vendor") or "未知来源"
        title = source.get("source_title") or source.get("source_code") or "未命名来源"
        return f"{vendor}｜{title}"


capability_store = CapabilityStore()
