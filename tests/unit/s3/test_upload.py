from pathlib import Path
from typing import List

import pytest

from deepset_cloud_sdk.s3.upload import S3, make_safe_file_name


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


@pytest.mark.asyncio
class TestValidateFilePaths:
    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/file1.txt"), Path("/home/user/file2.txt")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths(self, file_paths: List[Path]) -> None:
        await S3.validate_file_paths(file_paths)

    @pytest.mark.parametrize(
        "file_paths",
        [
            [Path("/home/user/file2.json")],
            [Path("/home/user/file1.md")],
            [Path("/home/user/file1.docx")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file2.pdf.meta.json")],
            [Path("/home/user/file1.pdf"), Path("/home/user/file1.txt.meta.json")],
            [Path("/home/user/file1.txt"), Path("/home/user/file1.pdf.meta.json")],
        ],
    )
    async def test_validate_file_paths_with_broken_meta_field(self, file_paths: List[Path]) -> None:
        with pytest.raises(ValueError):
            await S3.validate_file_paths(file_paths)
