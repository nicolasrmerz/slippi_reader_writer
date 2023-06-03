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

    def read(self, stream, given_version):
        if not self.compare_version(given_version):
            return
        #b = stream.read(struct.unpack(self.format_char))
        size = struct.calcsize(self.format_char)
        buf = stream.read(size)
        b = struct.unpack(self.format_char, buf)[0]
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
    # val: List = field(default_factory=list)
    val: List[bool] = field(
        default_factory = lambda: [False]*8
    )
    format_char: str = '>B'

    def __post_init__(self):
        if len(self.val) != 8:
            raise ValueError("Length of bitfield in instantiated U8BitFlagData must be 8")

    def write(self, stream):
        if not self.compare_version(given_version):
            return
        b = int("".join([str(int(v)) for v in self.val]),2)
        stream.write(struct.pack(self.format_char, b))

# TODO: Maybe implement this? Will probably have same problems as strings (in terms of it being ugly to define in JSON as an array)
@dataclass(kw_only=True)
class ShiftJISStringData(BinData):
    val: str
    format_char: str = '>B'

    def write(stream):
        raise NotImplementedError("Need to implement a write method for Shift JIS strings")

@dataclass(kw_only=True)
class StringData(BinData):
    write_null: bool = False
    val: str
    max_len: int

    def write(stream):
        if not self.compare_version(given_version):
            return
        str_bytes = bytearray(self.val[:self.max_len], 'ascii') + b'\0'*(self.max_len-len(self.val))
        # Ensure null-terminated
        if self.write_null:
            str_bytes[-1] = 0
        stream.write(str_bytes)

