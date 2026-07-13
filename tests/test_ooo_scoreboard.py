"""Tests for Out-of-order Scoreboard (P1-2 deliverable)."""

import pytest

from cache_vip.ooo_scoreboard import OooScoreboard, WritebackEvent
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

    def test_writeback_tracked_on_dirty_eviction(self):
        """Dirty eviction should auto-register an expected writeback event."""
        sb = OooScoreboard()
        wb_data = bytes([0x11, 0x22, 0x33, 0x44] + [0] * 60)
        txn = CacheTxn(CacheOp.READ, addr=0x200, size=4, txn_id=42)
        resp = CacheResponse(
            txn_id=42,
            data=0,
            hit=False,
            evicted=True,
            evicted_dirty=True,
            writeback_addr=0x100,
            writeback_data=wb_data,
        )
        sb.push_expected(txn, resp)

        assert 42 in sb.expected_writebacks
        assert sb.expected_writebacks[42].addr == 0x100
        assert sb.expected_writebacks[42].data == wb_data
        assert not sb.all_writebacks_matched

    def test_writeback_match_success(self):
        """Correct writeback event should match without error."""
        sb = OooScoreboard()
        wb_data = b"\xAA\xBB\xCC\xDD" + b"\x00" * 60
        txn = CacheTxn(CacheOp.READ, addr=0x400, size=4, txn_id=7)
        resp = CacheResponse(
            txn_id=7,
            data=0,
            hit=False,
            evicted=True,
            evicted_dirty=True,
            writeback_addr=0x300,
            writeback_data=wb_data,
        )
        sb.push_expected(txn, resp)
        sb.compare_actual(resp)
        sb.compare_writeback(WritebackEvent(txn_id=7, addr=0x300, data=wb_data))

        assert sb.matched_writebacks == 1
        assert sb.all_writebacks_matched

    def test_writeback_addr_mismatch_detected(self):
        """Writeback to wrong address should be caught."""
        sb = OooScoreboard()
        wb_data = b"\x11" * 64
        txn = CacheTxn(CacheOp.READ, addr=0x800, size=4, txn_id=99)
        resp = CacheResponse(
            txn_id=99,
            data=0,
            hit=False,
            evicted=True,
            evicted_dirty=True,
            writeback_addr=0x800,
            writeback_data=wb_data,
        )
        sb.push_expected(txn, resp)

        with pytest.raises(ScoreboardMismatch, match="writeback addr mismatch"):
            sb.compare_writeback(WritebackEvent(txn_id=99, addr=0x900, data=wb_data))

        assert sb.mismatched_writebacks == 1

    def test_writeback_data_mismatch_detected(self):
        """Corrupted writeback data should be caught."""
        sb = OooScoreboard()
        txn = CacheTxn(CacheOp.READ, addr=0x1000, size=4, txn_id=55)
        resp = CacheResponse(
            txn_id=55,
            data=0,
            hit=False,
            evicted=True,
            evicted_dirty=True,
            writeback_addr=0x1000,
            writeback_data=b"\x00" * 64,
        )
        sb.push_expected(txn, resp)

        bad_data = bytearray(64)
        bad_data[0] = 0xFF
        with pytest.raises(ScoreboardMismatch, match="writeback data mismatch"):
            sb.compare_writeback(WritebackEvent(txn_id=55, addr=0x1000, data=bytes(bad_data)))

    def test_orphan_writeback_detected(self):
        """Writeback with unknown txn_id should raise ScoreboardMismatch."""
        sb = OooScoreboard()

        with pytest.raises(ScoreboardMismatch, match="unexpected writeback"):
            sb.compare_writeback(WritebackEvent(txn_id=777, addr=0x0, data=b""))

        assert len(sb.orphan_writebacks) == 1

    def test_writeback_interleaved_with_responses(self):
        """Writebacks arriving interleaved with CPU responses should all match."""
        sb = OooScoreboard()
        wb1 = b"\x11" * 64
        wb2 = b"\x22" * 64

        txn1 = CacheTxn(CacheOp.WRITE, addr=0x040, size=4, data=0x11, mask=0xF, txn_id=1)
        resp1 = CacheResponse(
            txn_id=1, data=0, hit=False, evicted=True, evicted_dirty=True,
            writeback_addr=0x000, writeback_data=wb1,
        )
        txn2 = CacheTxn(CacheOp.WRITE, addr=0x0C0, size=4, data=0x22, mask=0xF, txn_id=2)
        resp2 = CacheResponse(
            txn_id=2, data=0, hit=False, evicted=True, evicted_dirty=True,
            writeback_addr=0x080, writeback_data=wb2,
        )
        sb.push_expected(txn1, resp1)
        sb.push_expected(txn2, resp2)

        sb.compare_actual(resp1)
        sb.compare_writeback(WritebackEvent(txn_id=1, addr=0x000, data=wb1))
        sb.compare_actual(resp2)
        sb.compare_writeback(WritebackEvent(txn_id=2, addr=0x080, data=wb2))

        assert sb.matched == 2
        assert sb.matched_writebacks == 2
        assert sb.is_empty
        assert sb.all_writebacks_matched

    def test_summary_includes_writeback_stats(self):
        """Summary dict should include writeback-related counters."""
        sb = OooScoreboard()
        s = sb.summary()
        assert "matched_writebacks" in s
        assert "mismatched_writebacks" in s
        assert "pending_writebacks" in s
        assert "orphan_writebacks" in s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
