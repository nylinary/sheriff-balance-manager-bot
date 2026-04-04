from __future__ import annotations

import math

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.operation import Operation
from bot.repositories import OperationRepo


class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.op_repo = OperationRepo(session)
        self.page_size = settings.history_page_size

    async def get_page(
        self, page: int, username_filter: str | None = None
    ) -> tuple[list[Operation], int, int]:
        """Returns (operations, current_page, total_pages)."""
        total = await self.op_repo.count(username_filter)
        total_pages = max(1, math.ceil(total / self.page_size))
        page = max(1, min(page, total_pages))
        operations = await self.op_repo.get_page(page, self.page_size, username_filter)
        return operations, page, total_pages

    async def get_operation(self, operation_id: int) -> Operation | None:
        return await self.op_repo.get_by_operation_id(operation_id)
