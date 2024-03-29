import io
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

sys.path.append("..")

from slp_dataclasses.common import (
    ArrayData,
    BinPrimitive,
    F32Data,
    S8Data,
    S16Data,
    S32Data,
    ShiftJISStringData,
    StringData,
    U8BitFlagData,
    U8Data,
    U16Data,
    U32Data,
)


# test_tuples is a list of tuples of form (input_b_string, expected_value)
def read_test(dclass_instance: BinPrimitive, test_tuples: List[Tuple]):
    for input_b_string, expected_value in test_tuples:
        stream = io.BytesIO(input_b_string)

        # This is a little silly - idk best way to ensure the version is guaranteed
        dclass_instance.read(stream, "10000.0.0")

        assert dclass_instance.val == expected_value


# test_tuples is a list of tuples of form (input_value, expected_b_string)
def write_test(dclass_instance: BinPrimitive, test_tuples: List[Tuple]):
    for input_value, expected_b_string in test_tuples:
        stream = io.BytesIO()

        dclass_instance.val = input_value

        stream.seek(0)
        dclass_instance.write(stream, "10000.0.0")
        stream.seek(0)

        out = stream.read()
        assert out == expected_b_string


# Unsigned datatypes
def test_U8():
    u8 = U8Data(val=0)

    read_test_tuples = [(b"\xFF", 255), (b"\x12", 18)]

    read_test(u8, read_test_tuples)

    write_test_tuples = [(255, b"\xFF"), (18, b"\x12")]

    write_test(u8, write_test_tuples)


def test_U8_version():
    stream = io.BytesIO(b"\xFF")

    u8 = U8Data(val=0)

    u8.read(stream, "0.0.1")
    # No value should be read, incorrect version
    assert u8.val == 0

    u8.val = 200

    u8.write(stream, "0.0.1")

    out = stream.read()
    # No value should have been written
    assert int.from_bytes(out, "big") == 255


def test_U16():
    u16 = U16Data(val=0)

    read_test_tuples = [(b"\x00\xFF", 255), (b"\x00\x12", 18), (b"\xFF\xFF", 65535)]

    read_test(u16, read_test_tuples)

    write_test_tuples = [(255, b"\x00\xFF"), (18, b"\x00\x12"), (65535, b"\xFF\xFF")]

    write_test(u16, write_test_tuples)


def test_U16_version():
    stream = io.BytesIO(b"\xFF\xFF")

    u16 = U16Data(val=0)

    u16.read(stream, "0.0.1")
    assert u16.val == 0

    u16.val = 200

    stream.seek(0)
    u16.write(stream, "0.0.1")
    stream.seek(0)

    out = stream.read()
    assert int.from_bytes(out, "big") == 65535


def test_U32():
    u32 = U32Data(val=0)

    read_test_tuples = [
        (b"\x00\x00\x00\xFF", 255),
        (b"\x00\x00\x00\x12", 18),
        (b"\x00\x00\xFF\xFF", 65535),
        (b"\x00\x73\xFF\xFF", 7602175),
        (b"\xFE\x73\xFF\xFF", 4269015039),
    ]

    read_test(u32, read_test_tuples)

    write_test_tuples = [
        (255, b"\x00\x00\x00\xFF"),
        (18, b"\x00\x00\x00\x12"),
        (65535, b"\x00\x00\xFF\xFF"),
        (7602175, b"\x00\x73\xFF\xFF"),
        (4269015039, b"\xFE\x73\xFF\xFF"),
    ]

    write_test(u32, write_test_tuples)


def test_U32_version():
    stream = io.BytesIO(b"\xFF\xFF\xFF\xFF")

    u32 = U32Data(val=0)

    u32.read(stream, "0.0.1")
    assert u32.val == 0

    u32.val = 0

    stream.seek(0)
    u32.write(stream, "0.0.1")
    stream.seek(0)

    out = stream.read()
    assert int.from_bytes(out, "big") == 4294967295


# Signed datatypes
def test_S8():
    s8 = S8Data(val=0)

    read_test_tuples = [(b"\xFF", -1), (b"\xFE", -2), (b"\x78", 120)]

    read_test(s8, read_test_tuples)

    write_test_tuples = [(-1, b"\xFF"), (-2, b"\xFE"), (120, b"\x78")]

    write_test(s8, write_test_tuples)


def test_S8_version():
    stream = io.BytesIO(b"\xFF")

    s8 = S8Data(val=0)

    s8.read(stream, "0.0.1")
    # No value should be read, incorrect version
    assert s8.val == 0

    s8.val = 200

    s8.write(stream, "0.0.1")

    out = stream.read()
    # No value should have been written
    assert int.from_bytes(out, "big") == 255


def test_S16():
    s16 = S16Data(val=0)

    read_test_tuples = [
        (b"\x00\xFF", 255),
        (b"\x2F\x12", 12050),
        (b"\xFF\xFF", -1),
        (b"\xFF\xFE", -2),
    ]

    read_test(s16, read_test_tuples)

    write_test_tuples = [
        (255, b"\x00\xFF"),
        (12050, b"\x2F\x12"),
        (-1, b"\xFF\xFF"),
        (-2, b"\xFF\xFE"),
    ]

    write_test(s16, write_test_tuples)


def test_S16_version():
    stream = io.BytesIO(b"\xFF\xFF")

    u16 = S16Data(val=0)

    u16.read(stream, "0.0.1")
    assert u16.val == 0

    u16.val = 200

    stream.seek(0)
    u16.write(stream, "0.0.1")
    stream.seek(0)

    out = stream.read()
    assert int.from_bytes(out, "big") == 65535


def test_S32():
    s32 = S32Data(val=0)

    read_test_tuples = [
        (b"\x00\x00\x00\xFF", 255),
        (b"\x00\x00\x2F\x12", 12050),
        (b"\x00\x73\xFF\xFF", 7602175),
        (b"\x70\xFF\x41\xFF", 1895776767),
        (b"\xFF\xFF\xFF\xFF", -1),
        (b"\xFF\xFF\xFF\xFE", -2),
    ]

    read_test(s32, read_test_tuples)

    write_test_tuples = [
        (255, b"\x00\x00\x00\xFF"),
        (12050, b"\x00\x00\x2F\x12"),
        (7602175, b"\x00\x73\xFF\xFF"),
        (1895776767, b"\x70\xFF\x41\xFF"),
        (-1, b"\xFF\xFF\xFF\xFF"),
        (-2, b"\xFF\xFF\xFF\xFE"),
    ]

    write_test(s32, write_test_tuples)


def test_S32_version():
    stream = io.BytesIO(b"\xFF\xFF\xFF\xFF")

    u32 = S32Data(val=0)

    u32.read(stream, "0.0.1")
    assert u32.val == 0

    u32.val = 0

    stream.seek(0)
    u32.write(stream, "0.0.1")
    stream.seek(0)

    out = stream.read()
    assert int.from_bytes(out, "big") == 4294967295


def test_U8BitFlagData():
    # 10101010
    stream = io.BytesIO(b"\xAA")

    u8bflag = U8BitFlagData()

    u8bflag.read(stream, "10000.0.0")

    assert u8bflag.val == [True, False, True, False, True, False, True, False]

    u8bflag.val = [False, True, False, True, False, True, False, True]

    stream.seek(0)
    u8bflag.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    # 01010101
    assert int.from_bytes(out, "big") == 85


def test_ArrayData():
    stream = io.BytesIO(b"\xFF\xFF\xFF\xFF")
    ad = ArrayData(val=[0, 0, 0, 0], len=4)
    ad.read(stream, "10000.0.0")
    assert ad.val == [255, 255, 255, 255]

    ad.val = [255, 0, 255, 0]
    stream.seek(0)
    ad.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    # FF 00 FF 00
    assert int.from_bytes(out, "big") == 4278255360


# Test behaviour when the length of the array is mismatched from the len attribute
def test_ArrayData_mismatched():
    stream = io.BytesIO(b"\xFF\xFF\xFF\xFF")
    ad = ArrayData(val=[0, 0, 0, 0], len=2)
    ad.read(stream, "10000.0.0")
    assert ad.val == [255, 255]

    ad = ArrayData(val=[0, 0, 0, 0], len=6)
    ad.val = [255, 0, 255, 0]

    stream.seek(0)
    ad.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    # FF 00 FF 00 00 00
    assert int.from_bytes(out, "big") == 280379743272960

    ad = ArrayData(val=[], len=6)
    ad.val = []

    stream.seek(0)
    ad.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    # FF 00 FF 00 00 00
    assert int.from_bytes(out, "big") == 0


def test_StringData():
    # ABCD
    stream = io.BytesIO(b"\x41\x42\x43\x44")
    ad = StringData(val="hello", len=4)
    ad.read(stream, "10000.0.0")
    assert ad.val == "ABCD"

    ad = StringData(val="a", len=5)
    ad.val = "hello"
    stream.seek(0)
    ad.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    # h e l l o
    assert int.from_bytes(out, "big") == 448378203247

    stream = io.BytesIO(b"\x00")
    ad = StringData(val="a", len=5)
    ad.val = ""
    stream.seek(0)
    ad.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    assert out == b"\x00\x00\x00\x00\x00"


def test_ShiftJISStringData():
    stream = io.BytesIO(b"\xDE\xAD\xBE\xEF\xFF\xFF")
    sjis = ShiftJISStringData(val=[0, 0], len=3)
    sjis.read(stream, "10000.0.0")
    assert sjis.val == [57005, 48879, 65535]

    # 0xBAADF00D
    sjis.val = [47789, 61453]

    stream.seek(0)
    sjis.write(stream, "10000.0.0")
    stream.seek(0)

    out = stream.read()
    assert out == b"\xBA\xAD\xF0\x0D\x00\x00"


if __name__ == "__main__":
    test_ShiftJISStringData()
