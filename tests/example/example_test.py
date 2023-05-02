import src


class TestExample:
    def test_example(self, example_fixture: str) -> None:
        assert example_fixture == "example", "I am an example test, please remove me from your test suite"
