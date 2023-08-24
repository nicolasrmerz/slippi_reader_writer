from dataclasses import dataclass

from .common import BinData, S32Data, U8Data


@dataclass
class FrameBookend(BinData):
    command_byte: U8Data
    frame_number: S32Data
    last_finalized_frame: S32Data
