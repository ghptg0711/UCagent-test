from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class CacheOp(str, Enum):
    READ = "read"
    WRITE = "write"


@dataclass(frozen=True)
class CacheTxn:
    op: CacheOp
    addr: int
    size: int
    data: int = 0
    mask: int | None = None
    txn_id: int = 0
    uncached: bool = False
    meta: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.addr < 0:
            raise ValueError("addr must be non-negative")
        if self.size not in (1, 2, 4, 8):
            raise ValueError(f"unsupported access size: {self.size}")
        max_mask = (1 << self.size) - 1
        mask = max_mask if self.mask is None else self.mask
        if mask < 0 or mask > max_mask:
            raise ValueError(f"mask 0x{mask:x} exceeds size {self.size}")
        object.__setattr__(self, "mask", mask)

    @property
    def aligned_addr(self) -> int:
        return self.addr - (self.addr % self.size)

    def byte_values(self) -> list[int]:
        return [(self.data >> (8 * i)) & 0xFF for i in range(self.size)]


@dataclass(frozen=True)
class CacheResponse:
    txn_id: int
    data: int = 0
    hit: bool | None = False
    evicted: bool = False
    evicted_dirty: bool = False
    writeback_addr: int | None = None
    writeback_data: bytes | None = None
    error: str | None = None
    observed_fields: frozenset[str] | None = None

    def observes(self, field_name: str) -> bool:
        """Return whether *field_name* came from a DUT-visible signal."""
        return self.observed_fields is None or field_name in self.observed_fields
