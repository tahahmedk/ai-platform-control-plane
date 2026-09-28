"""Atomic process-local admission. Failed attempts retain reservations."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from typing import Callable


class BudgetExceeded(RuntimeError):
    pass


class RateLimited(RuntimeError):
    pass


class TokenBudgetLedger:
    def __init__(
        self, limits: dict[str, int], rates: dict[str, int], clock: Callable[[], float] = monotonic
    ):
        self.limits = dict(limits)
        self.rates = dict(rates)
        self.usage: dict[str, int] = defaultdict(int)
        self.arrivals: dict[str, deque[float]] = defaultdict(deque)
        self.clock = clock
        self.lock = Lock()

    def reserve(self, tenant: str, tokens: int) -> None:
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        with self.lock:
            now = self.clock()
            arrivals = self.arrivals[tenant]
            while arrivals and arrivals[0] <= now - 60:
                arrivals.popleft()
            if len(arrivals) >= self.rates[tenant]:
                raise RateLimited("tenant request rate exceeded")
            if self.usage[tenant] + tokens > self.limits[tenant]:
                raise BudgetExceeded("tenant token budget exceeded")
            self.usage[tenant] += tokens
            arrivals.append(now)

    def remaining(self, tenant: str) -> int:
        with self.lock:
            return self.limits[tenant] - self.usage[tenant]
