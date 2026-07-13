from cache_vip.reference_model import CacheParams, ReferenceCache
from cache_vip.transactions import CacheOp, CacheTxn


def test_write_then_read_hits_and_returns_merged_data():
    cache = ReferenceCache(CacheParams(sets=4, ways=2, line_bytes=16))
    write = CacheTxn(CacheOp.WRITE, addr=0x20, size=4, data=0xAABBCCDD, mask=0xF, txn_id=1)
    read = CacheTxn(CacheOp.READ, addr=0x20, size=4, txn_id=2)

    cache.access(write)
    response = cache.access(read)

    assert response.hit is True
    assert response.data == 0xAABBCCDD


def test_partial_write_mask_preserves_unmasked_bytes():
    cache = ReferenceCache(CacheParams(sets=4, ways=2, line_bytes=16))
    cache.access(CacheTxn(CacheOp.WRITE, addr=0x30, size=4, data=0x11223344, mask=0xF, txn_id=1))
    cache.access(CacheTxn(CacheOp.WRITE, addr=0x30, size=4, data=0xAABBCCDD, mask=0b0101, txn_id=2))
    response = cache.access(CacheTxn(CacheOp.READ, addr=0x30, size=4, txn_id=3))

    assert response.data == 0x11BB33DD


def test_dirty_eviction_writes_back_to_memory():
    params = CacheParams(sets=1, ways=1, line_bytes=16)
    cache = ReferenceCache(params)

    cache.access(CacheTxn(CacheOp.WRITE, addr=0x00, size=8, data=0x1234, mask=0xFF, txn_id=1))
    response = cache.access(CacheTxn(CacheOp.READ, addr=0x10, size=8, txn_id=2))

    assert response.evicted_dirty is True
    assert cache.memory.read(0x00, 8) == 0x1234
