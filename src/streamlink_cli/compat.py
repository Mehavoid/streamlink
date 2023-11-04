import sys
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO


stdout: BinaryIO = sys.stdout.buffer


_BasePath = Path if TYPE_CHECKING else type(Path())
class DeprecatedPath(_BasePath):
    pass


__all__ = [
    "stdout",
    "DeprecatedPath",
]
