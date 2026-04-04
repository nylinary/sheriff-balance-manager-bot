from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import CURRENCIES
from bot.models.balance import Balance
from bot.repositories import BalanceRepo
from bot.utils import format_unsigned


class BalanceService:
    def __init__(self, session: AsyncSession) -> None:
        self.balance_repo = BalanceRepo(session)

    async def get_wallet_text(self) -> str:
        balances = await self.balance_repo.get_all()
        balance_map: dict[str, Balance] = {b.currency_code: b for b in balances}

        lines = ["💰 Баланс:\n"]
        for cur in CURRENCIES:
            b = balance_map.get(cur.code)
            amount = b.amount if b else 0
            lines.append(f"{cur.emoji} {cur.title}: {format_unsigned(amount)}")

        return "\n".join(lines)
