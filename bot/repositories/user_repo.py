from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.user import User, UserRole


class UserRepo:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        full_name: str | None = None,
    ) -> User:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        role = (
            UserRole.admin if telegram_id in settings.admin_ids else UserRole.employee
        )

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                role=role,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            user.username = username
            user.full_name = full_name
            user.role = role
            await self.session.flush()

        return user
