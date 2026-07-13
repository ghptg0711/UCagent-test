"""Smoke tests for Real NutShell Cache DUT integration.

These tests verify the basic functionality of the RealCacheAdapter
driving and sampling the Picker-generated DUT.

NOTE: These tests require the xspcomm library from Picker,
which is only available in WSL2/Linux environment.
"""

import asyncio

import pytest

from cache_vip.dut_regression import DUTRegressionRunner
from cache_vip.real_dut_adapter import create_real_dut_adapter
from cache_vip.real_dut_config import REAL_DUT_CACHE_PARAMS
from cache_vip.reference_model import ReferenceCache
from cache_vip.scoreboard import Scoreboard
from cache_vip.transactions import CacheOp, CacheTxn


def _xspcomm_available() -> bool:
    """Check whether the xspcomm runtime (Picker) is importable."""
    try:
        import xspcomm  # noqa: F401

        return True
    except Exception:
        return False


# Skip all tests in this module if xspcomm is not available
pytestmark = [
    pytest.mark.skipif(
        not _xspcomm_available(),
        reason="xspcomm (Picker runtime) not installed; run in WSL2 with Picker",
    ),
    pytest.mark.asyncio,
]


@pytest.fixture(scope="function")
async def setup_real_dut():
    """Fixture to set up real DUT and adapter before each test."""
    adapter = await create_real_dut_adapter()
    await adapter.reset()
    scoreboard = Scoreboard(ReferenceCache(REAL_DUT_CACHE_PARAMS))
    yield adapter, DUTRegressionRunner(adapter, scoreboard=scoreboard)
    adapter.finish()


async def test_real_dut_reset(setup_real_dut):
    """Test that reset properly initializes the DUT."""
    adapter, _runner = setup_real_dut
    await adapter.reset(cycles=10)
    assert await adapter.dut_wrapper.reset.read() == 0


async def test_real_dut_single_read_after_reset(setup_real_dut):
    """Test reading a single address after reset (should be a miss)."""
    _adapter, runner = setup_real_dut

    txn = CacheTxn(op=CacheOp.READ, addr=0x1000, size=8, txn_id=1)
    resp = await runner.execute(txn)

    assert resp.txn_id == txn.txn_id
    assert resp.data is not None


async def test_real_dut_write_then_read(setup_real_dut):
    """BUG-012 guard: a write miss must preserve CPU data after line fill."""
    _adapter, runner = setup_real_dut

    write_data = 0x1122334455667788
    write_txn = CacheTxn(op=CacheOp.WRITE, addr=0x2000, size=8, data=write_data, txn_id=1)
    await runner.execute(write_txn)

    read_txn = CacheTxn(op=CacheOp.READ, addr=0x2000, size=8, txn_id=2)
    resp = await runner.execute(read_txn)

    assert resp.txn_id == read_txn.txn_id
    assert resp.data == write_data


async def test_real_dut_read_miss_then_hit(setup_real_dut):
    """Test reading the same line twice (first miss, then hit)."""
    _adapter, runner = setup_real_dut

    addr = 0x3000

    first_read = CacheTxn(op=CacheOp.READ, addr=addr, size=8, txn_id=1)
    first_resp = await runner.execute(first_read)

    assert first_resp.txn_id == first_read.txn_id
    first_data = first_resp.data

    second_read = CacheTxn(op=CacheOp.READ, addr=addr, size=8, txn_id=2)
    second_resp = await runner.execute(second_read)

    assert second_resp.txn_id == second_read.txn_id
    assert second_resp.data == first_data


async def test_real_dut_partial_write_with_mask(setup_real_dut):
    """Test partial write with byte mask."""
    _adapter, runner = setup_real_dut

    base_addr = 0x4000
    write_txn = CacheTxn(
        op=CacheOp.WRITE, addr=base_addr, size=4, data=0xAABBCCDD, mask=0b1010, txn_id=1
    )
    await runner.execute(write_txn)

    read_txn = CacheTxn(op=CacheOp.READ, addr=base_addr, size=4, txn_id=2)
    resp = await runner.execute(read_txn)

    assert resp.txn_id == read_txn.txn_id
    assert resp.data == 0xAA00CC00


async def test_real_dut_multiple_transactions(setup_real_dut):
    """Test a sequence of multiple transactions."""
    _adapter, runner = setup_real_dut

    transactions = [
        CacheTxn(op=CacheOp.WRITE, addr=0x6000, size=4, data=0x12345678, mask=0xF, txn_id=1),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=4, txn_id=2),
        CacheTxn(op=CacheOp.WRITE, addr=0x6004, size=4, data=0xABCDEF01, mask=0xF, txn_id=3),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=8, txn_id=4),
    ]

    for txn in transactions:
        resp = await runner.execute(txn)
        assert resp.txn_id == txn.txn_id


async def test_bug010_real_dut_lru_victim(setup_real_dut):
    """BUG-010: a fifth same-set line must evict the least-recently-used tag."""
    _adapter, runner = setup_real_dut
    stride = REAL_DUT_CACHE_PARAMS.sets * REAL_DUT_CACHE_PARAMS.line_bytes

    async def scenario() -> None:
        for tag in range(4):
            await runner.execute(
                CacheTxn(
                    CacheOp.WRITE,
                    tag * stride,
                    8,
                    data=tag + 1,
                    mask=0xFF,
                    txn_id=100 + tag,
                )
            )
        for txn_id, tag in enumerate((0, 1, 0), start=200):
            response = await runner.execute(
                CacheTxn(CacheOp.READ, tag * stride, 8, txn_id=txn_id)
            )
            assert response.hit is True

        await runner.execute(CacheTxn(CacheOp.READ, 4 * stride, 8, txn_id=300))
        retained = await runner.execute(CacheTxn(CacheOp.READ, 3 * stride, 8, txn_id=301))
        victim = await runner.execute(CacheTxn(CacheOp.READ, 2 * stride, 8, txn_id=302))
        assert retained.hit is True
        assert victim.hit is False

    await asyncio.wait_for(scenario(), timeout=30)


async def test_bug011_real_dut_writeback_then_fill(setup_real_dut):
    """BUG-011: dirty eviction must complete writeback before filling the new line."""
    adapter, runner = setup_real_dut
    stride = REAL_DUT_CACHE_PARAMS.sets * REAL_DUT_CACHE_PARAMS.line_bytes

    async def scenario() -> None:
        for tag in range(4):
            await runner.execute(
                CacheTxn(
                    CacheOp.WRITE,
                    tag * stride,
                    8,
                    data=0x100 + tag,
                    mask=0xFF,
                    txn_id=400 + tag,
                )
            )

        event_start = len(adapter.bus_events)
        response = await runner.execute(CacheTxn(CacheOp.READ, 4 * stride, 8, txn_id=500))
        events = adapter.bus_events[event_start:]
        commands = [int(event["cmd"]) for event in events if event["bus"] == "mem"]
        assert any(command & 0x1 for command in commands), "dirty victim did not write back"
        assert any((command & 0x1) == 0 for command in commands), "new line fill request is missing"
        assert response.evicted_dirty is True

    await asyncio.wait_for(scenario(), timeout=30)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
