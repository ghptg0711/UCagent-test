"""Functional coverage collector for NutShell Cache verification.

The model tracks the required sign-off bins for operation type, access result,
transfer size, replacement type, write masks, address locality, and latency.
It is intentionally independent from any specific DUT wrapper so the same
collector can be used for mock-DUT tests, directed reference-model checks, and
real DUT smoke/regression flows.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import ClassVar

from .transactions import CacheTxn


@dataclass
class Coverage:
    bins: Counter[str] = field(default_factory=Counter)
    line_bytes: int = 64

    REQUIRED_BINS: ClassVar[frozenset[str]] = frozenset(
        {
            "op.read",
            "op.write",
            "size.1",
            "size.2",
            "size.4",
            "size.8",
            "access.read_hit",
            "access.read_miss",
            "access.write_hit",
            "access.write_miss",
            "replacement.clean",
            "replacement.dirty",
            "mask.full",
            "mask.single",
            "mask.sparse",
            "addr.same_set",
            "addr.line_boundary",
            "latency.short",
            "latency.long",
        }
    )

    def sample_access(
        self,
        txn: CacheTxn,
        *,
        hit: bool | None,
        evicted_dirty: bool = False,
        evicted_clean: bool = False,
        latency: int = 0,
        same_set: bool = False,
    ) -> None:
        self.bins[f"op.{txn.op.value}"] += 1
        self.bins[f"size.{txn.size}"] += 1
        if hit is not None:
            self.bins[f"access.{txn.op.value}_{'hit' if hit else 'miss'}"] += 1

        full_mask = (1 << txn.size) - 1
        if txn.mask == full_mask:
            self.bins["mask.full"] += 1
        elif txn.mask and txn.mask & (txn.mask - 1) == 0:
            self.bins["mask.single"] += 1
        else:
            self.bins["mask.sparse"] += 1

        if evicted_dirty:
            self.bins["replacement.dirty"] += 1
        if evicted_clean:
            self.bins["replacement.clean"] += 1
        if same_set:
            self.bins["addr.same_set"] += 1
        if txn.addr % self.line_bytes >= self.line_bytes - 8:
            self.bins["addr.line_boundary"] += 1
        self.bins["latency.long" if latency >= 8 else "latency.short"] += 1

    def percent(self) -> float:
        hit = sum(1 for name in self.REQUIRED_BINS if self.bins[name] > 0)
        return 100.0 * hit / len(self.REQUIRED_BINS)

    def missing(self) -> list[str]:
        return sorted(name for name in self.REQUIRED_BINS if self.bins[name] == 0)

    def summary(self) -> dict[str, object]:
        return {
            "coverage_percent": round(self.percent(), 2),
            "covered_bins": len(self.REQUIRED_BINS) - len(self.missing()),
            "total_bins": len(self.REQUIRED_BINS),
            "missing": self.missing(),
            "bins": self.required_bin_counts(),
        }

    def required_bin_counts(self) -> dict[str, int]:
        return {name: self.bins[name] for name in sorted(self.REQUIRED_BINS)}
