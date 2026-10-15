"""Suite primitives: an Attack, a Finding, and a capability-aware runner."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..adapters.base import Target, Capability


class Status(str, Enum):
    BLOCKED = "BLOCKED"    # the attack was correctly denied (good)
    LEAK = "LEAK"          # the attack got through (bad)
    SKIPPED = "SKIPPED"    # a required capability is not configured
    ERROR = "ERROR"        # the check itself crashed


@dataclass
class Attack:
    id: str
    category: str
    desc: str
    check: object                     # (target) -> bool ; True == safe/blocked
    requires: set = field(default_factory=set)


@dataclass
class Finding:
    id: str
    category: str
    desc: str
    status: Status
    detail: str = ""


def run_catalogue(factory, attacks: list[Attack]) -> list[Finding]:
    """`factory` returns a Target. A FRESH target is used per attack so stateful
    effects (lockout counters, revoked tokens, disabled users) don't bleed between
    attacks. For a live HTTP backend the factory reuses one client; isolate state
    there by pointing at a disposable test instance and using distinct accounts."""
    caps = set(factory().capabilities())
    out = []
    for atk in attacks:
        missing = set(atk.requires) - caps
        if missing:
            names = ", ".join(sorted(m.value for m in missing))
            out.append(Finding(atk.id, atk.category, atk.desc, Status.SKIPPED,
                               f"needs capability: {names}"))
            continue
        try:
            t = factory()
            t.reset()
            safe = bool(atk.check(t))
            out.append(Finding(atk.id, atk.category, atk.desc,
                               Status.BLOCKED if safe else Status.LEAK))
        except Exception as e:
            out.append(Finding(atk.id, atk.category, atk.desc, Status.ERROR, repr(e)))
    return out
