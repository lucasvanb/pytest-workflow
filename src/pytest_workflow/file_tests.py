"""All tests for workflow files"""
import hashlib
from pathlib import Path
from typing import Union

import pytest

from .schema import FileTest


class FileTestCollector(pytest.Collector):
    """This collector returns all tests for one particular file"""

    def __init__(self, parent: pytest.Collector, filetest: FileTest,
                 cwd: Union[bytes, str]):
        """
        Create a FiletestCollector
        :param parent: The collector that started this collector
        :param filetest: a FileTest object
        :param cwd: the working directory from which relative filepaths should
        be evaluated
        """
        name = filetest.path.__str__()
        super().__init__(name, parent)
        self.filetest = filetest
        self.cwd = Path(cwd)

    def collect(self):
        """Returns all tests for one file. Also the absolute path of the files
        is determined in this function."""
        filepath = self.filetest.path \
            if self.filetest.path.is_absolute() \
            else self.cwd / self.filetest.path

        # Below structure was chosen since it allows for adding tests when
        # certain conditions are met.
        tests = []

        tests.append(FileExists(self, filepath, self.filetest.should_exist))

        if self.filetest.md5sum:
            tests.append(FileMd5(self, filepath, self.filetest.md5sum))

        return tests


class FileExists(pytest.Item):
    """A pytest file exists test."""

    def __init__(self, parent: pytest.Collector, filepath: Path,
                 should_exist: bool):
        """
        :param parent: Collector that started this test
        :param filepath: A path to the file
        :param should_exist: Whether the file should exist
        """
        name = "should exist" if should_exist else "should not exist"
        super().__init__(name, parent)
        self.file = filepath
        self.should_exist = should_exist

    def runtest(self):
        assert self.file.exists() == self.should_exist


class FileMd5(pytest.Item):
    def __init__(self, parent: pytest.Collector, filepath: Path,
                 md5sum: str):
        """
        Create a tests for the file md5sum.
        :param parent: The collector that started this item
        :param filepath: The path to the file
        :param md5sum:  The expected md5sum
        """
        name = "md5sum"
        super().__init__(name, parent)
        self.filepath = filepath
        self.md5sum = md5sum

    def runtest(self):
        assert file_md5sum(self.filepath) == self.md5sum


def file_md5sum(filepath: Path):
    """
    Generates a md5sum for a file. Reads file in blocks to save memory.
    :param filepath: a pathlib. Path to the file
    :return: a md5sum as hexadecimal string.
    """

    hasher = hashlib.md5()
    with filepath.open('rb') as f:  # Read the file in bytes
        # Hardcode the blocksize at 8192 bytes here.
        # This can be changed or made variable when the requirements compel us
        # to do so.
        for block in iter(lambda: f.read(8192), b''):
            hasher.update(block)
    return hasher.hexdigest()
