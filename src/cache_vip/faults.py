from __future__ import annotations

from dataclasses import replace

from .transactions import CacheResponse, CacheTxn


class FaultInjector:
    @staticmethod
    def flip_read_bit(response: CacheResponse, bit: int = 0) -> CacheResponse:
        return replace(response, data=response.data ^ (1 << bit))

    @staticmethod
    def drop_mask_bit(txn: CacheTxn, bit: int = 0) -> CacheTxn:
        if txn.mask is None or not txn.mask:
            return txn
        return replace(txn, mask=txn.mask & ~(1 << bit))

    @staticmethod
    def corrupt_writeback_byte(response: CacheResponse, byte_index: int = 0) -> CacheResponse:
        if response.writeback_data is None:
            return response
        data = bytearray(response.writeback_data)
        if not data:
            return response
        data[byte_index % len(data)] ^= 0x1
        return replace(response, writeback_data=bytes(data))

    @staticmethod
    def swap_order(responses: list[CacheResponse]) -> list[CacheResponse]:
        if len(responses) < 2:
            return responses
        swapped = list(responses)
        swapped[0], swapped[1] = swapped[1], swapped[0]
        return swapped

    @staticmethod
    def flip_tag_match(response: CacheResponse) -> CacheResponse:
        """Inject a tag comparator error: a hit becomes a miss (or vice versa).

        Models a hardware bug in the tag comparator where a valid match is
        incorrectly rejected, causing an unnecessary cache refill or stale data.
        """
        return replace(response, hit=not response.hit)
