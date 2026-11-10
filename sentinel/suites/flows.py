"""
Flows — the checks grouped by the part of the product they attack, in the words
a product team uses ("test the login", "test sign-up", "test uploads"), instead
of by suite. Every check belongs to exactly one flow; the web UI and
`--flow` select by it.
"""
from __future__ import annotations

# (key, label, what it covers) — display order
FLOWS = [
    ("login", "Login", "Brute force, lockout, bots dodging the limit, SQL injection, MFA"),
    ("registration", "Registration", "Privilege fields at sign-up, weak passwords, sign-up bursts"),
    ("upload", "Uploads & media", "Malicious, disguised and oversized files, SSRF via import-by-URL"),
    ("session", "Sessions & tokens", "Forged tokens, logout and revocation, CSRF, account changes"),
    ("reset", "Password reset", "Token reuse and guessing, injection, enumeration"),
    ("access", "Data access & admin", "Reading other users' data, admin endpoints, spoofed identity"),
    ("oauth", "OAuth sign-in", "PKCE, redirect URI, code replay and theft"),
    ("frontend", "Front end & exposure", "Exposed files, CORS, front-end headers, secrets in JavaScript"),
    ("platform", "Load & hardening", "Hostile request shapes, a load burst, headers, error leaks"),
]
FLOW_LABEL = {k: label for k, label, _ in FLOWS}

_GROUPS = {
    "login": "BF1 BF2 BF3 BF4 BF5 BF6 INJ1 SES1 SES5 CT3 NOV5 NOV7 NOV9 BOT1 BOT2 BOT3 BOT4",
    "registration": "AZ5 AZ7 OCT9 REG1 BOT5",
    "upload": "INJ5 INJ6 OUT5 UP1 UP2 UP3 MED1 MED2 MED3 MED4 OCT5 OCT6",
    "session": "C1 C2 C3 C5 C6 SES2 SES3 SES4 SES6 SES7 NOV1 NOV2 NOV3 NOV4 NOV8 CT1 AT4 OCT2",
    "reset": "AT1 AT3 ID2 ID3 OCT3a OCT3b NOV6 BOT6",
    "access": "AZ1 AZ2 AZ3 AZ4 AZ6 OCT4 OCT7 OCT8 NOV10",
    "oauth": "OA1 OA2 OA3 OA4 OA5 OCT1 NOV11 NOV12",
    "frontend": "SUR1 SUR2 FE1 FE2 FE3 FE4 FE5",
    "platform": "OUT1 OUT3 ID1 RES1 RES2 RES3 RES4 RES5 RES6 RES7 RES8 RES9",
}
FLOW_OF = {cid: flow for flow, ids in _GROUPS.items() for cid in ids.split()}


def flow_of(check_id: str) -> str:
    """The flow a check belongs to ('' for an id nobody classified — a test
    fails if that ever happens)."""
    return FLOW_OF.get(check_id, "")
