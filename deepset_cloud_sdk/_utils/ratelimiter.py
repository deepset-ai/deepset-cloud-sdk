import asyncio
import time
from typing import Any

import aiohttp
from aiohttp import ClientSession

# 500 requests per second, AWS limit is 3500 PUT/POST/DELETE requests a second
DEFAULT_RATE_LIMIT = 500


class RateLimiter:  # pylint: disable=too-few-public-methods
    """Rate limits an HTTP client for post() calls.

    Calls are rate-limited by host.
    This is a slightly modified version of the following code:
      - https://gist.github.com/pquentin/28628ad59145e339027cc1612195a961
    which is referenced in the following blog post:
      - https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
    This class is not thread-safe.
    """

    def __init__(self, client: ClientSession):
        """
        Create RateLimiter Object.

        :param client: Instance of an aiohttp.ClientSession.
        """
        self._client = client
        self._rate = DEFAULT_RATE_LIMIT
        self._max_tokens = 500
        self._tokens = 0
        self._updated_at = time.monotonic()

    async def post(self, *args: Any, **kwargs: Any) -> aiohttp.client._RequestContextManager:
        """
        Ensure there is an available token before making a request.

        :params *args: the arguments to be passed to the ClientSession
        :param **kwargs: the keyword arguments to pass to the ClientSession
        """
        await self._wait_for_token()
        return self._client.post(*args, **kwargs)

    async def _wait_for_token(self) -> None:
        """Wait until a token becomes available."""
        while self._tokens < 1:
            self._add_new_tokens()
            await asyncio.sleep(0.1)
        self._tokens -= 1

    def _add_new_tokens(self) -> None:
        """Add additional tokens based on the time passed and the defined rate."""
        now = time.monotonic()
        time_since_update = now - self._updated_at
        new_tokens = int(time_since_update * self._rate)

        if self._tokens + new_tokens >= 1:
            self._tokens = min(self._tokens + new_tokens, self._max_tokens)
            self._updated_at = now
