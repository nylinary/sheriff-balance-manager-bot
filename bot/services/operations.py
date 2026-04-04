from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import Currency
from bot.models.operation import Operation, OperationType
from bot.repositories import BalanceRepo, OperationRepo, UserRepo


class OperationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.op_repo = OperationRepo(session)
        self.balance_repo = BalanceRepo(session)
        self.user_repo = UserRepo(session)

    async def create_operation(
        self,
        *,
        telegram_user_id: int,
        username: str | None,
        full_name: str | None,
        chat_id: int,
        chat_type: str,
        currency: Currency,
        amount: int,
    ) -> tuple[Operation, int]:
        """Create operation and update balance. Returns (operation, new_balance)."""
        user = await self.user_repo.get_or_create(
            telegram_id=telegram_user_id,
            username=username,
            full_name=full_name,
        )

        op_type = OperationType.income if amount > 0 else OperationType.expense

        operation = await self.op_repo.create(
            telegram_user_id=telegram_user_id,
            username=username,
            full_name=full_name,
            role_snapshot=user.role.value,
            chat_id=chat_id,
            chat_type=chat_type,
            currency_code=currency.code,
            currency_title=currency.title,
            currency_command=currency.command,
            amount=amount,
            operation_type=op_type,
        )

        balance = await self.balance_repo.update_amount(currency.code, amount)
        await self.session.commit()
        return operation, balance.amount

    async def revert_operation(
        self,
        operation_id: int,
        *,
        admin_telegram_id: int,
        admin_username: str | None,
        admin_full_name: str | None,
    ) -> tuple[Operation, Operation, int]:
        """Revert an operation. Returns (original_op, revert_op, new_balance).

        Raises ValueError if operation not found or already reverted.
        """
        original = await self.op_repo.get_by_operation_id(operation_id)
        if original is None:
            raise ValueError("Операция не найдена.")
        if original.is_reverted:
            raise ValueError("Операция уже откатана.")

        reverse_amount = -original.amount
        op_type = OperationType.revert

        revert_op = await self.op_repo.create(
            telegram_user_id=admin_telegram_id,
            username=admin_username,
            full_name=admin_full_name,
            role_snapshot="admin",
            chat_id=0,
            chat_type="private",
            currency_code=original.currency_code,
            currency_title=original.currency_title,
            currency_command=original.currency_command,
            amount=reverse_amount,
            operation_type=op_type,
            revert_parent_operation_id=original.operation_id,
        )

        await self.op_repo.mark_reverted(original.operation_id, revert_op.operation_id)

        balance = await self.balance_repo.update_amount(original.currency_code, reverse_amount)
        await self.session.commit()

        # Refresh original to get updated is_reverted
        refreshed = await self.op_repo.get_by_operation_id(original.operation_id)
        return refreshed or original, revert_op, balance.amount
