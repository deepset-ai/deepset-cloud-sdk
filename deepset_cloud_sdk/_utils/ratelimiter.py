import asyncio
import time
from typing import Any

import aiohttp
from aiohttp import ClientSession


class RateLimiter:
    """Rate limits an HTTP client for post() calls.

    Calls are rate-limited by host.
    This is a slightly modified version of the following code:
      - https://gist.github.com/pquentin/28628ad59145e339027cc1612195a961
    which is referenced in the following blog post:
      - https://quentin.pradet.me/blog/how-do-you-rate-limit-calls-with-aiohttp.html
    This class is not thread-safe.
    """

    RATE = 500  # 500 requests per second, AWS limit is 3500 PUT/POST/DELETE requests a second
    MAX_TOKENS = 500

    def __init__(self, client: ClientSession):
        """
        Create RateLimiter Object.

        :param client: Instance of an aiohttp.ClientSession.
        """
        self.client = client
        self.tokens = RateLimiter.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def post(self, *args: Any, **kwargs: Any) -> aiohttp.client._RequestContextManager:
        """
        Ensure there is an avaialable token before making a request.

        :params *args: the arguments to be passed to the ClientSession
        :param **kwargs: the keyword arguments to pass to the ClientSession
        """
        await self.wait_for_token()
        return self.client.post(*args, **kwargs)

    async def wait_for_token(self) -> None:
        """Wait until a token becomes available."""

        while self.tokens < 1:
            self.add_new_tokens()
            await asyncio.sleep(0.1)
        self.tokens -= 1

    def add_new_tokens(self) -> None:
        """Add additional tokens based on the time passed and the defined rate."""

        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = int(time_since_update * self.RATE)

        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now
