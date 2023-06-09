"""Utils for making async code sync."""
from asyncio import AbstractEventLoop
from typing import AsyncIterator, Generator, Optional, Tuple, TypeVar

T = TypeVar("T")


def iter_over_async(ait: AsyncIterator[T], loop: AbstractEventLoop) -> Generator[T, None, None]:
    """Convert an async generator to a sync generator.

    :param ait: Async generator to convert.
    :param loop: Event loop to run the async generator on.
    :return: Sync generator.
    """
    # Taken from
    # https://stackoverflow.com/questions/63587660/yielding-asyncio-generator-data-back-from-event-loop-possible/63595496#63595496
    ait = ait.__aiter__()  # pylint: disable=unnecessary-dunder-call

    async def get_next() -> Tuple[bool, Optional[T]]:
        try:
            obj = await ait.__anext__()  # pylint: disable=unnecessary-dunder-call
            return False, obj
        except StopAsyncIteration:
            return True, None

    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        # object will always be not `None`
        yield obj  # type: ignore
