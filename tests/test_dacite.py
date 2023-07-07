import sys

sys.path.append("..")
from dataclasses import dataclass
from typing import List

from dacite import from_dict

from slp_dataclasses.common import (
    ArrayData,
    BinData,
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


def test_dacite():
    @dataclass
    class TestDacite:
        str: StringData
        u16: U16Data
        u8: U8Data

    @dataclass
    class TestDacite2:
        u8: List[U8Data]

    data = {
        "str": {"val": "hello", "len": 5},
        "u16": {"val": 65535},
        "u8": {"val": 255},
    }

    td = from_dict(data_class=TestDacite, data=data)

    data = {
        "u8": [
            {"val": 255},
            {"val": 0},
            {"val": 255},
            {"val": 0},
        ]
    }

    td = from_dict(data_class=TestDacite2, data=data)


if __name__ == "__main__":
    test_dacite()
