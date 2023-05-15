import pytest

from deepset_cloud_sdk.s3.upload import make_safe_file_name


class TestUploadsS3:
    class TestHelpers:
        @pytest.mark.parametrize(
            "input_file_name,expected_file_name",
            [
                ("hello.txt", "hello.txt"),
                # unprintable characters
                (
                    "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1A\x1B\x1C\x1D\x1E\x1F",
                    "_" * 32,
                ),
                # additional special characters
                ("""#%"'|<>{}`^[]~\\""", "_" * 15),
                ("$£%\x09宿 a.txt", "%24%C2%A3__%E5%AE%BF%20a.txt"),
            ],
        )
        def test_make_safe_file_name(self, input_file_name: str, expected_file_name: str) -> None:
            safe_name = make_safe_file_name(input_file_name)
            assert safe_name == expected_file_name
