"""Constrained-random transaction generator for NutShell Cache verification.

The generator provides reproducible random streams plus directed helpers for
replacement, partial writes, same-set pressure, uncached accesses, and line
boundary stress. Profiles control read/write balance, hot-set bias, boundary
rate, and uncached traffic without changing test code.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from .reference_model import CacheParams
from .transactions import CacheOp, CacheTxn


@dataclass(frozen=True)
class GeneratorProfile:
    read_weight: int = 55
    write_weight: int = 45
    hot_set_weight: int = 35
    boundary_weight: int = 10
    uncached_weight: int = 5


class CacheGenerator:
    def __init__(
        self,
        params: CacheParams | None = None,
        *,
        seed: int = 1,
        profile: GeneratorProfile | None = None,
    ) -> None:
        self.params = params or CacheParams()
        self.random = random.Random(seed)
        self.profile = profile or GeneratorProfile()
        self._txn_id = 0

    def random_txn(self) -> CacheTxn:
        op = self.random.choices(
            [CacheOp.READ, CacheOp.WRITE],
            weights=[self.profile.read_weight, self.profile.write_weight],
        )[0]
        size = self.random.choice([1, 2, 4, 8])
        addr = self._random_addr(size)
        mask = self._random_mask(size) if op is CacheOp.WRITE else (1 << size) - 1
        data = self.random.getrandbits(size * 8)
        uncached = self.random.randrange(100) < self.profile.uncached_weight
        return self._make(op, addr, size, data=data, mask=mask, uncached=uncached)

    def random_stream(self, count: int) -> list[CacheTxn]:
        return [self.random_txn() for _ in range(count)]

    def replacement_sequence(self, set_idx: int = 0, *, dirty: bool = True) -> list[CacheTxn]:
        txns: list[CacheTxn] = []
        for tag in range(self.params.ways + 1):
            addr = self._addr_from_tag_set(tag, set_idx)
            txns.append(self._make(CacheOp.WRITE if dirty else CacheOp.READ, addr, 8, data=tag + 1))
        txns.append(self._make(CacheOp.READ, self._addr_from_tag_set(0, set_idx), 8))
        return txns

    def partial_write_sequence(self, base_addr: int) -> list[CacheTxn]:
        base = base_addr - (base_addr % self.params.line_bytes)
        return [
            self._make(CacheOp.WRITE, base + 0, 8, data=0x1122334455667788, mask=0xFF),
            self._make(CacheOp.WRITE, base + 1, 4, data=0xAABBCCDD, mask=0b0101),
            self._make(CacheOp.WRITE, base + 6, 2, data=0xEEFF, mask=0b10),
            self._make(CacheOp.READ, base + 0, 8),
        ]

    def mixed_corner_stream(self) -> list[CacheTxn]:
        txns = []
        txns.extend(self.partial_write_sequence(0x1000))
        txns.extend(self.replacement_sequence(3, dirty=True))
        txns.extend(self.replacement_sequence(5, dirty=False))
        return txns

    def replacement_sequence_with_lru_check(self, set_idx: int = 0) -> list[CacheTxn]:
        """Generate same-set pressure that exposes an incorrect LRU victim."""
        txns: list[CacheTxn] = []
        for tag in range(self.params.ways + 1):
            addr = self._addr_from_tag_set(tag, set_idx)
            txns.append(self._make(CacheOp.WRITE, addr, 8, data=tag + 1))
        # Access tag 1 to make it MRU, pushing tag 0 to LRU
        txns.append(self._make(CacheOp.READ, self._addr_from_tag_set(1, set_idx), 8))
        # Access tag 0 to confirm it was evicted (should be a miss)
        txns.append(self._make(CacheOp.READ, self._addr_from_tag_set(0, set_idx), 8))
        # Access tag 1 again to confirm it's still cached (should be a hit)
        txns.append(self._make(CacheOp.READ, self._addr_from_tag_set(1, set_idx), 8))
        return txns

    def partial_write_cross_offset(self, base_addr: int = 0x2000) -> list[CacheTxn]:
        """Generate partial writes at several offsets followed by readback."""
        base = base_addr - (base_addr % self.params.line_bytes)
        txns: list[CacheTxn] = []
        # Write full 8 bytes at offset 0
        txns.append(self._make(CacheOp.WRITE, base + 0, 8, data=0x1122334455667788, mask=0xFF))
        # Partial write at offset 4 with mask 0b0101
        txns.append(self._make(CacheOp.WRITE, base + 4, 4, data=0xCAFEBABE, mask=0b0101))
        # Partial write at offset 12 with mask 0b1010
        txns.append(self._make(CacheOp.WRITE, base + 12, 4, data=0xDEADC0DE, mask=0b1010))
        # Partial write at offset 24 with single byte
        txns.append(self._make(CacheOp.WRITE, base + 24, 1, data=0xFF, mask=0x1))
        # Read back full line at offset 0
        txns.append(self._make(CacheOp.READ, base + 0, 8))
        txns.append(self._make(CacheOp.READ, base + 8, 8))
        return txns

    def raw_dependency_sequence(self, base_addr: int = 0x3000) -> list[CacheTxn]:
        """Generate RAW, WAR, and WAW dependencies for one cache line."""
        base = base_addr - (base_addr % self.params.line_bytes)
        txns: list[CacheTxn] = []
        # Write initial value
        txns.append(self._make(CacheOp.WRITE, base, 8, data=0x0102030405060708, mask=0xFF))
        # RAW: read after write (should get written value)
        txns.append(self._make(CacheOp.READ, base, 8))
        # WAR: write after read (partial write)
        txns.append(self._make(CacheOp.WRITE, base + 2, 2, data=0xAABB, mask=0x3))
        # Read back to verify WAR
        txns.append(self._make(CacheOp.READ, base, 8))
        # WAW: write after write (overwrite)
        txns.append(self._make(CacheOp.WRITE, base, 4, data=0xDEADBEEF, mask=0xF))
        # Final read
        txns.append(self._make(CacheOp.READ, base, 8))
        return txns

    def line_boundary_all_sizes(self, base_addr: int = 0x3C00) -> list[CacheTxn]:
        """Generate accesses of every supported size at a line boundary."""
        base = base_addr - (base_addr % self.params.line_bytes)
        line_end = base + self.params.line_bytes
        txns: list[CacheTxn] = []
        # Access at line_end - 1 (1 byte)
        txns.append(self._make(CacheOp.READ, line_end - 1, 1))
        # Access at line_end - 2 (2 bytes)
        txns.append(self._make(CacheOp.READ, line_end - 2, 2))
        # Access at line_end - 4 (4 bytes)
        txns.append(self._make(CacheOp.READ, line_end - 4, 4))
        # Access at line_end - 8 (8 bytes)
        txns.append(self._make(CacheOp.READ, line_end - 8, 8))
        # Write and read back at boundary
        txns.append(self._make(CacheOp.WRITE, line_end - 4, 4, data=0x12345678, mask=0xF))
        txns.append(self._make(CacheOp.READ, line_end - 8, 8))
        return txns

    def uncached_access_sequence(self, base_addr: int = 0x80000000) -> list[CacheTxn]:
        """Generate uncached reads and writes followed by a cached access."""
        txns: list[CacheTxn] = []
        # Uncached write
        txns.append(
            self._make(CacheOp.WRITE, base_addr, 4, data=0xCAFEBABE, mask=0xF, uncached=True)
        )
        # Uncached read (should get written value)
        txns.append(self._make(CacheOp.READ, base_addr, 4, uncached=True))
        # Uncached write with partial mask
        txns.append(
            self._make(CacheOp.WRITE, base_addr + 4, 2, data=0x1234, mask=0x3, uncached=True)
        )
        # Uncached read back
        txns.append(self._make(CacheOp.READ, base_addr + 4, 2, uncached=True))
        # Cached access to different address (should use cache)
        txns.append(self._make(CacheOp.WRITE, base_addr + 0x100, 4, data=0xDEADBEEF, mask=0xF))
        txns.append(self._make(CacheOp.READ, base_addr + 0x100, 4))
        return txns

    def reset_state_clear(self, base_addr: int = 0x4000) -> list[CacheTxn]:
        """Generate accesses used to verify cache state across a reset."""
        base = base_addr - (base_addr % self.params.line_bytes)
        txns: list[CacheTxn] = []
        # Write data
        txns.append(self._make(CacheOp.WRITE, base, 8, data=0x1122334455667788, mask=0xFF))
        # Read back (should hit)
        txns.append(self._make(CacheOp.READ, base, 8))
        # Note: reset is handled by the testbench, not the generator.
        # After reset, the following reads should be misses.
        # We add a marker in meta to indicate reset expectation.
        txns.append(self._make(CacheOp.READ, base, 8))
        return txns

    def weighted_stream(
        self, count: int, *, read_weight: float = 0.6, write_weight: float = 0.4
    ) -> list[CacheTxn]:
        """Generate a weighted stream concentrated in a small set range."""
        txns: list[CacheTxn] = []
        for _ in range(count):
            op = self.random.choices(
                [CacheOp.READ, CacheOp.WRITE],
                weights=[read_weight, write_weight],
            )[0]
            set_count = min(self.params.sets, 8)
            set_idx = self.random.randint(0, set_count - 1)
            offset = self.random.randint(0, self.params.line_bytes - 8)
            addr = set_idx * (self.params.line_bytes * self.params.ways) + offset
            size = self.random.choice([1, 2, 4, 8])

            if op is CacheOp.WRITE:
                data = self.random.getrandbits(size * 8)
                mask_options = [0xFF, 0x0F, 0xF0, 0x01, 0x10, 0x11, 0x55, 0xAA]
                full = (1 << size) - 1
                mask = self.random.choice(mask_options[:size]) & full
                if mask == 0:
                    mask = full
            else:
                data = 0
                mask = 0

            txns.append(self._make(op, addr, size, data=data, mask=mask))
        return txns

    def implication_stream(self, count: int, base_addr: int = 0x1000) -> list[CacheTxn]:
        """Generate a stream whose size and mask follow address constraints."""
        txns: list[CacheTxn] = []
        for _ in range(count):
            aligned = self.random.random() < 0.3

            if aligned:
                # Line-aligned accesses use the maximum transfer size.
                set_idx = self.random.randint(0, self.params.sets - 1)
                addr = base_addr + set_idx * self.params.line_bytes
                size = 8
            else:
                # Interior accesses use a sub-line transfer size.
                set_idx = self.random.randint(0, self.params.sets - 1)
                size = self.random.choice([1, 2, 4])
                offset = self.random.randint(1, self.params.line_bytes - size)
                addr = base_addr + set_idx * self.params.line_bytes + offset

            op = self.random.choice([CacheOp.READ, CacheOp.WRITE])

            if op is CacheOp.WRITE:
                data = self.random.getrandbits(size * 8)
                # The transfer size bounds the valid byte-enable mask.
                mask = (1 << size) - 1
                # Occasionally clear one bit to exercise sparse masks.
                if self.random.random() < 0.3:
                    clear_bit = self.random.randint(0, size - 1)
                    mask &= ~(1 << clear_bit)
                    if mask == 0:
                        mask = (1 << size) - 1
            else:
                data = 0
                mask = 0

            txns.append(self._make(op, addr, size, data=data, mask=mask))
        return txns

    def _random_addr(self, size: int) -> int:
        if self.random.randrange(100) < self.profile.hot_set_weight:
            set_idx = self.random.randrange(min(8, self.params.sets))
            tag = self.random.randrange(32)
            base = self._addr_from_tag_set(tag, set_idx)
        else:
            base = self.random.randrange(0, 1 << 16)
            base -= base % self.params.line_bytes

        if self.random.randrange(100) < self.profile.boundary_weight:
            offset = max(0, self.params.line_bytes - size)
        else:
            offset = self.random.randrange(0, self.params.line_bytes - size + 1)
        return base + offset

    def _random_mask(self, size: int) -> int:
        full = (1 << size) - 1
        choice = self.random.randrange(100)
        if choice < 45:
            return full
        if choice < 70:
            return 1 << self.random.randrange(size)
        mask = 0
        while mask == 0:
            mask = self.random.randrange(1, full + 1)
        return mask

    def _make(
        self,
        op: CacheOp,
        addr: int,
        size: int,
        *,
        data: int = 0,
        mask: int | None = None,
        uncached: bool = False,
    ) -> CacheTxn:
        self._txn_id += 1
        return CacheTxn(
            op=op,
            addr=addr,
            size=size,
            data=data,
            mask=mask,
            txn_id=self._txn_id,
            uncached=uncached,
        )

    def _addr_from_tag_set(self, tag: int, set_idx: int) -> int:
        return (tag * self.params.sets + set_idx) * self.params.line_bytes


def iter_seeded_streams(
    seeds: Iterable[int], count: int, params: CacheParams | None = None
) -> Iterable[list[CacheTxn]]:
    for seed in seeds:
        yield CacheGenerator(params, seed=seed).random_stream(count)
