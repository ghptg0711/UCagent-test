from __future__ import annotations

import random as _random
from dataclasses import dataclass, field
from enum import Enum

from .transactions import CacheOp, CacheResponse, CacheTxn


class ReplacementPolicy(str, Enum):
    LRU = "lru"
    FIFO = "fifo"
    RANDOM = "random"


@dataclass(frozen=True)
class CacheParams:
    sets: int = 64
    ways: int = 4
    line_bytes: int = 64
    replacement: ReplacementPolicy = ReplacementPolicy.LRU
    write_allocate: bool = True

    def __post_init__(self) -> None:
        if self.sets <= 0 or self.ways <= 0 or self.line_bytes <= 0:
            raise ValueError("cache params must be positive")
        if self.line_bytes & (self.line_bytes - 1):
            raise ValueError("line_bytes must be a power of two")


@dataclass
class CacheLine:
    valid: bool = False
    dirty: bool = False
    tag: int = 0
    data: bytearray = field(default_factory=bytearray)


class ByteMemory:
    def __init__(self) -> None:
        self._data: dict[int, int] = {}

    def read_byte(self, addr: int) -> int:
        return self._data.get(addr, 0)

    def write_byte(self, addr: int, value: int) -> None:
        self._data[addr] = value & 0xFF

    def read(self, addr: int, size: int) -> int:
        return sum(self.read_byte(addr + i) << (8 * i) for i in range(size))

    def write(self, addr: int, size: int, data: int, mask: int) -> None:
        for i in range(size):
            if mask & (1 << i):
                self.write_byte(addr + i, data >> (8 * i))

    def read_line(self, base: int, line_bytes: int) -> bytearray:
        return bytearray(self.read_byte(base + i) for i in range(line_bytes))

    def write_line(self, base: int, data: bytes | bytearray) -> None:
        for i, value in enumerate(data):
            self.write_byte(base + i, value)


class ReferenceCache:
    def __init__(self, params: CacheParams | None = None, memory: ByteMemory | None = None) -> None:
        self.params = params or CacheParams()
        self.memory = memory or ByteMemory()
        self.lines: list[list[CacheLine]] = [
            [CacheLine(data=bytearray(self.params.line_bytes)) for _ in range(self.params.ways)]
            for _ in range(self.params.sets)
        ]
        self.lru: list[list[int]] = [list(range(self.params.ways)) for _ in range(self.params.sets)]
        self.fifo: list[list[int]] = [
            list(range(self.params.ways)) for _ in range(self.params.sets)
        ]
        self._rng = _random.Random(42)
        self.last_writeback: tuple[int, bytes] | None = None

    def reset(self) -> None:
        """Clear cache line state but preserve backing memory."""
        for set_lines in self.lines:
            for line in set_lines:
                line.valid = False
                line.dirty = False
                line.tag = 0
        self.lru = [list(range(self.params.ways)) for _ in range(self.params.sets)]
        self.fifo = [list(range(self.params.ways)) for _ in range(self.params.sets)]
        self.last_writeback = None

    def access(self, txn: CacheTxn) -> CacheResponse:
        line_base = self._line_base(txn.addr)
        set_idx = self._set_idx(txn.addr)
        tag = self._tag(txn.addr)
        way = self._find_way(set_idx, tag)
        hit = way is not None
        evicted = False
        evicted_dirty = False
        writeback_addr: int | None = None
        writeback_data: bytes | None = None

        if txn.uncached:
            return self._uncached_access(txn)

        if way is None:
            if txn.op is CacheOp.WRITE and not self.params.write_allocate:
                self.memory.write(txn.addr, txn.size, txn.data, txn.mask or ((1 << txn.size) - 1))
                return CacheResponse(txn_id=txn.txn_id, data=0, hit=False)
            way, evicted, evicted_dirty, writeback_addr, writeback_data = self._allocate_line(
                set_idx, tag, line_base
            )

        line = self.lines[set_idx][way]
        offset = txn.addr - line_base
        if offset + txn.size > self.params.line_bytes:
            raise ValueError("cross-line access is not supported by this reference model")

        if txn.op is CacheOp.READ:
            data = sum(line.data[offset + i] << (8 * i) for i in range(txn.size))
        else:
            data = 0
            for i, value in enumerate(txn.byte_values()):
                if txn.mask and txn.mask & (1 << i):
                    line.data[offset + i] = value
            line.dirty = True

        self._touch(set_idx, way)
        return CacheResponse(
            txn_id=txn.txn_id,
            data=data,
            hit=hit,
            evicted=evicted,
            evicted_dirty=evicted_dirty,
            writeback_addr=writeback_addr,
            writeback_data=writeback_data,
        )

    def _uncached_access(self, txn: CacheTxn) -> CacheResponse:
        if txn.op is CacheOp.READ:
            data = self.memory.read(txn.addr, txn.size)
        else:
            self.memory.write(txn.addr, txn.size, txn.data, txn.mask or 0)
            data = 0
        return CacheResponse(txn_id=txn.txn_id, data=data, hit=False)

    def _select_victim(self, set_idx: int) -> int:
        """Select victim way based on replacement policy."""
        if self.params.replacement is ReplacementPolicy.LRU:
            return self.lru[set_idx][-1]
        elif self.params.replacement is ReplacementPolicy.FIFO:
            return self.fifo[set_idx][-1]
        elif self.params.replacement is ReplacementPolicy.RANDOM:
            return self._rng.randrange(self.params.ways)
        return self.lru[set_idx][-1]

    def _allocate_line(
        self, set_idx: int, tag: int, line_base: int
    ) -> tuple[int, bool, bool, int | None, bytes | None]:
        way = next((i for i, line in enumerate(self.lines[set_idx]) if not line.valid), None)
        evicted = False
        evicted_dirty = False
        writeback_addr: int | None = None
        writeback_data: bytes | None = None
        if way is None:
            way = self._select_victim(set_idx)
            evicted = True
            victim = self.lines[set_idx][way]
            evicted_dirty = victim.valid and victim.dirty
            if evicted_dirty:
                victim_base = self._addr_from_tag_set(victim.tag, set_idx)
                self.memory.write_line(victim_base, victim.data)
                writeback_addr = victim_base
                writeback_data = bytes(victim.data)
                self.last_writeback = (writeback_addr, writeback_data)

        self.lines[set_idx][way] = CacheLine(
            valid=True,
            dirty=False,
            tag=tag,
            data=self.memory.read_line(line_base, self.params.line_bytes),
        )
        # Track FIFO insertion order
        if self.params.replacement is ReplacementPolicy.FIFO:
            if way in self.fifo[set_idx]:
                self.fifo[set_idx].remove(way)
            self.fifo[set_idx].insert(0, way)
        return way, evicted, evicted_dirty, writeback_addr, writeback_data

    def _find_way(self, set_idx: int, tag: int) -> int | None:
        for way, line in enumerate(self.lines[set_idx]):
            if line.valid and line.tag == tag:
                return way
        return None

    def _touch(self, set_idx: int, way: int) -> None:
        """Update replacement metadata on access."""
        if self.params.replacement is ReplacementPolicy.LRU:
            order = self.lru[set_idx]
            if way in order:
                order.remove(way)
            order.insert(0, way)

    def _line_base(self, addr: int) -> int:
        return addr - (addr % self.params.line_bytes)

    def _set_idx(self, addr: int) -> int:
        return (addr // self.params.line_bytes) % self.params.sets

    def _tag(self, addr: int) -> int:
        return (addr // self.params.line_bytes) // self.params.sets

    def _addr_from_tag_set(self, tag: int, set_idx: int) -> int:
        return (tag * self.params.sets + set_idx) * self.params.line_bytes
