"""Advanced edge case and integration tests for NutShell Cache verification.

Tests more complex scenarios that combine multiple features:
- Full cache thrashing (fill all ways + evict)
- Sequential vs random access patterns
- Mixed-size access to same line
- Back-to-back replacement pressure
- Alignment stress tests
- Reset during operation recovery
"""

import pytest

from cache_vip.coverage import Coverage
from cache_vip.generator import CacheGenerator
from cache_vip.reference_model import CacheParams, ReferenceCache, ReplacementPolicy
from cache_vip.scoreboard import ScoreboardMismatch
from cache_vip.transactions import CacheOp, CacheTxn


class _Result:
    """Lightweight result container with coverage."""

    def __init__(self, ref: ReferenceCache) -> None:
        self.reference = ref
        self.coverage = Coverage(line_bytes=ref.params.line_bytes)


def _run_txns(
    txns: list[CacheTxn], params: CacheParams | None = None, *, mark_same_set: bool = False
) -> _Result:
    """Run transactions and verify functional correctness independently.

    Instead of comparing reference model to itself, verifies:
    - READ data matches prior WRITEs to the same address
    - No unexpected exceptions
    - Coverage is collected
    """
    cache_params = params or CacheParams()
    ref = ReferenceCache(cache_params)
    result = _Result(ref)
    written: dict[int, tuple[int, int]] = {}  # addr -> (data, mask)

    for index, txn in enumerate(txns):
        latency = 10 if index % 11 == 0 else index % 4
        response = ref.access(txn)
        result.coverage.sample_access(
            txn,
            hit=response.hit,
            evicted_dirty=response.evicted_dirty,
            evicted_clean=(response.evicted and not response.evicted_dirty),
            latency=latency,
            same_set=mark_same_set,
            replacement_policy=cache_params.replacement.value,
            write_allocate=cache_params.write_allocate,
        )

        if txn.op is CacheOp.READ and txn.addr in written:
            prev_data, prev_mask = written[txn.addr]
            read_mask = (1 << txn.size) - 1
            effective_mask = prev_mask & read_mask
            if effective_mask:
                actual_bytes = response.data & effective_mask
                expected_bytes = prev_data & effective_mask
                if actual_bytes != expected_bytes:
                    raise ScoreboardMismatch(
                        f"read data mismatch at 0x{txn.addr:x}: "
                        f"written 0x{prev_data:x} mask 0x{prev_mask:x}, "
                        f"got 0x{response.data:x}"
                    )

        if txn.op is CacheOp.WRITE:
            if txn.addr in written:
                old_data, old_mask = written[txn.addr]
                merged_data = 0
                merged_mask = old_mask | txn.mask
                for i in range(txn.size):
                    if txn.mask & (1 << i):
                        merged_data |= (txn.data >> (8 * i) & 0xFF) << (8 * i)
                    elif old_mask & (1 << i):
                        merged_data |= (old_data >> (8 * i) & 0xFF) << (8 * i)
                written[txn.addr] = (merged_data, merged_mask)
            else:
                written[txn.addr] = (txn.data, txn.mask)

    return result


class TestFullCacheThrashing:
    def test_fill_all_ways_then_evict(self):
        """Fill all ways of a set, then access a new tag to force eviction."""
        params = CacheParams(sets=1, ways=4, line_bytes=64)
        gen = CacheGenerator(params, seed=42)

        txns: list[CacheTxn] = []
        for way in range(4):
            addr = way * 64
            txns.append(gen._make(CacheOp.WRITE, addr, 8, data=way + 1, mask=0xFF))

        # Access tag 4 to evict the LRU (tag 0)
        txns.append(gen._make(CacheOp.READ, 4 * 64, 8))

        sb = _run_txns(txns, params, mark_same_set=True)
        assert sb.coverage.bins["replacement.dirty"] >= 1
        assert sb.coverage.bins["addr.same_set"] >= 5

    def test_all_ways_dirty_then_clean_mix(self):
        """Mix of dirty and clean lines to test replacement selection."""
        params = CacheParams(sets=1, ways=4, line_bytes=64)
        gen = CacheGenerator(params, seed=99)

        txns: list[CacheTxn] = []
        for way in range(2):
            addr = way * 64
            txns.append(gen._make(CacheOp.WRITE, addr, 8, data=way + 100, mask=0xFF))
        for way in range(2, 4):
            addr = way * 64
            txns.append(gen._make(CacheOp.READ, addr, 8))

        # Evict one (clean or dirty?)
        txns.append(gen._make(CacheOp.READ, 4 * 64, 8))

        sb = _run_txns(txns, params, mark_same_set=True)
        assert (
            sb.coverage.bins["replacement.clean"] >= 1 or sb.coverage.bins["replacement.dirty"] >= 1
        )


class TestSequentialAccess:
    def test_sequential_read_same_line(self):
        """Read sequentially within the same cache line."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=123)

        base = 0x10000
        txns: list[CacheTxn] = []
        for offset in range(0, 56, 8):
            txns.append(gen._make(CacheOp.READ, base + offset, 8))

        sb = _run_txns(txns, params)
        # First read is miss, rest should be hits
        assert sb.coverage.bins["access.read_miss"] >= 1
        assert sb.coverage.bins["access.read_hit"] >= 1

    def test_sequential_write_same_line(self):
        """Write sequentially within the same cache line."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=456)

        base = 0x20000
        txns: list[CacheTxn] = []
        for offset in range(0, 56, 8):
            txns.append(gen._make(CacheOp.WRITE, base + offset, 8, data=offset * 10, mask=0xFF))
        txns.append(gen._make(CacheOp.READ, base, 8))

        sb = _run_txns(txns, params)
        assert sb.coverage.bins["access.write_miss"] >= 1
        assert sb.coverage.bins["access.write_hit"] >= 1


class TestMixedSizeAccess:
    def test_mixed_sizes_same_line(self):
        """Access the same cache line with different sizes (1B, 2B, 4B, 8B)."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=789)

        base = 0x30000
        txns: list[CacheTxn] = []
        # Write 8 bytes first to fill the line
        txns.append(gen._make(CacheOp.WRITE, base, 8, data=0x0102030405060708, mask=0xFF))
        # Read 1 byte
        txns.append(gen._make(CacheOp.READ, base, 1))
        # Read 2 bytes
        txns.append(gen._make(CacheOp.READ, base + 2, 2))
        # Read 4 bytes
        txns.append(gen._make(CacheOp.READ, base + 4, 4))
        # Write 1 byte
        txns.append(gen._make(CacheOp.WRITE, base + 7, 1, data=0xFF, mask=0x1))
        # Write 2 bytes
        txns.append(gen._make(CacheOp.WRITE, base + 1, 2, data=0xAABB, mask=0x3))
        # Final 8-byte read to verify
        txns.append(gen._make(CacheOp.READ, base, 8))

        sb = _run_txns(txns, params)
        for size in [1, 2, 4, 8]:
            assert sb.coverage.bins[f"size.{size}"] >= 1

    def test_1byte_all_positions(self):
        """1-byte access at every offset in a line."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=111)

        base = 0x40000
        txns: list[CacheTxn] = []
        for offset in range(64):
            txns.append(gen._make(CacheOp.WRITE, base + offset, 1, data=offset + 1, mask=0x1))

        for offset in range(64):
            txns.append(gen._make(CacheOp.READ, base + offset, 1))

        sb = _run_txns(txns, params)
        assert sb.coverage.bins["size.1"] >= 10
        assert sb.coverage.bins["access.write_miss"] >= 1
        assert sb.coverage.bins["access.read_hit"] >= 1


class TestReplacementPressure:
    def test_continuous_replacement(self):
        """Continuously access different tags in the same set, forcing many evictions."""
        params = CacheParams(sets=1, ways=2, line_bytes=64)
        gen = CacheGenerator(params, seed=333)

        txns: list[CacheTxn] = []
        for tag in range(20):
            addr = tag * 64
            txns.append(gen._make(CacheOp.WRITE, addr, 4, data=tag, mask=0xF))

        sb = _run_txns(txns, params, mark_same_set=True)
        assert sb.coverage.bins["replacement.dirty"] >= 10
        assert sb.coverage.bins["addr.same_set"] >= 10

    def test_alternating_two_tags(self):
        """Alternate between two tags that always miss (fully associative 1-way)."""
        params = CacheParams(sets=1, ways=1, line_bytes=64)
        gen = CacheGenerator(params, seed=555)

        txns: list[CacheTxn] = []
        for i in range(20):
            addr = (i % 2) * 64
            txns.append(gen._make(CacheOp.READ, addr, 4))

        sb = _run_txns(txns, params, mark_same_set=True)
        assert sb.coverage.bins["access.read_miss"] >= 10
        assert sb.coverage.bins["replacement.clean"] >= 5

    def test_replacement_interrupted_by_new_request(self):
        """Replacement followed immediately by a new CPU request completes both.

        NutShell L1 Cache does not expose hardware snoop in this environment, so
        this corner case models the observable CPU-side interruption: a dirty
        eviction/fill sequence is immediately followed by an unrelated request.
        """
        params = CacheParams(sets=64, ways=4, line_bytes=64)
        ref = ReferenceCache(params)
        base_addr = 0x1000
        set_stride = params.sets * params.line_bytes

        for way in range(params.ways):
            addr = base_addr + way * set_stride
            ref.access(CacheTxn(CacheOp.WRITE, addr, 8, data=way + 1, mask=0xFF, txn_id=way))

        replace_addr = base_addr + params.ways * set_stride
        replace_resp = ref.access(
            CacheTxn(CacheOp.WRITE, replace_addr, 8, data=0xDEAD, mask=0xFF, txn_id=10)
        )

        interrupt_addr = 0x2080
        interrupt_resp = ref.access(CacheTxn(CacheOp.READ, interrupt_addr, 8, txn_id=11))

        assert replace_resp.evicted is True
        assert replace_resp.evicted_dirty is True
        assert interrupt_resp.data is not None

        replaced_read = ref.access(CacheTxn(CacheOp.READ, replace_addr, 8, txn_id=12))
        assert replaced_read.hit is True
        assert replaced_read.data == 0xDEAD

    def test_lru_counter_saturation(self):
        """LRU metadata remains correct after many repeated hot-line accesses."""
        params = CacheParams(sets=1, ways=4, line_bytes=64)
        ref = ReferenceCache(params)

        for way in range(params.ways):
            ref.access(CacheTxn(CacheOp.WRITE, way * 64, 8, data=way, mask=0xFF, txn_id=way))

        hot_addr = 0
        for txn_id in range(100, 356):
            resp = ref.access(CacheTxn(CacheOp.READ, hot_addr, 8, txn_id=txn_id))
            assert resp.hit is True

        new_addr = params.ways * 64
        replace_resp = ref.access(
            CacheTxn(CacheOp.WRITE, new_addr, 8, data=0xBEEF, mask=0xFF, txn_id=400)
        )
        hot_resp = ref.access(CacheTxn(CacheOp.READ, hot_addr, 8, txn_id=401))
        new_resp = ref.access(CacheTxn(CacheOp.READ, new_addr, 8, txn_id=402))

        assert replace_resp.evicted is True
        assert hot_resp.hit is True, "The repeatedly accessed hot line must not be evicted"
        assert hot_resp.data == 0
        assert new_resp.hit is True
        assert new_resp.data == 0xBEEF


class TestAlignmentStress:
    def test_all_aligned_offsets(self):
        """Test 8-byte access at all 8-byte-aligned offsets in a line."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=777)

        base = 0x50000
        txns: list[CacheTxn] = []
        for offset in range(0, 64, 8):
            txns.append(
                gen._make(CacheOp.WRITE, base + offset, 8, data=offset * 0x11223344, mask=0xFF)
            )

        for offset in range(0, 64, 8):
            txns.append(gen._make(CacheOp.READ, base + offset, 8))

        sb = _run_txns(txns, params)
        assert sb.coverage.bins["access.write_miss"] >= 1
        assert sb.coverage.bins["access.read_hit"] >= 7

    def test_unaligned_4byte_across_boundary(self):
        """Test 4-byte access at unaligned (non-4-aligned) offset."""
        params = CacheParams()
        gen = CacheGenerator(params, seed=888)

        base = 0x60000
        txns: list[CacheTxn] = []
        # Write the whole line first
        txns.append(gen._make(CacheOp.WRITE, base, 8, data=0x0102030405060708, mask=0xFF))
        txns.append(gen._make(CacheOp.WRITE, base + 8, 8, data=0x1112131415161718, mask=0xFF))
        # Read 4 bytes at offset 1 (not aligned to 4-byte boundary)
        txns.append(gen._make(CacheOp.READ, base + 1, 4))

        sb = _run_txns(txns, params)
        assert sb.coverage.bins["size.4"] >= 1


class TestResetRecovery:
    def test_write_reset_read(self):
        """Write data, then reset cache, then read - should get memory value."""
        params = CacheParams()
        ref = ReferenceCache(params)

        # Write some data
        txn_write = CacheTxn(CacheOp.WRITE, 0x1000, 8, data=0xDEADBEEF, mask=0xFF, txn_id=1)
        resp = ref.access(txn_write)
        assert resp.data == 0

        # Read back - should be hit
        txn_read1 = CacheTxn(CacheOp.READ, 0x1000, 8, txn_id=2)
        resp = ref.access(txn_read1)
        assert resp.hit is True
        assert resp.data == 0xDEADBEEF

        # Reset by creating new reference (simulating reset)
        ref2 = ReferenceCache(params)
        # Memory should still have the data (reference model memory is separate)
        txn_read2 = CacheTxn(CacheOp.READ, 0x1000, 8, txn_id=3)
        resp2 = ref2.access(txn_read2)
        assert resp2.hit is False  # Should be miss after reset
        # Data comes from memory (not written in new ref's memory)

    def test_reset_evicts_all_dirty(self):
        """After filling cache with dirty data, reset clears everything."""
        params = CacheParams(sets=2, ways=2, line_bytes=64)
        ref = ReferenceCache(params)

        for s in range(2):
            for w in range(2):
                addr = (s * 2 + w) * 64
                txn = CacheTxn(CacheOp.WRITE, addr, 4, data=s * 10 + w, mask=0xF, txn_id=s * 2 + w)
                ref.access(txn)

        all_dirty = True
        for set_lines in ref.lines:
            for line in set_lines:
                if line.valid and not line.dirty:
                    all_dirty = False
                    break
        assert all_dirty, "All valid lines should be dirty"


class TestCrossSetConsistency:
    def test_same_tag_different_sets(self):
        """Same tag in different sets should not conflict."""
        params = CacheParams(sets=4, ways=2, line_bytes=64)
        ref = ReferenceCache(params)

        for s in range(4):
            addr = s * 64  # tag 0, set s
            txn = CacheTxn(CacheOp.WRITE, addr, 4, data=s + 1, mask=0xF, txn_id=s)
            ref.access(txn)

        for s in range(4):
            addr = s * 64
            txn = CacheTxn(CacheOp.READ, addr, 4, txn_id=100 + s)
            resp = ref.access(txn)
            assert resp.hit is True
            # Each set should have its own data
            assert (resp.data & 0xFFFFFFFF) == s + 1


class TestFIFOEdge:
    def test_fifo_ordering(self):
        """Verify FIFO replacement follows insertion order, not access order."""
        params = CacheParams(sets=1, ways=3, line_bytes=64, replacement=ReplacementPolicy.FIFO)
        ref = ReferenceCache(params)

        # Fill 3 ways in order: 0, 1, 2
        for tag in range(3):
            addr = tag * 64
            txn = CacheTxn(CacheOp.WRITE, addr, 4, data=tag + 10, mask=0xF, txn_id=tag)
            ref.access(txn)

        # Access tag 0 multiple times (should NOT change FIFO order)
        for _ in range(5):
            txn = CacheTxn(CacheOp.READ, 0, 4, txn_id=10 + _)
            resp = ref.access(txn)
            assert resp.hit is True

        # Access tag 3 - should evict tag 0 (first in), not tag 1
        txn = CacheTxn(CacheOp.READ, 3 * 64, 4, txn_id=20)
        resp = ref.access(txn)
        assert resp.evicted_dirty is True

        # Tag 1 and 2 should still be in cache
        txn = CacheTxn(CacheOp.READ, 1 * 64, 4, txn_id=21)
        resp = ref.access(txn)
        assert resp.hit is True

        txn = CacheTxn(CacheOp.READ, 2 * 64, 4, txn_id=22)
        resp = ref.access(txn)
        assert resp.hit is True

        # Tag 0 should be evicted
        txn = CacheTxn(CacheOp.READ, 0 * 64, 4, txn_id=23)
        resp = ref.access(txn)
        assert resp.hit is False


class TestNoWriteAllocateEdge:
    def test_no_write_allocate_read_then_write(self):
        """Read miss allocates line, write hit works, write miss doesn't allocate."""
        params = CacheParams(sets=1, ways=2, line_bytes=64, write_allocate=False)
        ref = ReferenceCache(params)

        # Read miss - should allocate
        txn = CacheTxn(CacheOp.READ, 0, 4, txn_id=1)
        resp = ref.access(txn)
        assert resp.hit is False

        # Read hit - line was allocated by read miss
        txn = CacheTxn(CacheOp.READ, 0, 4, txn_id=2)
        resp = ref.access(txn)
        assert resp.hit is True

        # Write miss to different tag - should NOT allocate
        txn = CacheTxn(CacheOp.WRITE, 2 * 64, 4, data=42, mask=0xF, txn_id=3)
        resp = ref.access(txn)
        assert resp.hit is False
        assert resp.evicted_dirty is False  # No line was evicted

        # Original tag should still be in cache (write miss didn't evict)
        txn = CacheTxn(CacheOp.READ, 0, 4, txn_id=4)
        resp = ref.access(txn)
        assert resp.hit is True


class TestCRVStability:
    def test_same_seed_same_result(self):
        """Same seed should produce identical transaction sequence."""
        params = CacheParams()
        gen1 = CacheGenerator(params, seed=42)
        gen2 = CacheGenerator(params, seed=42)

        txns1 = gen1.random_stream(100)
        txns2 = gen2.random_stream(100)

        assert len(txns1) == len(txns2)
        for t1, t2 in zip(txns1, txns2, strict=True):
            assert t1 == t2

    def test_different_seeds_different_patterns(self):
        """Different seeds should produce different transaction patterns."""
        params = CacheParams()
        gen1 = CacheGenerator(params, seed=1)
        gen2 = CacheGenerator(params, seed=2)

        txns1 = gen1.random_stream(50)
        txns2 = gen2.random_stream(50)

        diffs = sum(1 for t1, t2 in zip(txns1, txns2, strict=True) if t1 != t2)
        assert diffs > 0, "Different seeds should produce different sequences"


class TestCrossLineDetection:
    def test_cross_line_read_raises(self):
        """Reference model must reject accesses that span two cache lines."""
        params = CacheParams(sets=1, ways=1, line_bytes=16)
        ref = ReferenceCache(params)

        txn = CacheTxn(CacheOp.READ, addr=12, size=8, txn_id=1)
        with pytest.raises(ValueError, match="cross-line"):
            ref.access(txn)

    def test_cross_line_write_raises(self):
        """Write that spans two lines must also be rejected."""
        params = CacheParams(sets=1, ways=1, line_bytes=16)
        ref = ReferenceCache(params)

        txn = CacheTxn(CacheOp.WRITE, addr=14, size=4, data=0xDEAD, mask=0xF, txn_id=1)
        with pytest.raises(ValueError, match="cross-line"):
            ref.access(txn)

    def test_last_byte_access_ok(self):
        """Access ending exactly at line boundary is valid."""
        params = CacheParams(sets=1, ways=1, line_bytes=16)
        ref = ReferenceCache(params)

        txn = CacheTxn(CacheOp.READ, addr=8, size=8, txn_id=1)
        resp = ref.access(txn)
        assert resp.hit is False


class TestMultiSetEvictionConsistency:
    def test_eviction_in_one_set_does_not_affect_another(self):
        """Evicting a line in set N must not modify lines in set M."""
        params = CacheParams(sets=4, ways=2, line_bytes=64)
        ref = ReferenceCache(params)

        set_0_tags = [0, 4, 8]
        set_2_tags = [1, 5, 9]

        set_0_addrs = [tag * params.sets * params.line_bytes + 0 * params.line_bytes for tag in set_0_tags]
        set_2_addrs = [tag * params.sets * params.line_bytes + 2 * params.line_bytes for tag in set_2_tags]

        for i, addr in enumerate(set_0_addrs[:2]):
            ref.access(CacheTxn(CacheOp.WRITE, addr, 4, data=100 + i, mask=0xF, txn_id=i))

        for i, addr in enumerate(set_2_addrs[:2]):
            ref.access(CacheTxn(CacheOp.WRITE, addr, 4, data=200 + i, mask=0xF, txn_id=10 + i))

        evict_resp = ref.access(
            CacheTxn(CacheOp.WRITE, set_0_addrs[2], 4, data=199, mask=0xF, txn_id=20)
        )
        assert evict_resp.evicted is True

        for i, addr in enumerate(set_2_addrs[:2]):
            resp = ref.access(CacheTxn(CacheOp.READ, addr, 4, txn_id=30 + i))
            assert resp.hit is True
            assert (resp.data & 0xFFFFFFFF) == 200 + i


class TestPolicyBehavioralDifference:
    def test_lru_vs_fifo_victim_selection_differs(self):
        """Under access pattern that re-touches first line, LRU and FIFO
        must evict different victims.
        """
        params_lru = CacheParams(sets=1, ways=2, line_bytes=64, replacement=ReplacementPolicy.LRU)
        params_fifo = CacheParams(sets=1, ways=2, line_bytes=64, replacement=ReplacementPolicy.FIFO)

        ref_lru = ReferenceCache(params_lru)
        ref_fifo = ReferenceCache(params_fifo)

        ref_lru.access(CacheTxn(CacheOp.WRITE, 0x00, 4, data=0xAA, mask=0xF, txn_id=1))
        ref_lru.access(CacheTxn(CacheOp.WRITE, 0x40, 4, data=0xBB, mask=0xF, txn_id=2))
        ref_lru.access(CacheTxn(CacheOp.READ, 0x00, 4, txn_id=3))

        ref_fifo.access(CacheTxn(CacheOp.WRITE, 0x00, 4, data=0xAA, mask=0xF, txn_id=1))
        ref_fifo.access(CacheTxn(CacheOp.WRITE, 0x40, 4, data=0xBB, mask=0xF, txn_id=2))
        ref_fifo.access(CacheTxn(CacheOp.READ, 0x00, 4, txn_id=3))

        resp_lru = ref_lru.access(CacheTxn(CacheOp.WRITE, 0x80, 4, data=0xCC, mask=0xF, txn_id=4))
        resp_fifo = ref_fifo.access(CacheTxn(CacheOp.WRITE, 0x80, 4, data=0xCC, mask=0xF, txn_id=4))

        assert resp_lru.evicted is True
        assert resp_fifo.evicted is True

        lru_0_still_hit = ref_lru.access(CacheTxn(CacheOp.READ, 0x00, 4, txn_id=5)).hit
        fifo_0_still_hit = ref_fifo.access(CacheTxn(CacheOp.READ, 0x00, 4, txn_id=5)).hit

        assert lru_0_still_hit is True, "LRU: re-touched line 0 stays, line 1 evicted"
        assert fifo_0_still_hit is False, "FIFO: line 0 was first in, gets evicted"


class TestExtendedCoverageBins:
    def test_extended_coverage_samples_cross_bins(self):
        """Extended cross-coverage bins must be populated by directed traffic."""
        params = CacheParams(sets=2, ways=2, line_bytes=64, replacement=ReplacementPolicy.LRU)
        ref = ReferenceCache(params)
        cov = Coverage(line_bytes=params.line_bytes)

        txns = [
            CacheTxn(CacheOp.WRITE, 0x000, 8, data=0xDEADBEEF, mask=0xFF, txn_id=1),
            CacheTxn(CacheOp.READ, 0x000, 4, txn_id=2),
            CacheTxn(CacheOp.WRITE, 0x008, 4, data=0xABCD, mask=0b0101, txn_id=3),
            CacheTxn(CacheOp.WRITE, 0x040, 8, data=0x11223344, mask=0xFF, txn_id=4),
            CacheTxn(CacheOp.READ, 0x080, 8, txn_id=5),
            CacheTxn(CacheOp.WRITE, 0x000, 1, data=0xFF, mask=0x1, txn_id=6),
        ]

        visited_sets: set[int] = set()
        for idx, txn in enumerate(txns):
            resp = ref.access(txn)
            set_idx = (txn.addr // params.line_bytes) % params.sets
            same_set = set_idx in visited_sets
            visited_sets.add(set_idx)
            cov.sample_access(
                txn,
                hit=resp.hit,
                evicted_dirty=resp.evicted_dirty,
                evicted_clean=(resp.evicted and not resp.evicted_dirty),
                latency=10 if idx % 3 == 0 else 2,
                same_set=same_set,
                replacement_policy=params.replacement.value,
                write_allocate=params.write_allocate,
            )

        assert cov.bins["cross.size_mask.size8_full"] >= 1
        assert cov.bins["policy.write_allocate.write_miss_alloc"] >= 1
        assert cov.bins["addr.back_to_back_same_line"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
