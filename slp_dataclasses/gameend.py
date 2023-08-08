from dataclasses import dataclass
from typing import List

from .common import BinData, S8Data, U8Data


@dataclass
class GameEnd(BinData):
    command_byte: U8Data
    game_end_method: U8Data
    lras_initiator: S8Data
    player_placements: List[S8Data]
