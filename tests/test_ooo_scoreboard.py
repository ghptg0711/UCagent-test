"""Tests for Out-of-order Scoreboard (P1-2 deliverable)."""

import pytest

from cache_vip.ooo_scoreboard import OooScoreboard
from cache_vip.scoreboard import ScoreboardMismatch
from cache_vip.transactions import CacheOp, CacheResponse, CacheTxn


class TestOooScoreboard:
    """Test out-of-order transaction matching by txn_id."""

    def test_in_order_match(self):
        """Responses arriving in order should match correctly."""
        sb = OooScoreboard()
        for tid in range(3):
            txn = CacheTxn(CacheOp.READ, addr=0x100 * tid, size=8, txn_id=tid)
            resp = CacheResponse(txn_id=tid, data=0xDEAD, hit=True)
            sb.push_expected(txn, resp)

        for tid in range(3):
            sb.compare_actual(CacheResponse(txn_id=tid, data=0xDEAD, hit=True))

        assert sb.matched == 3
        assert sb.is_empty

    def test_out_of_order_match(self):
        """Responses arriving in reverse order should still match by txn_id."""
        sb = OooScoreboard()
        txns = [
            CacheTxn(CacheOp.WRITE, addr=0x200, size=4, data=0x1111, mask=0xF, txn_id=1),
            CacheTxn(CacheOp.READ, addr=0x300, size=4, txn_id=2),
            CacheTxn(CacheOp.READ, addr=0x400, size=4, txn_id=3),
        ]
        for txn in txns:
            resp = CacheResponse(txn_id=txn.txn_id, data=txn.data or 0, hit=True)
            sb.push_expected(txn, resp)

        # Responses arrive in reverse: 3, 1, 2
        sb.compare_actual(CacheResponse(txn_id=3, data=0, hit=True))
        sb.compare_actual(CacheResponse(txn_id=1, data=0x1111, hit=True))
        sb.compare_actual(CacheResponse(txn_id=2, data=0, hit=True))

        assert sb.matched == 3
        assert sb.is_empty

    def test_orphan_response_detected(self):
        """Response with unknown txn_id should raise ScoreboardMismatch."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=1)
        sb.push_expected(txn, CacheResponse(txn_id=1, data=0, hit=True))

        with pytest.raises(ScoreboardMismatch, match="unexpected or duplicate"):
            sb.compare_actual(CacheResponse(txn_id=999, data=0, hit=True))

        assert sb.mismatched == 1
        assert len(sb.orphan) == 1

    def test_duplicate_txn_id_rejected(self):
        """Pushing the same txn_id twice should raise."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=5)
        sb.push_expected(txn, CacheResponse(txn_id=5, data=0, hit=True))

        with pytest.raises(ScoreboardMismatch, match="duplicate"):
            sb.push_expected(txn, CacheResponse(txn_id=5, data=0, hit=True))

    def test_data_mismatch_detected(self):
        """Read data divergence should be caught."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x100, size=4, txn_id=1)
        sb.push_expected(txn, CacheResponse(txn_id=1, data=0xCAFEBABE, hit=True))

        with pytest.raises(ScoreboardMismatch, match="read data mismatch"):
            sb.compare_actual(CacheResponse(txn_id=1, data=0xDEADBEEF, hit=True))

    def test_hit_miss_mismatch_detected(self):
        """Hit/miss status divergence should be caught."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x100, size=4, txn_id=1)
        sb.push_expected(txn, CacheResponse(txn_id=1, data=0, hit=True))

        with pytest.raises(ScoreboardMismatch, match="hit/miss mismatch"):
            sb.compare_actual(CacheResponse(txn_id=1, data=0, hit=False))

    def test_drain_pending(self):
        """drain_pending should return unmatched txn_ids."""
        sb = OooScoreboard()
        for tid in [10, 20, 30]:
            txn = CacheTxn(CacheOp.READ, addr=0x100 * tid, size=4, txn_id=tid)
            sb.push_expected(txn, CacheResponse(txn_id=tid, data=0, hit=True))

        # Only match one
        sb.compare_actual(CacheResponse(txn_id=20, data=0, hit=True))

        remaining = sb.drain_pending()
        assert sorted(remaining) == [10, 30]
        assert sb.is_empty

    def test_summary(self):
        """Summary should report correct counts."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x100, size=4, txn_id=1)
        sb.push_expected(txn, CacheResponse(txn_id=1, data=0, hit=True))
        sb.compare_actual(CacheResponse(txn_id=1, data=0, hit=True))

        s = sb.summary()
        assert s["matched"] == 1
        assert s["mismatched"] == 0
        assert s["pending"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
