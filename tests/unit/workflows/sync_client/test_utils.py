import asyncio
from typing import AsyncIterator

from deepset_cloud_sdk.workflows.sync_client.utils import iter_over_async


def test_iter_over_async() -> None:
    loop = asyncio.new_event_loop()
    try:

        async def async_generator() -> AsyncIterator[int]:
            yield 1
            yield 2
            yield 3

        sync_generator = iter_over_async(async_generator(), loop)
        assert list(sync_generator) == [1, 2, 3]
    finally:
        loop.close()
