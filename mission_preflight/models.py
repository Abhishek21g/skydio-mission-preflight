"""Shared types for preflight checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CheckResult:
    signal: str
    status: str  # pass | warn | fail
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2}


def overall_status(statuses: list[str]) -> str:
    worst = max(statuses, key=lambda s: STATUS_ORDER.get(s, 1))
    if worst == "fail":
        return "blocked"
    if worst == "warn":
        return "caution"
    return "cleared"
