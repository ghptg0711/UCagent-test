from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .coverage import Coverage
from .reference_model import ReferenceCache
from .scoreboard import Scoreboard
from .transactions import CacheResponse, CacheTxn


class CacheDUTAdapter(Protocol):
    async def drive_cpu_request(self, txn: CacheTxn) -> None: ...

    async def sample_cpu_response(self) -> CacheResponse: ...


@dataclass
class DUTRegressionRunner:
    """Independent expected/actual pipeline for a concrete DUT adapter."""

    adapter: CacheDUTAdapter
    scoreboard: Scoreboard = field(default_factory=Scoreboard)
    coverage: Coverage = field(init=False)
    _visited_sets: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.coverage = Coverage(line_bytes=self.scoreboard.reference.params.line_bytes)

    async def execute(self, txn: CacheTxn, *, latency: int | None = None) -> CacheResponse:
        self.scoreboard.push_request(txn, sample_coverage=False)
        start_cycle = getattr(self.adapter, "cycle_count", None)
        await self.adapter.drive_cpu_request(txn)
        actual = await self.adapter.sample_cpu_response()
        self.scoreboard.compare_response(txn, actual)

        if latency is None:
            end_cycle = getattr(self.adapter, "cycle_count", None)
            latency = (
                end_cycle - start_cycle
                if start_cycle is not None and end_cycle is not None
                else 0
            )

        params = self.scoreboard.reference.params
        set_idx = (txn.addr // params.line_bytes) % params.sets
        same_set = set_idx in self._visited_sets
        self._visited_sets.add(set_idx)
        self.coverage.sample_access(
            txn,
            hit=actual.hit if actual.observes("hit") else None,
            evicted_dirty=(actual.evicted_dirty if actual.observes("evicted_dirty") else False),
            evicted_clean=(
                actual.evicted and not actual.evicted_dirty
                if actual.observes("evicted") and actual.observes("evicted_dirty")
                else False
            ),
            latency=latency,
            same_set=same_set,
        )
        return actual
