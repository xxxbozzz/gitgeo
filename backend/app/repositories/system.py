"""System status repository."""

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SystemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ping(self) -> bool:
        try:
            await self.session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    @staticmethod
    def has_llm_credentials() -> bool:
        return bool(os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("GEO_LLM_API_KEY"))
