from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.balance import Balance


class BalanceRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, currency_code: str) -> Balance:
        stmt = select(Balance).where(Balance.currency_code == currency_code)
        result = await self.session.execute(stmt)
        balance = result.scalar_one_or_none()
        if balance is None:
            balance = Balance(currency_code=currency_code, amount=0)
            self.session.add(balance)
            await self.session.flush()
        return balance

    async def update_amount(self, currency_code: str, delta: int) -> Balance:
        balance = await self.get(currency_code)
        balance.amount += delta
        await self.session.flush()
        return balance

    async def get_all(self) -> list[Balance]:
        from bot.config import CURRENCIES

        balances: list[Balance] = []
        for cur in CURRENCIES:
            balances.append(await self.get(cur.code))
        return balances
