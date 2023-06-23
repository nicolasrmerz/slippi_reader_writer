from typing import Union, List
from dataclasses import dataclass, field
from packaging import version
import struct

@dataclass(kw_only=True)
class BinData:
    val: Union[float, int, str]
    data_type: type = int
    format_char: str = '>B'
    offset: int = 0
    length: int = 0
    version: str = '0.1.0'

    def compare_version(self, given_ver):
        return version.parse(self.version) <= version.parse(given_ver)

    def _read(self, stream):
        size = struct.calcsize(self.format_char)
        buf = stream.read(size)
        b = struct.unpack(self.format_char, buf)[0]
        return b

    def read(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        #b = stream.read(struct.unpack(self.format_char))
        b = self._read(stream)
        self.val = self.data_type(b)

    def write(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        stream.write(struct.pack(self.format_char, self.val))

# These don't serve much purpose - they just make classes a little more annotated
@dataclass(kw_only=True)
class U8Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>B'

@dataclass(kw_only=True)
class U16Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>H'

@dataclass(kw_only=True)
class U32Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>L'

@dataclass(kw_only=True)
class S8Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>b'

@dataclass(kw_only=True)
class S16Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>h'

@dataclass(kw_only=True)
class S32Data(BinData):
    val: int
    data_type: type = int
    format_char: str = '>l'

@dataclass(kw_only=True)
class F32Data(BinData):
    val: float
    data_type: type = float
    format_char: str = '>f'

@dataclass(kw_only=True)
class U8BitFlagData(BinData):
    val: List[bool] = field(
        default_factory = lambda: [False]*8
    )
    format_char: str = '>B'

    def __post_init__(self):
        if len(self.val) != 8:
            raise ValueError("Length of bitfield in instantiated U8BitFlagData must be 8")

    def read(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        b = self._read(stream)
        binary = bin(int(str(b)))[2:]

        # Should not be possible since we're reading a >B format char, but sanity check
        if len(binary) != 8:
            raise ValueError("Length of read bitfield in U8BitFlagData must be 8")
        self.val = [False if c == '0' else True for c in binary]

    def write(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        b = int("".join([str(int(v)) for v in self.val]),2)
        stream.write(struct.pack(self.format_char, b))

@dataclass(kw_only=True)
class ArrayData(BinData):
    val: List[int]
    len: int
    format_char: str = '>B'

    def _read(self, stream):
        size = struct.calcsize(self.format_char) * self.len
        buf = stream.read(size)
        arr_fmt_str = ">" + str(self.len) + self.format_char.replace(">", "")
        b = list(struct.unpack(arr_fmt_str, buf))
        return b

    def read(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        self.val = self._read(stream)

    def _write(self, val):
        # Zero-pad or crop to the required length
        return bytearray(val[:self.len]) + b'\0'*(self.len-len(val))

    def write(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        b_array = self._write(self.val)
        stream.write(b_array)

@dataclass(kw_only=True)
class StringData(ArrayData):
    write_null: bool = False
    val: str

    def read(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        val_arr = self._read(stream)
        self.val = "".join([chr(c) for c in val_arr])

    def write(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        val_arr = [ord(c) for c in self.val]
        b_array = self._write(val_arr)
        if self.write_null:
            b_array[-1] = 0
        stream.write(b_array)

# TODO: Cause I'm lazy, I'm not doing ShiftJIS decoding - they are just streated as raw arrays of uint16s for now
@dataclass(kw_only=True)
class ShiftJISStringData(ArrayData):
    format_char: str = '>H'

    def _write(self, val):
        return b''.join([struct.pack(self.format_char, v) for v in val]) + b'\x00\x00'*(self.len-len(val))
