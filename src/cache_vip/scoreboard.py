from __future__ import annotations

from dataclasses import dataclass, field

from .coverage import Coverage
from .reference_model import ReferenceCache
from .transactions import CacheOp, CacheResponse, CacheTxn


class ScoreboardMismatch(AssertionError):
    pass


@dataclass
class Scoreboard:
    reference: ReferenceCache = field(default_factory=ReferenceCache)
    coverage: Coverage = field(init=False)
    expected: list[CacheResponse] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.coverage = Coverage(line_bytes=self.reference.params.line_bytes)

    def push_request(
        self,
        txn: CacheTxn,
        *,
        latency: int = 0,
        same_set: bool = False,
        sample_coverage: bool = True,
    ) -> CacheResponse:
        response = self.reference.access(txn)
        self.expected.append(response)
        if sample_coverage:
            self.coverage.sample_access(
                txn,
                hit=response.hit,
                evicted_dirty=response.evicted_dirty,
                evicted_clean=(response.evicted and not response.evicted_dirty),
                latency=latency,
                same_set=same_set,
                replacement_policy=self.reference.params.replacement.value,
                write_allocate=self.reference.params.write_allocate,
            )
        return response

    def compare_response(self, txn: CacheTxn, actual: CacheResponse) -> None:
        if not self.expected:
            raise ScoreboardMismatch(f"unexpected response txn_id={actual.txn_id}")
        expected = self.expected.pop(0)
        if expected.txn_id != actual.txn_id:
            raise ScoreboardMismatch(
                f"txn order mismatch: expected {expected.txn_id}, got {actual.txn_id}"
            )
        if actual.observes("hit") and expected.hit != actual.hit:
            raise ScoreboardMismatch(
                f"hit/miss mismatch txn_id={txn.txn_id} addr=0x{txn.addr:x}: "
                f"expected hit={expected.hit}, got hit={actual.hit}"
            )
        if txn.op is CacheOp.READ and expected.data != actual.data:
            raise ScoreboardMismatch(
                f"read data mismatch txn_id={txn.txn_id} addr=0x{txn.addr:x}: "
                f"expected 0x{expected.data:x}, got 0x{actual.data:x}"
            )
        if actual.observes("evicted_dirty") and expected.evicted_dirty != actual.evicted_dirty:
            raise ScoreboardMismatch(
                f"dirty eviction mismatch txn_id={txn.txn_id}: "
                f"expected {expected.evicted_dirty}, got {actual.evicted_dirty}"
            )
        if actual.observes("writeback_addr") and expected.writeback_addr != actual.writeback_addr:
            raise ScoreboardMismatch(
                f"writeback addr mismatch txn_id={txn.txn_id}: "
                f"expected {expected.writeback_addr}, got {actual.writeback_addr}"
            )
        if actual.observes("writeback_data") and expected.writeback_data != actual.writeback_data:
            raise ScoreboardMismatch(f"writeback data mismatch txn_id={txn.txn_id}")
        if actual.observes("error") and expected.error != actual.error:
            raise ScoreboardMismatch(
                f"error mismatch txn_id={txn.txn_id}: expected {expected.error}, got {actual.error}"
            )

    def observe_transaction(
        self, txn: CacheTxn, actual: CacheResponse | None = None, *, latency: int = 0
    ) -> None:
        self.push_request(txn, latency=latency)
        if actual is None:
            raise ScoreboardMismatch(
                f"observe_transaction requires actual response for txn_id={txn.txn_id}; "
                f"got None (self-comparison is not valid)"
            )
        self.compare_response(txn, actual)
