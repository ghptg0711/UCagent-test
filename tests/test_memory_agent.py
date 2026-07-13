from cache_vip.memory_agent import MemoryRequest, ScriptedMemoryAgent


def test_memory_agent_models_backpressure_latency_and_masked_write():
    agent = ScriptedMemoryAgent(default_latency=2, backpressure_pattern=[False, True])

    assert (
        agent.accept(
            MemoryRequest(addr=0x10, size=4, write=True, data=0xAABBCCDD, mask=0b0101, txn_id=1)
        )
        is False
    )
    assert agent.tick() == []
    assert (
        agent.accept(
            MemoryRequest(addr=0x10, size=4, write=True, data=0xAABBCCDD, mask=0b0101, txn_id=1)
        )
        is True
    )
    assert agent.accept(MemoryRequest(addr=0x10, size=4, txn_id=2), latency=1) is True

    assert agent.tick() == []
    assert agent.tick() == []
    responses = agent.tick()

    assert [response.txn_id for response in responses] == [1, 2]
    assert responses[1].data == 0x00BB00DD
