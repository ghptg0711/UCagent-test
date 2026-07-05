import pytest

from cache_vip.faults import FaultInjector
from cache_vip.generator import CacheGenerator
from cache_vip.reference_model import CacheParams, ReferenceCache
from cache_vip.scoreboard import Scoreboard, ScoreboardMismatch
from cache_vip.transactions import CacheTxn
from cache_vip.transactions import CacheOp


def test_replacement_sequence_forces_dirty_eviction():
    params = CacheParams(sets=2, ways=2, line_bytes=16)
    gen = CacheGenerator(params, seed=7)
    sb = Scoreboard(reference=ReferenceCache(params))

    saw_dirty_eviction = False
    for txn in gen.replacement_sequence(set_idx=1, dirty=True):
        expected = sb.push_request(txn)
        saw_dirty_eviction |= expected.evicted_dirty
        sb.compare_response(txn, expected)

    assert saw_dirty_eviction


def test_scoreboard_detects_read_corruption():
    gen = CacheGenerator(CacheParams(sets=4, ways=2, line_bytes=16), seed=3)
    sb = Scoreboard()
    txns = gen.partial_write_sequence(0x100)

    for txn in txns[:-1]:
        expected = sb.push_request(txn)
        sb.compare_response(txn, expected)

    read = txns[-1]
    expected = sb.push_request(read)
    corrupted = FaultInjector.flip_read_bit(expected, bit=4)

    with pytest.raises(ScoreboardMismatch):
        sb.compare_response(read, corrupted)


def test_scoreboard_detects_response_order_swap():
    sb = Scoreboard()
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x40, size=4, data=0x12345678, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x40, size=4, txn_id=2),
    ]
    actual = [sb.push_request(txn) for txn in txns]
    swapped = FaultInjector.swap_order(actual)

    with pytest.raises(ScoreboardMismatch):
        sb.compare_response(txns[0], swapped[0])


def test_scoreboard_detects_partial_write_mask_drop():
    expected_sb = Scoreboard()
    faulty_ref = ReferenceCache()
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x80, size=4, data=0x11223344, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.WRITE, addr=0x80, size=4, data=0xAABBCCDD, mask=0b0101, txn_id=2),
        CacheTxn(CacheOp.READ, addr=0x80, size=4, txn_id=3),
    ]

    for txn in txns[:1]:
        expected_sb.push_request(txn)
        expected_sb.compare_response(txn, faulty_ref.access(txn))

    expected_sb.push_request(txns[1])
    expected_sb.compare_response(txns[1], faulty_ref.access(FaultInjector.drop_mask_bit(txns[1], bit=0)))

    expected_sb.push_request(txns[2])
    with pytest.raises(ScoreboardMismatch):
        expected_sb.compare_response(txns[2], faulty_ref.access(txns[2]))


def test_scoreboard_detects_dirty_writeback_corruption():
    params = CacheParams(sets=1, ways=1, line_bytes=16)
    sb = Scoreboard(reference=ReferenceCache(params))
    txns = [
        CacheTxn(CacheOp.WRITE, addr=0x00, size=8, data=0x123456789ABCDEF0, mask=0xFF, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x10, size=8, txn_id=2),
    ]

    expected = sb.push_request(txns[0])
    sb.compare_response(txns[0], expected)
    expected = sb.push_request(txns[1])
    corrupted = FaultInjector.corrupt_writeback_byte(expected)

    with pytest.raises(ScoreboardMismatch):
        sb.compare_response(txns[1], corrupted)


def test_directed_stream_reaches_required_core_coverage():
    params = CacheParams(sets=4, ways=2, line_bytes=64)
    sb = Scoreboard(reference=ReferenceCache(params))
    gen = CacheGenerator(params, seed=19)
    stream = [
        CacheTxn(CacheOp.READ, addr=0x00, size=1, txn_id=1),
        CacheTxn(CacheOp.READ, addr=0x00, size=1, txn_id=2),
        CacheTxn(CacheOp.WRITE, addr=0x08, size=2, data=0xABCD, mask=0x3, txn_id=3),
        CacheTxn(CacheOp.WRITE, addr=0x08, size=2, data=0x00EF, mask=0x1, txn_id=4),
        CacheTxn(CacheOp.WRITE, addr=0x10, size=4, data=0x11223344, mask=0b0101, txn_id=5),
        CacheTxn(CacheOp.WRITE, addr=0x18, size=8, data=0xAABBCCDDEEFF0011, mask=0xFF, txn_id=6),
        CacheTxn(CacheOp.READ, addr=0x38, size=8, txn_id=7),
    ]
    stream.extend(gen.replacement_sequence(set_idx=1, dirty=True))
    stream.extend(gen.replacement_sequence(set_idx=2, dirty=False))

    for index, txn in enumerate(stream):
        expected = sb.push_request(txn, latency=10 if index % 3 == 0 else 1, same_set=index >= 7)
        sb.compare_response(txn, expected)

    assert sb.coverage.percent() == 100.0
    assert sb.coverage.missing() == []


def test_random_stream_contains_reads_and_writes():
    gen = CacheGenerator(seed=11)
    stream = gen.random_stream(200)
    ops = {txn.op for txn in stream}

    assert CacheOp.READ in ops
    assert CacheOp.WRITE in ops
