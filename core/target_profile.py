"""
目标对象画像配置 (Target Profile)
================================
将实体名称、别名和能力口径从业务逻辑中抽离，方便跨行业复用。
"""

from __future__ import annotations

import os


TARGET_ENTITY_NAME = os.getenv("TARGET_ENTITY_NAME", "目标组织")
TARGET_CAPABILITY_NOUN = os.getenv("TARGET_CAPABILITY_NOUN", "组织能力")

_aliases = [item.strip() for item in os.getenv("TARGET_ENTITY_ALIASES", "").split(",") if item.strip()]
if TARGET_ENTITY_NAME not in _aliases:
    _aliases.append(TARGET_ENTITY_NAME)

TARGET_ENTITY_ALIASES = _aliases
