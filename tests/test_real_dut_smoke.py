"""Smoke tests for Real NutShell Cache DUT integration.

These tests verify the basic functionality of the RealCacheAdapter
driving and sampling the Picker-generated DUT.

NOTE: These tests require the xspcomm library from Picker,
which is only available in WSL2/Linux environment.
"""

import pytest

from cache_vip.real_dut_adapter import create_real_dut_adapter
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
    yield adapter
    adapter.finish()


async def test_real_dut_reset(setup_real_dut):
    """Test that reset properly initializes the DUT."""
    adapter = setup_real_dut
    await adapter.reset(cycles=10)


async def test_real_dut_single_read_after_reset(setup_real_dut):
    """Test reading a single address after reset (should be a miss)."""
    adapter = setup_real_dut

    txn = CacheTxn(op=CacheOp.READ, addr=0x1000, size=8, txn_id=1)
    await adapter.drive_cpu_request(txn)
    resp = await adapter.sample_cpu_response()

    assert resp.txn_id == txn.txn_id
    assert resp.data is not None


async def test_real_dut_write_then_read(setup_real_dut):
    """Test writing to an address and then reading it back (write hit)."""
    adapter = setup_real_dut

    write_data = 0x1122334455667788
    write_txn = CacheTxn(op=CacheOp.WRITE, addr=0x2000, size=8, data=write_data, txn_id=1)
    await adapter.drive_cpu_request(write_txn)
    await adapter.sample_cpu_response()

    read_txn = CacheTxn(op=CacheOp.READ, addr=0x2000, size=8, txn_id=2)
    await adapter.drive_cpu_request(read_txn)
    resp = await adapter.sample_cpu_response()

    assert resp.txn_id == read_txn.txn_id
    assert resp.data == write_data


async def test_real_dut_read_miss_then_hit(setup_real_dut):
    """Test reading the same line twice (first miss, then hit)."""
    adapter = setup_real_dut

    addr = 0x3000

    first_read = CacheTxn(op=CacheOp.READ, addr=addr, size=8, txn_id=1)
    await adapter.drive_cpu_request(first_read)
    first_resp = await adapter.sample_cpu_response()

    assert first_resp.txn_id == first_read.txn_id
    first_data = first_resp.data

    second_read = CacheTxn(op=CacheOp.READ, addr=addr, size=8, txn_id=2)
    await adapter.drive_cpu_request(second_read)
    second_resp = await adapter.sample_cpu_response()

    assert second_resp.txn_id == second_read.txn_id
    assert second_resp.data == first_data


async def test_real_dut_partial_write_with_mask(setup_real_dut):
    """Test partial write with byte mask."""
    adapter = setup_real_dut

    base_addr = 0x4000
    write_txn = CacheTxn(
        op=CacheOp.WRITE, addr=base_addr, size=4, data=0xAABBCCDD, mask=0b1010, txn_id=1
    )
    await adapter.drive_cpu_request(write_txn)
    await adapter.sample_cpu_response()

    read_txn = CacheTxn(op=CacheOp.READ, addr=base_addr, size=4, txn_id=2)
    await adapter.drive_cpu_request(read_txn)
    resp = await adapter.sample_cpu_response()

    assert resp.txn_id == read_txn.txn_id


async def test_real_dut_multiple_transactions(setup_real_dut):
    """Test a sequence of multiple transactions."""
    adapter = setup_real_dut

    transactions = [
        CacheTxn(op=CacheOp.WRITE, addr=0x6000, size=4, data=0x12345678, mask=0xF, txn_id=1),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=4, txn_id=2),
        CacheTxn(op=CacheOp.WRITE, addr=0x6004, size=4, data=0xABCDEF01, mask=0xF, txn_id=3),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=8, txn_id=4),
    ]

    for txn in transactions:
        await adapter.drive_cpu_request(txn)
        resp = await adapter.sample_cpu_response()
        assert resp.txn_id == txn.txn_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
