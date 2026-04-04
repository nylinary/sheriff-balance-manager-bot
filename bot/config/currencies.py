from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Currency:
    code: str
    title: str
    command: str
    emoji: str


CURRENCIES: list[Currency] = [
    Currency(code="rub", title="Руб", command="руб", emoji="🇷🇺"),
    Currency(code="usd_blue", title="Доллар синий", command="доллс", emoji="💵"),
    Currency(code="usd_white", title="Доллар белый", command="доллб", emoji="💴"),
    Currency(code="eur", title="Евро", command="евро", emoji="🇪🇺"),
    Currency(code="eur500", title="Евро500", command="евро500", emoji="💶"),
]

# Fast lookups
CURRENCY_BY_COMMAND: dict[str, Currency] = {c.command: c for c in CURRENCIES}
CURRENCY_BY_CODE: dict[str, Currency] = {c.code: c for c in CURRENCIES}
