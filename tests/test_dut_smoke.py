"""Smoke tests for NutShell Cache DUT integration with Toffee adapter.

These tests verify the basic functionality of the ToffeeCacheAdapter
driving and sampling a real (or mock) DUT. The tests cover:
- Reset sequence
- Basic read after reset
- Write followed by read (write hit)
- Multiple reads to same line (miss then hit)
- Partial write with byte mask
"""

import asyncio
import pytest

pytest_plugins = ('pytest_asyncio',)

pytestmark = pytest.mark.asyncio

from cache_vip.toffee_adapter import ToffeeCacheAdapter, load_signal_map
from cache_vip.transactions import CacheOp, CacheTxn, CacheResponse
from cache_vip.scoreboard import Scoreboard
from cache_vip.reference_model import ReferenceCache


@pytest.fixture(scope="function")
async def setup_dut():
    """Fixture to set up mock DUT and adapter before each test."""
    from tests.mock_dut import create_mock_dut
    
    dut = await create_mock_dut()
    signal_map = load_signal_map("configs/signal_map.yaml")
    adapter = ToffeeCacheAdapter(dut, signal_map)
    
    await adapter.reset()
    
    return dut, adapter


async def test_reset_sequence(setup_dut):
    """Test that reset properly initializes the DUT."""
    dut, adapter = setup_dut
    
    await adapter.reset(cycles=10)
    
    reset_val = await dut.signals["reset"].read()
    assert reset_val == 0, "Reset should be deasserted after reset sequence"


async def test_single_read_after_reset(setup_dut):
    """Test reading a single address after reset (should be a miss)."""
    dut, adapter = setup_dut
    
    txn = CacheTxn(op=CacheOp.READ, addr=0x1000, size=8, txn_id=1)
    await adapter.drive_cpu_request(txn)
    resp = await adapter.sample_cpu_response()
    
    assert resp.txn_id == txn.txn_id, f"txn_id mismatch: expected {txn.txn_id}, got {resp.txn_id}"
    assert resp.data is not None, "Response data should not be None"


async def test_write_then_read(setup_dut):
    """Test writing to an address and then reading it back (write hit)."""
    dut, adapter = setup_dut
    
    write_data = 0x1122334455667788
    write_txn = CacheTxn(op=CacheOp.WRITE, addr=0x2000, size=8, data=write_data, txn_id=1)
    await adapter.drive_cpu_request(write_txn)
    await adapter.sample_cpu_response()
    
    read_txn = CacheTxn(op=CacheOp.READ, addr=0x2000, size=8, txn_id=2)
    await adapter.drive_cpu_request(read_txn)
    resp = await adapter.sample_cpu_response()
    
    assert resp.txn_id == read_txn.txn_id, f"txn_id mismatch: expected {read_txn.txn_id}, got {resp.txn_id}"
    assert resp.data == write_data, f"Read data mismatch: expected 0x{write_data:x}, got 0x{resp.data:x}"


async def test_read_miss_then_hit(setup_dut):
    """Test reading the same line twice (first miss, then hit)."""
    dut, adapter = setup_dut
    
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
    assert second_resp.data == first_data, "Second read should return same data as first (cache hit)"


async def test_partial_write_with_mask(setup_dut):
    """Test partial write with byte mask, then read back and verify data."""
    dut, adapter = setup_dut

    base_addr = 0x4000
    write_txn = CacheTxn(op=CacheOp.WRITE, addr=base_addr, size=4, data=0xAABBCCDD, mask=0b1010, txn_id=1)
    await adapter.drive_cpu_request(write_txn)
    await adapter.sample_cpu_response()

    read_txn = CacheTxn(op=CacheOp.READ, addr=base_addr, size=4, txn_id=2)
    await adapter.drive_cpu_request(read_txn)
    resp = await adapter.sample_cpu_response()

    assert resp.txn_id == read_txn.txn_id
    # Data 0xAABBCCDD in little-endian bytes: [0xDD, 0xCC, 0xBB, 0xAA]
    # Mask 0b1010 writes byte 1 (0xCC) and byte 3 (0xAA)
    # Expected: 0xAA00CC00
    expected_data = 0xAA00CC00
    assert resp.data == expected_data, f"Partial write data mismatch: expected 0x{expected_data:x}, got 0x{resp.data:x}"


async def test_scoreboard_integration(setup_dut):
    """Test full integration with scoreboard comparing DUT against reference model."""
    dut, adapter = setup_dut
    scoreboard = Scoreboard()
    
    write_txn = CacheTxn(op=CacheOp.WRITE, addr=0x5000, size=8, data=0xDEADBEEFCAFEBABE, mask=0xFF, txn_id=1)
    scoreboard.push_request(write_txn)
    await adapter.drive_cpu_request(write_txn)
    resp = await adapter.sample_cpu_response()
    
    read_txn = CacheTxn(op=CacheOp.READ, addr=0x5000, size=8, txn_id=2)
    expected_resp = scoreboard.push_request(read_txn)
    await adapter.drive_cpu_request(read_txn)
    actual_resp = await adapter.sample_cpu_response()
    
    assert actual_resp.data == expected_resp.data, f"Data mismatch: expected 0x{expected_resp.data:x}, got 0x{actual_resp.data:x}"


async def test_multiple_transactions(setup_dut):
    """Test a sequence of multiple transactions with data verification."""
    dut, adapter = setup_dut

    transactions = [
        CacheTxn(op=CacheOp.WRITE, addr=0x6000, size=4, data=0x12345678, mask=0xF, txn_id=1),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=4, txn_id=2),
        CacheTxn(op=CacheOp.WRITE, addr=0x6004, size=4, data=0xABCDEF01, mask=0xF, txn_id=3),
        CacheTxn(op=CacheOp.READ, addr=0x6000, size=8, txn_id=4),
    ]

    responses = []
    for txn in transactions:
        await adapter.drive_cpu_request(txn)
        resp = await adapter.sample_cpu_response()
        assert resp.txn_id == txn.txn_id, f"txn_id mismatch for txn {txn.txn_id}"
        responses.append(resp)

    # Verify read data for transaction 2: should be 0x12345678
    assert responses[1].data == 0x12345678, \
        f"Read data mismatch txn 2: expected 0x12345678, got 0x{responses[1].data:x}"

    # Verify read data for transaction 4: should be 0xABCDEF01_12345678 (little-endian)
    expected_8byte = 0xABCDEF0112345678
    assert responses[3].data == expected_8byte, \
        f"Read data mismatch txn 4: expected 0x{expected_8byte:x}, got 0x{responses[3].data:x}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])