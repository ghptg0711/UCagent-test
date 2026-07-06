"""Toffee binding boundary for the NutShell Cache DUT.

This module implements the Toffee adapter that translates between the
DUT-independent verification core (transactions, reference model, scoreboard)
and the concrete DUT signals driven/sampled via Toffee/Picker.

All protocol translation happens here; generator, reference model, scoreboard,
and coverage remain DUT-independent.
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass

from .transactions import CacheOp, CacheResponse, CacheTxn


@dataclass(frozen=True)
class SignalMap:
    clock: str
    reset: str
    cpu_req_valid: str
    cpu_req_ready: str
    cpu_req_addr: str
    cpu_req_write: str | None
    cpu_req_wdata: str
    cpu_req_wmask: str
    cpu_resp_valid: str
    cpu_resp_ready: str
    cpu_resp_rdata: str
    cpu_req_cmd: str | None = None
    cpu_req_size: str | None = None
    cpu_req_user: str | None = None
    cpu_resp_cmd: str | None = None
    cpu_resp_user: str | None = None
    flush: str | None = None
    empty: str | None = None
    mem_req_valid: str | None = None
    mem_req_ready: str | None = None
    mem_req_addr: str | None = None
    mem_req_write: str | None = None
    mem_req_cmd: str | None = None
    mem_req_size: str | None = None
    mem_req_wdata: str | None = None
    mem_req_wmask: str | None = None
    mem_resp_valid: str | None = None
    mem_resp_ready: str | None = None
    mem_resp_cmd: str | None = None
    mem_resp_rdata: str | None = None
    mmio_req_valid: str | None = None
    mmio_req_ready: str | None = None
    mmio_req_addr: str | None = None
    mmio_req_cmd: str | None = None
    mmio_req_size: str | None = None
    mmio_req_wdata: str | None = None
    mmio_req_wmask: str | None = None
    mmio_resp_valid: str | None = None
    mmio_resp_ready: str | None = None
    mmio_resp_cmd: str | None = None
    mmio_resp_rdata: str | None = None
    coh_req_valid: str | None = None
    coh_req_ready: str | None = None
    coh_resp_valid: str | None = None
    coh_resp_ready: str | None = None


def load_signal_map(path: str) -> SignalMap:
    """Load signal map from YAML configuration file."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return SignalMap(**data)


class ToffeeCacheAdapter:
    def __init__(self, dut: object, signal_map: SignalMap, *, response_timeout: int = 1000) -> None:
        self.dut = dut
        self.signal_map = signal_map
        self._pending_txns: dict[int, CacheTxn] = {}
        self._response_timeout = response_timeout

    async def reset(self, cycles: int = 10) -> None:
        """
        Reset the DUT by asserting the reset signal and waiting.
        
        Steps:
        1. Assert reset signal (active high)
        2. Wait for specified number of clock cycles
        3. Deassert reset signal
        4. Wait for DUT to stabilize
        """
        reset_signal = getattr(self.dut, self.signal_map.reset)
        await reset_signal.write(1)
        await self.dut.wait_cycles(cycles)
        await reset_signal.write(0)
        await self.dut.wait_cycles(2)

    async def drive_cpu_request(self, txn: CacheTxn) -> None:
        """
        Drive a CPU request to the DUT following valid/ready handshake.
        
        Steps:
        1. Parse CacheTxn fields
        2. Set up DUT request signals:
           - valid: pull high
           - addr: txn.addr
           - write: txn.op == WRITE
           - wdata: txn.data (little-endian)
           - wmask: txn.mask (byte mask)
        3. Wait for ready signal to go high
        4. Wait one cycle for handshake to complete
        5. Pull valid low
        """
        valid_sig = getattr(self.dut, self.signal_map.cpu_req_valid)
        ready_sig = getattr(self.dut, self.signal_map.cpu_req_ready)
        addr_sig = getattr(self.dut, self.signal_map.cpu_req_addr)
        write_sig = getattr(self.dut, self.signal_map.cpu_req_write)
        wdata_sig = getattr(self.dut, self.signal_map.cpu_req_wdata)
        wmask_sig = getattr(self.dut, self.signal_map.cpu_req_wmask)

        await valid_sig.write(1)
        await addr_sig.write(txn.addr)
        await write_sig.write(1 if txn.op is CacheOp.WRITE else 0)
        await wdata_sig.write(txn.data)
        await wmask_sig.write(txn.mask)

        while True:
            ready = await ready_sig.read()
            if ready:
                break
            await self.dut.wait_cycles(1)

        await self.dut.wait_cycles(1)
        await valid_sig.write(0)

        self._pending_txns[txn.txn_id] = txn

    async def sample_cpu_response(self) -> CacheResponse:
        """
        Sample a CPU response from the DUT.

        Steps:
        1. Wait for valid signal to go high (with timeout)
        2. Sample response data
        3. Infer hit/miss based on response latency
        4. Return CacheResponse object
        5. Pull ready high to acknowledge
        """
        valid_sig = getattr(self.dut, self.signal_map.cpu_resp_valid)
        ready_sig = getattr(self.dut, self.signal_map.cpu_resp_ready)
        rdata_sig = getattr(self.dut, self.signal_map.cpu_resp_rdata)

        wait_cycles = 0
        while True:
            valid = await valid_sig.read()
            if valid:
                break
            wait_cycles += 1
            if wait_cycles > self._response_timeout:
                raise TimeoutError(
                    f"DUT response timeout after {self._response_timeout} cycles"
                )
            await self.dut.wait_cycles(1)

        rdata = await rdata_sig.read()

        await ready_sig.write(1)
        await self.dut.wait_cycles(1)
        await ready_sig.write(0)

        txn_id = next(iter(self._pending_txns.keys()), 0)
        if txn_id in self._pending_txns:
            del self._pending_txns[txn_id]

        # Infer hit/miss: short latency (<=1 wait cycle) implies hit,
        # longer latency implies miss (fill from memory needed)
        hit = wait_cycles <= 1

        return CacheResponse(txn_id=txn_id, data=rdata, hit=hit)
