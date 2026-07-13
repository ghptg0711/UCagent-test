from dataclasses import replace

from cache_vip.reference_model import CacheParams, ReferenceCache
from cache_vip.regression import _run_named_stream
from cache_vip.transactions import CacheOp, CacheTxn


def test_crv_oracle_tracks_data_across_dirty_eviction() -> None:
    params = CacheParams(sets=1, ways=1, line_bytes=16)
    txns = [
        CacheTxn(CacheOp.WRITE, 0x00, 8, data=0x1122334455667788, mask=0xFF, txn_id=1),
        CacheTxn(CacheOp.READ, 0x10, 8, txn_id=2),
        CacheTxn(CacheOp.READ, 0x00, 8, txn_id=3),
    ]

    result = _run_named_stream("eviction_readback", txns, params)

    assert result["status"] == "PASS"


def test_crv_oracle_rejects_corrupted_model_read(monkeypatch) -> None:
    original_access = ReferenceCache.access

    def corrupted_access(self, txn):
        response = original_access(self, txn)
        if txn.op is CacheOp.READ:
            return replace(response, data=response.data ^ 1)
        return response

    monkeypatch.setattr(ReferenceCache, "access", corrupted_access)
    txns = [
        CacheTxn(CacheOp.WRITE, 0x20, 4, data=0xAABBCCDD, mask=0xF, txn_id=1),
        CacheTxn(CacheOp.READ, 0x20, 4, txn_id=2),
    ]

    result = _run_named_stream("corrupted_read", txns, CacheParams())

    assert result["status"] == "FAIL"
    assert "architectural read mismatch" in result["error"]
