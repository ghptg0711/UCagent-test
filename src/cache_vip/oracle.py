from __future__ import annotations

from .scoreboard import ScoreboardMismatch
from .transactions import CacheOp, CacheResponse, CacheTxn


class ArchitecturalMemoryOracle:
    """Byte-level architectural oracle independent of cache replacement state."""

    def __init__(self) -> None:
        self._bytes: dict[int, int] = {}

    def check_and_apply(self, txn: CacheTxn, response: CacheResponse) -> None:
        if txn.op is CacheOp.READ:
            expected = sum(
                self._bytes.get(txn.addr + index, 0) << (8 * index) for index in range(txn.size)
            )
            if response.data != expected:
                raise ScoreboardMismatch(
                    f"architectural read mismatch at 0x{txn.addr:x}: "
                    f"expected 0x{expected:x}, got 0x{response.data:x}"
                )
            return

        for index in range(txn.size):
            if txn.mask and txn.mask & (1 << index):
                self._bytes[txn.addr + index] = (txn.data >> (8 * index)) & 0xFF
