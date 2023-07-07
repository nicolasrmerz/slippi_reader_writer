from dataclasses import dataclass
from typing import List

from .common import (
    F32Data,
    S8Data,
    S16Data,
    S32Data,
    StringData,
    U8Data,
    U16Data,
    U32Data,
)


@dataclass
class OtherEventPayloads:
    command_byte: U8Data
    payload_size: U16Data


@dataclass
class EventPayloads:
    command_byte: U8Data
    payload_size: U8Data
    other_cmds: List[OtherEventPayloads]
