from datetime import datetime

import pytest

from deepset_cloud_sdk._utils.datetime import from_isoformat


class TestFromIsoformat:
    @pytest.mark.parametrize(
        "input",
        [
            "2024-02-03T08:10:10.335884Z",
            "2024-02-03T08:10:10.335884+00:00",
        ],
    )
    def test_fromisoformat(self, input: str) -> None:
        assert from_isoformat(input) == datetime(2024, 2, 3, 8, 10, 10, 335884)
