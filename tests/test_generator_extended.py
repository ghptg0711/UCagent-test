from cache_vip.generator import CacheGenerator, iter_seeded_streams
from cache_vip.reference_model import CacheParams
from cache_vip.transactions import CacheOp


def test_weighted_stream_respects_operation_weights_and_masks() -> None:
    gen = CacheGenerator(CacheParams(sets=4, ways=2, line_bytes=64), seed=9)

    writes = gen.weighted_stream(20, read_weight=0, write_weight=1)
    reads = gen.weighted_stream(10, read_weight=1, write_weight=0)

    assert all(txn.op is CacheOp.WRITE and 0 < txn.mask < (1 << txn.size) for txn in writes)
    assert all(txn.op is CacheOp.READ and txn.data == 0 for txn in reads)


def test_implication_stream_obeys_size_alignment_and_mask_constraints() -> None:
    gen = CacheGenerator(CacheParams(sets=8, ways=2, line_bytes=64), seed=12)

    txns = gen.implication_stream(100)

    assert len(txns) == 100
    for txn in txns:
        assert txn.addr >= 0x1000
        assert txn.addr % 64 != 0 or txn.size == 8
        if txn.op is CacheOp.WRITE:
            assert 0 < txn.mask <= (1 << txn.size) - 1


def test_iter_seeded_streams_is_reproducible_and_distinct() -> None:
    streams = list(iter_seeded_streams((1, 2), 5))
    repeated = list(iter_seeded_streams((1,), 5))[0]

    assert streams[0] == repeated
    assert streams[0] != streams[1]
