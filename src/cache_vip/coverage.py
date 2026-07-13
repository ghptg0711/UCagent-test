"""Functional coverage collector for NutShell Cache verification.

The model tracks the required sign-off bins for operation type, access result,
transfer size, replacement type, write masks, address locality, and latency.
Extended cross-coverage bins provide deeper insight into corner-case interaction
between size/mask, replacement/policy, and access-type/latency dimensions.

It is intentionally independent from any specific DUT wrapper so the same
collector can be used for mock-DUT tests, directed reference-model checks, and
real DUT smoke/regression flows.
"""

from __future__ import annotations

from collections import Counter
from typing import ClassVar

from .transactions import CacheTxn


class Coverage:
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

    EXTENDED_BINS: ClassVar[frozenset[str]] = frozenset(
        {
            "cross.size_mask.size8_full",
            "cross.size_mask.size4_sparse",
            "cross.size_mask.size1_single",
            "cross.replacement_type.dirty_read_miss",
            "cross.replacement_type.clean_write_miss",
            "cross.access_latency.read_miss_long",
            "cross.access_latency.write_hit_short",
            "policy.write_allocate.write_miss_alloc",
            "policy.replacement.lru_eviction",
            "policy.replacement.fifo_eviction",
            "addr.back_to_back_same_line",
            "addr.stride_access_pattern",
        }
    )

    def __init__(self, line_bytes: int = 64) -> None:
        self.bins: Counter[str] = Counter()
        self.line_bytes = line_bytes
        self._last_line_base: int | None = None
        self._last_addr: int | None = None

    def sample_access(
        self,
        txn: CacheTxn,
        *,
        hit: bool | None,
        evicted_dirty: bool = False,
        evicted_clean: bool = False,
        latency: int = 0,
        same_set: bool = False,
        replacement_policy: str = "lru",
        write_allocate: bool = True,
    ) -> None:
        self.bins[f"op.{txn.op.value}"] += 1
        self.bins[f"size.{txn.size}"] += 1
        if hit is not None:
            self.bins[f"access.{txn.op.value}_{'hit' if hit else 'miss'}"] += 1

        full_mask = (1 << txn.size) - 1
        if txn.mask == full_mask:
            mask_type = "full"
            self.bins["mask.full"] += 1
        elif txn.mask and txn.mask & (txn.mask - 1) == 0:
            mask_type = "single"
            self.bins["mask.single"] += 1
        else:
            mask_type = "sparse"
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

        self._sample_cross_bins(
            txn,
            hit,
            evicted_dirty,
            evicted_clean,
            latency,
            mask_type,
            replacement_policy,
            write_allocate,
        )

    def _sample_cross_bins(
        self,
        txn: CacheTxn,
        hit: bool | None,
        evicted_dirty: bool,
        evicted_clean: bool,
        latency: int,
        mask_type: str,
        replacement_policy: str,
        write_allocate: bool,
    ) -> None:
        if txn.size == 8 and mask_type == "full":
            self.bins["cross.size_mask.size8_full"] += 1
        if txn.size == 4 and mask_type == "sparse":
            self.bins["cross.size_mask.size4_sparse"] += 1
        if txn.size == 1 and mask_type == "single":
            self.bins["cross.size_mask.size1_single"] += 1

        if evicted_dirty and hit is False and txn.op.value == "read":
            self.bins["cross.replacement_type.dirty_read_miss"] += 1
        if evicted_clean and hit is False and txn.op.value == "write":
            self.bins["cross.replacement_type.clean_write_miss"] += 1

        if hit is False and txn.op.value == "read" and latency >= 8:
            self.bins["cross.access_latency.read_miss_long"] += 1
        if hit is True and txn.op.value == "write" and latency < 8:
            self.bins["cross.access_latency.write_hit_short"] += 1

        if write_allocate and hit is False and txn.op.value == "write":
            self.bins["policy.write_allocate.write_miss_alloc"] += 1

        if evicted_dirty or evicted_clean:
            if replacement_policy == "lru":
                self.bins["policy.replacement.lru_eviction"] += 1
            elif replacement_policy == "fifo":
                self.bins["policy.replacement.fifo_eviction"] += 1

        line_base = txn.addr - (txn.addr % self.line_bytes)
        if self._last_line_base is not None and line_base == self._last_line_base:
            self.bins["addr.back_to_back_same_line"] += 1
        self._last_line_base = line_base

        if self._last_addr is not None and abs(txn.addr - self._last_addr) == self.line_bytes:
            self.bins["addr.stride_access_pattern"] += 1
        self._last_addr = txn.addr

    def percent(self) -> float:
        hit = sum(1 for name in self.REQUIRED_BINS if self.bins[name] > 0)
        return 100.0 * hit / len(self.REQUIRED_BINS)

    def extended_percent(self) -> float:
        if not self.EXTENDED_BINS:
            return 100.0
        hit = sum(1 for name in self.EXTENDED_BINS if self.bins[name] > 0)
        return 100.0 * hit / len(self.EXTENDED_BINS)

    def missing(self) -> list[str]:
        return sorted(name for name in self.REQUIRED_BINS if self.bins[name] == 0)

    def extended_missing(self) -> list[str]:
        return sorted(name for name in self.EXTENDED_BINS if self.bins[name] == 0)

    def summary(self) -> dict[str, object]:
        return {
            "coverage_percent": round(self.percent(), 2),
            "covered_bins": len(self.REQUIRED_BINS) - len(self.missing()),
            "total_bins": len(self.REQUIRED_BINS),
            "missing": self.missing(),
            "bins": self.required_bin_counts(),
            "extended_coverage_percent": round(self.extended_percent(), 2),
            "extended_covered": len(self.EXTENDED_BINS) - len(self.extended_missing()),
            "extended_total": len(self.EXTENDED_BINS),
            "extended_missing": self.extended_missing(),
            "extended_bins": self.extended_bin_counts(),
        }

    def required_bin_counts(self) -> dict[str, int]:
        return {name: self.bins[name] for name in sorted(self.REQUIRED_BINS)}

    def extended_bin_counts(self) -> dict[str, int]:
        return {name: self.bins[name] for name in sorted(self.EXTENDED_BINS)}
