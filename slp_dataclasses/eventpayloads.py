from dataclasses import dataclass
from .common import U8Data, U16Data, U32Data, S8Data, S16Data, S32Data, F32Data, StringData
from typing import List

@dataclass
class OtherEventPayloads:
    command_byte: U8Data
    payload_size: U16Data


@dataclass
class EventPayloads:
    command_byte: U8Data
    payload_size: U8Data
    other_cmds: List[OtherEventPayloads]
