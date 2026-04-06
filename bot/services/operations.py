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
        reverted_by_telegram_id: int,
        reverted_by_username: str | None,
        reverted_by_full_name: str | None,
        is_admin_user: bool = False,
    ) -> tuple[Operation, Operation, int]:
        """Create a revert operation for the given operation.

        Returns (original_op, revert_op, new_balance).
        Admins can revert non-admin operations and their own operations.
        Admins cannot revert other admins' operations.
        Non-admins can only revert their own operations.
        Raises ValueError if operation not found or already reverted.
        """
        original = await self.op_repo.get_by_operation_id(operation_id)
        if original is None:
            raise ValueError("Операция не найдена.")
        if original.operation_type == OperationType.revert:
            raise ValueError("Нельзя откатить операцию отката.")
        if original.is_reverted:
            raise ValueError("Операция уже откатана.")

        is_own = original.telegram_user_id == reverted_by_telegram_id
        original_is_admin = original.role_snapshot == "admin"

        if not is_own:
            if not is_admin_user:
                raise ValueError("Можно откатить только свою операцию.")
            if original_is_admin:
                raise ValueError("Нельзя откатить операцию другого администратора.")

        reverse_amount = -original.amount

        revert_op = await self.op_repo.create(
            telegram_user_id=reverted_by_telegram_id,
            username=reverted_by_username,
            full_name=reverted_by_full_name,
            role_snapshot="admin" if is_admin_user else "employee",
            chat_id=0,
            chat_type="private",
            currency_code=original.currency_code,
            currency_title=original.currency_title,
            currency_command=original.currency_command,
            amount=reverse_amount,
            operation_type=OperationType.revert,
            revert_parent_operation_id=original.operation_id,
        )

        await self.op_repo.mark_reverted(
            original.operation_id,
            revert_op.operation_id,
            reverted_by_telegram_id=reverted_by_telegram_id,
            reverted_by_username=reverted_by_username,
            reverted_by_full_name=reverted_by_full_name,
        )

        balance = await self.balance_repo.update_amount(
            original.currency_code, reverse_amount
        )
        await self.session.commit()

        refreshed = await self.op_repo.get_by_operation_id(original.operation_id)
        return refreshed or original, revert_op, balance.amount
