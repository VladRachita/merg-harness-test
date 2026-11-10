"""
Safety rails. This harness sends real attacks, mutates accounts and (in the
resilience suite) generates load, so it must be hard to aim at the wrong thing.

  scope guard   The harness only talks to hosts that are plainly internal:
                loopback, private/link-local addresses, single-label names
                (docker service / container names), reserved test TLDs. Any
                other host — anything that could be a real, public system —
                must be listed in `safety.allowed_hosts` (or
                $SENTINEL_ALLOWED_HOSTS) by someone who is authorised to test it.

  pacing        `safety.max_rps` spaces requests out; `safety.max_requests` is a
                hard budget for one run. Both default to off for local/docker
                targets and are there for shared staging environments.
"""
from __future__ import annotations

import ipaddress
import socket
import threading
import time

from .adapters.base import Inconclusive

# TLDs that can never be a real public host (RFC 2606 / RFC 6761 / RFC 8375 and
# the conventional private-network suffixes used by docker, k8s and mDNS).
_INTERNAL_SUFFIXES = (".localhost", ".local", ".test", ".example", ".invalid", ".internal",
                      ".lan", ".home.arpa", ".docker", ".svc", ".cluster.local")


class ScopeError(Exception):
    """The configured target is outside the allowed scope."""


class BudgetExceeded(Inconclusive):
    """The run's request budget (`safety.max_requests`) is spent."""


def _ip_internal(ip) -> bool:
    return bool(ip.is_loopback or ip.is_private or ip.is_link_local)


def classify_host(host: str, resolve: bool = True):
    """Return ('internal'|'public', reason) for a hostname or IP literal."""
    h = (host or "").strip().strip("[]").lower().rstrip(".")
    if not h:
        return "public", "empty host"
    try:
        ip = ipaddress.ip_address(h)
        return ("internal", "private/loopback address") if _ip_internal(ip) \
            else ("public", "public IP address")
    except ValueError:
        pass
    if h == "localhost" or "." not in h:
        return "internal", "single-label name (docker service / container)"
    if h.endswith(_INTERNAL_SUFFIXES):
        return "internal", "reserved internal/test domain"
    if resolve:
        try:
            infos = socket.getaddrinfo(h, None)
            ips = {ipaddress.ip_address(i[4][0].split("%")[0]) for i in infos}
            if ips and all(_ip_internal(ip) for ip in ips):
                return "internal", "resolves only to private addresses"
        except (OSError, ValueError):
            pass
    return "public", "public or unresolvable hostname"


def _allowed(host: str, allow) -> bool:
    h = host.lower().rstrip(".")
    for pat in allow or []:
        p = str(pat).lower().strip().rstrip(".")
        if p == h or (p.startswith("*.") and h.endswith(p[1:])):
            return True
    return False


def check_scope(cfg, resolve: bool = True) -> list:
    """Raise ScopeError unless every host the config can reach is in scope.
    Returns notes about explicitly allow-listed public hosts."""
    notes, blocked = [], []
    allow = cfg.safety.get("allowed_hosts") or []
    for host in sorted(cfg.hosts()):
        kind, why = classify_host(host, resolve)
        if kind == "internal":
            continue
        if _allowed(host, allow):
            notes.append(f"'{host}' is a public host, allowed by safety.allowed_hosts")
        else:
            blocked.append(f"{host} ({why})")
    if blocked:
        raise ScopeError(
            "refusing to run: target outside the allowed scope — " + ", ".join(blocked) + ".\n"
            "This harness sends real attacks and changes data. It runs freely against "
            "internal targets (localhost, private IPs, docker service names). To test another "
            "host you are authorised to test, add it to `safety.allowed_hosts` in the config "
            "(or $SENTINEL_ALLOWED_HOSTS). Never aim it at production or at a system you "
            "don't own.")
    return notes


class Pacer:
    """Thread-safe request pacing and budget."""

    def __init__(self, max_rps=0, max_requests=0):
        self.interval = 1.0 / float(max_rps) if max_rps else 0.0
        self.max_requests = int(max_requests or 0)
        self.count = 0
        self._next = 0.0
        self._lock = threading.Lock()

    def tick(self):
        with self._lock:
            self.count += 1
            if self.max_requests and self.count > self.max_requests:
                raise BudgetExceeded(f"request budget spent (safety.max_requests={self.max_requests})")
            wait = 0.0
            if self.interval:
                now = time.monotonic()
                wait = max(0.0, self._next - now)
                self._next = max(now, self._next) + self.interval
        if wait:
            time.sleep(wait)
