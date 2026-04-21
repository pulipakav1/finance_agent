"""Structured logging and in-memory metrics."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Iterator

from src.fin_platform.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


logger = logging.getLogger("fin_platform")


@dataclass
class MetricsStore:
    counters: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    timings_ms: Dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def incr(self, key: str) -> None:
        self.counters[key] += 1

    def observe_ms(self, key: str, value: float) -> None:
        self.timings_ms[key].append(value)


metrics = MetricsStore()


@contextmanager
def timed(metric_key: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = (time.perf_counter() - start) * 1000
        metrics.observe_ms(metric_key, elapsed)
