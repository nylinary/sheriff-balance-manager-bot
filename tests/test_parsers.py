"""Tests for parse_amount_and_comment — the value+comment parser for currency commands."""

from __future__ import annotations

import pytest

from bot.utils.parsers import _MAX_COMMENT_LEN, parse_amount_and_comment


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # plain amount, no comment
        ("3200", (3200, None)),
        ("1000000", (1000000, None)),
        # amount + comment
        ("3200 оплата за такси", (3200, "оплата за такси")),
        ("15 some comment 123", (15, "some comment 123")),
        # space-grouped thousands
        ("1 000", (1000, None)),
        ("1 000 такси", (1000, "такси")),
        ("1 000 000 крупная сумма", (1000000, "крупная сумма")),
        # sign
        ("+500", (500, None)),
        ("-500 возврат", (-500, "возврат")),
        # comment starting with a non-3-digit number stays in the comment
        ("100 50 тест", (100, "50 тест")),
        # documented ambiguity: a 3-digit group is folded into the amount
        ("500 200 за такси", (500200, "за такси")),
        # surrounding / collapsed whitespace
        ("  3200   такси  ", (3200, "такси")),
        # multi-line comment (Telegram allows newlines)
        ("3200 строка1\nстрока2", (3200, "строка1\nстрока2")),
    ],
)
def test_valid_inputs(text: str, expected: tuple[int, str | None]) -> None:
    assert parse_amount_and_comment(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        None,
        "",
        "   ",
        "0",
        "0 коммент",
        "-0",
        "abc",
        "такси",
        "3200такси",  # no space between number and text -> invalid amount
        "12abc",
    ],
)
def test_invalid_inputs(text: str | None) -> None:
    assert parse_amount_and_comment(text) is None


def test_comment_is_trimmed() -> None:
    assert parse_amount_and_comment("100    с пробелами   ") == (100, "с пробелами")


def test_blank_comment_becomes_none() -> None:
    assert parse_amount_and_comment("100    ") == (100, None)


def test_comment_length_capped() -> None:
    long_comment = "a" * (_MAX_COMMENT_LEN + 50)
    amount, comment = parse_amount_and_comment(f"100 {long_comment}")
    assert amount == 100
    assert comment is not None
    assert len(comment) == _MAX_COMMENT_LEN
