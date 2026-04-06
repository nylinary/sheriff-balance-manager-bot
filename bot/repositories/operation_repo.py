from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.operation import Operation, OperationType


class OperationRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _next_operation_id(self) -> int:
        result = await self.session.execute(text("SELECT nextval('operation_id_seq')"))
        return result.scalar_one()

    async def create(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        full_name: str | None,
        role_snapshot: str,
        chat_id: int,
        chat_type: str,
        currency_code: str,
        currency_title: str,
        currency_command: str,
        amount: int,
        operation_type: OperationType,
        reverted_operation_id: int | None = None,
        revert_parent_operation_id: int | None = None,
        meta_json: dict | None = None,
    ) -> Operation:
        op_id = await self._next_operation_id()
        op = Operation(
            operation_id=op_id,
            telegram_user_id=telegram_user_id,
            username=username,
            full_name=full_name,
            role_snapshot=role_snapshot,
            chat_id=chat_id,
            chat_type=chat_type,
            currency_code=currency_code,
            currency_title=currency_title,
            currency_command=currency_command,
            amount=amount,
            operation_type=operation_type,
            reverted_operation_id=reverted_operation_id,
            revert_parent_operation_id=revert_parent_operation_id,
            meta_json=meta_json,
        )
        self.session.add(op)
        await self.session.flush()
        return op

    async def get_by_operation_id(self, operation_id: int) -> Operation | None:
        stmt = select(Operation).where(Operation.operation_id == operation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_reverted(
        self,
        operation_id: int,
        revert_op_id: int,
        *,
        reverted_by_telegram_id: int | None = None,
        reverted_by_username: str | None = None,
        reverted_by_full_name: str | None = None,
    ) -> None:
        op = await self.get_by_operation_id(operation_id)
        if op:
            op.is_reverted = True
            op.reverted_operation_id = revert_op_id
            op.reverted_by_telegram_id = reverted_by_telegram_id
            op.reverted_by_username = reverted_by_username
            op.reverted_by_full_name = reverted_by_full_name
            await self.session.flush()

    async def count(self, username_filter: str | None = None) -> int:
        stmt = select(func.count(Operation.id))
        if username_filter:
            clean = username_filter.lstrip("@").lower()
            stmt = stmt.where(func.lower(Operation.username) == clean)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def get_page(
        self,
        page: int,
        page_size: int,
        username_filter: str | None = None,
    ) -> list[Operation]:
        stmt = select(Operation).order_by(Operation.operation_id.desc())
        if username_filter:
            clean = username_filter.lstrip("@").lower()
            stmt = stmt.where(func.lower(Operation.username) == clean)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self) -> list[Operation]:
        stmt = select(Operation).order_by(Operation.operation_id.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
