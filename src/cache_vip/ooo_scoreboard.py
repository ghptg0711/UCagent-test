"""Out-of-order Scoreboard for transaction-level verification.

Unlike the in-order Scoreboard which expects responses in FIFO order, this
component matches expected vs actual responses by transaction ID. This models
pipelined caches where a miss (long latency) may be overtaken by a later hit
(short latency), so responses arrive out of request order.

Integration points:
    >>> from cache_vip.ooo_scoreboard import OooScoreboard
    >>> from cache_vip.reference_model import ReferenceCache
    >>> sb = OooScoreboard(reference=ReferenceCache())
    >>> sb.push_expected(txn, response)   # record expected
    >>> sb.compare_actual(response)        # match by txn_id
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .scoreboard import ScoreboardMismatch
from .transactions import CacheOp, CacheResponse, CacheTxn


@dataclass
class OooScoreboard:
    """Out-of-order scoreboard matching responses by transaction ID.

    Expected responses are stored in a dict keyed by txn_id. When an actual
    response arrives, it is matched against the expected entry with the same
    txn_id — regardless of insertion order. This enables verification of
    pipelined DUTs where responses may overtake each other.
    """

    pending: dict[int, tuple[CacheTxn, CacheResponse]] = field(default_factory=dict)
    matched: int = 0
    mismatched: int = 0
    orphan: list[CacheResponse] = field(default_factory=list)
    timed_out: list[int] = field(default_factory=list)

    def push_expected(self, txn: CacheTxn, response: CacheResponse) -> None:
        """Record an expected response indexed by txn_id."""
        if txn.txn_id in self.pending:
            raise ScoreboardMismatch(
                f"duplicate txn_id={txn.txn_id} already pending in OOO scoreboard"
            )
        self.pending[txn.txn_id] = (txn, response)

    def compare_actual(self, actual: CacheResponse) -> None:
        """Match an actual response to its expected counterpart by txn_id.

        Raises ScoreboardMismatch on any field divergence.
        """
        txn_id = actual.txn_id
        if txn_id not in self.pending:
            self.orphan.append(actual)
            self.mismatched += 1
            raise ScoreboardMismatch(
                f"unexpected or duplicate response txn_id={txn_id} "
                f"(pending: {sorted(self.pending.keys())})"
            )
        txn, expected = self.pending.pop(txn_id)
        self._check_fields(txn, expected, actual)
        self.matched += 1

    def _check_fields(self, txn: CacheTxn, expected: CacheResponse, actual: CacheResponse) -> None:
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

    def drain_pending(self) -> list[int]:
        """Return txn_ids of expected responses that never arrived."""
        remaining = list(self.pending.keys())
        self.timed_out.extend(remaining)
        self.pending.clear()
        return remaining

    @property
    def is_empty(self) -> bool:
        return len(self.pending) == 0

    def summary(self) -> dict[str, object]:
        return {
            "matched": self.matched,
            "mismatched": self.mismatched,
            "pending": len(self.pending),
            "orphan": len(self.orphan),
            "timed_out": len(self.timed_out),
        }
