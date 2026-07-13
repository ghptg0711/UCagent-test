import pytest

from cache_vip.dut_regression import DUTRegressionRunner
from cache_vip.scoreboard import ScoreboardMismatch
from cache_vip.transactions import CacheOp, CacheResponse, CacheTxn


class FakeAdapter:
    def __init__(self, responses: list[CacheResponse]) -> None:
        self.responses = responses
        self.driven: list[CacheTxn] = []

    async def drive_cpu_request(self, txn: CacheTxn) -> None:
        self.driven.append(txn)

    async def sample_cpu_response(self) -> CacheResponse:
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_dut_runner_compares_independent_actual_data() -> None:
    txn = CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=1)
    runner = DUTRegressionRunner(FakeAdapter([CacheResponse(txn_id=1, data=1, hit=False)]))

    with pytest.raises(ScoreboardMismatch, match="read data mismatch"):
        await runner.execute(txn)


@pytest.mark.asyncio
async def test_dut_runner_does_not_invent_unobservable_hit_status() -> None:
    txn = CacheTxn(CacheOp.READ, addr=0x100, size=8, txn_id=1)
    actual = CacheResponse(
        txn_id=1,
        data=0,
        hit=None,
        observed_fields=frozenset({"txn_id", "data"}),
    )
    runner = DUTRegressionRunner(FakeAdapter([actual]))

    response = await runner.execute(txn)

    assert response.hit is None
    assert runner.scoreboard.coverage.bins == {}
    assert runner.coverage.bins["access.read_hit"] == 0
    assert runner.coverage.bins["access.read_miss"] == 0
