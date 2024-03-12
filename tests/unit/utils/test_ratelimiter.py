import time
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from freezegun import freeze_time

from deepset_cloud_sdk._utils.ratelimiter import RateLimiter

pytest_plugins = ("pytest_asyncio",)


# These tests need timeouts, if there is a bug in RateLimiter, it could result in the tests running forever
@pytest.mark.timeout(0.1)
class TestRateLimiter:
    @pytest.fixture
    def client_mock(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_ratelimiter_consumes_tokens(self, client_mock: AsyncMock) -> None:
        with freeze_time(datetime.now()) as _:
            ratelimiter = RateLimiter(client=client_mock)
            ratelimiter._updated_at = time.monotonic()
            ratelimiter._tokens = 0  # all tokens depleted
            ratelimiter._rate = 1  # 1 request per second limit
            ratelimiter._max_tokens = 10

            ratelimiter._tokens = 10

            for _ in range(10):
                await ratelimiter.post()

            assert ratelimiter._tokens == 0, f"0 tokens should be remaining, but got {ratelimiter._tokens}"

    @pytest.mark.asyncio
    @patch("asyncio.sleep", AsyncMock())
    async def test_ratelimiter_adds_tokens_upon_depletion(self, client_mock: AsyncMock) -> None:
        with freeze_time(datetime.now()) as frozen_datetime:
            ratelimiter = RateLimiter(client=client_mock)
            ratelimiter._updated_at = time.monotonic()
            ratelimiter._tokens = 0  # all tokens depleted
            ratelimiter._rate = 1  # 1 request per second limit
            ratelimiter._max_tokens = 10

            # fast forward 10 seconds
            frozen_datetime.tick(10.0)

            await ratelimiter.post()  #

            # 10 tokens added, 1 token immediately consumed
            assert ratelimiter._tokens == 9, f"9 tokens should be added, but got {ratelimiter._tokens}"

    @pytest.mark.asyncio
    @patch("asyncio.sleep", AsyncMock())
    async def test_ratelimiter_does_not_add_more_than_max_tokens(self, client_mock: AsyncMock) -> None:
        with freeze_time(datetime.now()) as frozen_datetime:
            ratelimiter = RateLimiter(client=client_mock)
            ratelimiter._updated_at = time.monotonic()
            ratelimiter._tokens = 0  # all tokens depleted
            ratelimiter._rate = 1  # 1 request per second limit
            ratelimiter._max_tokens = 10

            # fast forward 100 seconds
            frozen_datetime.tick(100.0)

            await ratelimiter.post()  #

            assert (
                ratelimiter._tokens == ratelimiter._max_tokens - 1
            ), f"{ratelimiter._max_tokens - 1} tokens should be added, but got {ratelimiter._tokens}"

    @pytest.mark.asyncio
    @patch("asyncio.sleep", AsyncMock())
    async def test_ratelimiter_client_post_method_is_called(self, client_mock: AsyncMock) -> None:
        with freeze_time(datetime.now()) as frozen_datetime:
            ratelimiter = RateLimiter(client=client_mock)
            ratelimiter._updated_at = time.monotonic()
            ratelimiter._tokens = 10
            ratelimiter._rate = 1  # 1 request per second limit
            ratelimiter._max_tokens = 10

            await ratelimiter.post(1, 2, 3, a="a", b="b")  #

            client_mock.post.assert_called_with(1, 2, 3, a="a", b="b")

    @pytest.mark.asyncio
    @patch("asyncio.sleep", AsyncMock())
    async def test_ratelimiter_1_request_per_second_edge_case(self, client_mock: AsyncMock) -> None:
        with freeze_time(datetime.now()) as frozen_datetime:
            ratelimiter = RateLimiter(client=client_mock)
            ratelimiter._updated_at = time.monotonic()
            ratelimiter._tokens = 1
            ratelimiter._rate = 1  # 1 request per second limit
            ratelimiter._max_tokens = 1

            await ratelimiter.post()
            assert client_mock.post.call_count == 1, "no available tokens, so post should not be called"

            frozen_datetime.tick(1)
            await ratelimiter.post()
            assert client_mock.post.call_count == 2, "no available tokens, so post should not be called"

            frozen_datetime.tick(1)
            await ratelimiter.post()
            assert client_mock.post.call_count == 3, "no available tokens, so post should not be called"

            frozen_datetime.tick(1)
            await ratelimiter.post()
            assert client_mock.post.call_count == 4, "no available tokens, so post should not be called"
