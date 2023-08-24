from dataclasses import dataclass

from .common import BinData, S32Data, U8Data, U32Data


@dataclass
class FrameStart(BinData):
    command_byte: U8Data
    frame_number: S32Data
    random_seed: U32Data
    scene_frame_counter: U32Data
