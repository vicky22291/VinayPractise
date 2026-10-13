"""Whole-file and tile-level I/O for the binary matrix format."""

import os
from typing import BinaryIO

from .header import HEADER_SIZE, Header


def write_matrix(path: str, header: Header, data: bytes) -> None:
    check_data_size(header, len(data))
    with open(path, "wb") as f:
        f.write(header.pack())
        f.write(data)


def read_matrix(path: str) -> tuple[Header, bytes]:
    """Load a whole matrix into RAM. Only for files that fit."""
    with open(path, "rb") as f:
        header = Header.read(f)
        data = f.read(header.data_size + 1)  # +1 to detect trailing bytes
    check_data_size(header, len(data))
    return header, data


def read_checked_header(f: BinaryIO) -> Header:
    """Read the header and check it against the real file size, without loading data."""
    header = Header.read(f)
    check_data_size(header, os.fstat(f.fileno()).st_size - HEADER_SIZE)
    return header


def check_data_size(header: Header, actual: int) -> None:
    if actual != header.data_size:
        raise ValueError(
            f"header says {header.rows}x{header.cols}x{header.elem_size} = "
            f"{header.data_size} data bytes, file has {actual}"
        )


# Tile I/O. Open files with buffering=0: a buffered reader pulls a full buffer
# (128 KiB on Python 3.14) on every seek, so a 4 KiB run would read 32x the bytes.

def read_tile(f: BinaryIO, header: Header, r0: int, c0: int, h: int, w: int) -> bytearray:
    """Read the h x w block at (r0, c0): h seeks, each one contiguous run of w elements."""
    run = w * header.elem_size
    block = bytearray(h * run)
    view = memoryview(block)  # readinto a slice of the view: no extra copy per run
    for k in range(h):
        f.seek(header.offset(r0 + k, c0))
        if f.readinto(view[k * run:(k + 1) * run]) != run:
            raise IOError(f"short read at row {r0 + k}")
    return block


def write_tile(f: BinaryIO, header: Header, r0: int, c0: int, h: int, w: int, block: bytes) -> None:
    """Write an h x w block at (r0, c0): h seeks, each one contiguous run of w elements."""
    run = w * header.elem_size
    view = memoryview(block)
    for k in range(h):
        f.seek(header.offset(r0 + k, c0))
        if f.write(view[k * run:(k + 1) * run]) != run:
            raise IOError(f"short write at row {r0 + k}")


def create_output(path: str, header: Header) -> BinaryIO:
    """Open an unbuffered output file with the header written and the full size reserved."""
    f = open(path, "wb", buffering=0)
    f.write(header.pack())
    f.truncate(f.tell() + header.data_size)
    return f
