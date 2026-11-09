"""Suite registry. Each builder takes a Config and returns a list[Attack]."""
from . import access_control, media_injection, oct2026, nov2026, automation, resilience

BUILDERS = {
    "access_control": access_control.build,     # auth, sessions, authz, OAuth, takeover
    "media_injection": media_injection.build,   # hostile uploads
    "oct2026": oct2026.build,                   # techniques exploited in October 2026
    "nov2026": nov2026.build,                   # disclosures mid-Oct → early Nov 2026
    "automation": automation.build,             # bots / scripted agents / spam (OWASP OAT)
    "resilience": resilience.build,             # pathological input + bounded load
}

SUITE_INFO = {
    "access_control": "Auth, sessions, authorization, OAuth, account takeover",
    "media_injection": "Hostile and malformed uploads",
    "oct2026": "Techniques exploited in October 2026",
    "nov2026": "Flaws disclosed mid-October to early November 2026",
    "automation": "Bots, scripted agents and spam (rate-limit evasion, sign-up bursts)",
    "resilience": "Pathological input and a bounded load burst",
}
