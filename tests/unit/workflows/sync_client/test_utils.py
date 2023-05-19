from asyncio import AbstractEventLoop
from typing import AsyncIterator

from deepset_cloud_sdk.workflows.sync_client.utils import iter_over_async


def test_iter_over_async(event_loop: AbstractEventLoop) -> None:
    async def async_generator() -> AsyncIterator[int]:
        yield 1
        yield 2
        yield 3

    sync_generator = iter_over_async(async_generator(), event_loop)
    assert list(sync_generator) == [1, 2, 3]
