from typing import List
from dataclasses import dataclass
from .common import U8Data, U16Data, U32Data, S8Data, S16Data, S32Data, F32Data, StringData, ShiftJISStringData

@dataclass
class GameInfoBlock:
    x: int

@dataclass
class StartFixes:
    dashback_fix: U32Data
    shield_drop_fix: U32Data

@dataclass
class DisplayName:
    display_name: ShiftJISStringData
    null_terminator: U8Data

@dataclass
class ConnectCode:
    connect_code_str: StringData
    connect_code_num: U16Data
    null_terminator: U8Data

@dataclass
class Start:
    command_byte: U8Data
    version: List[U8Data]
    game_info_block: GameInfoBlock
    random_seed: U32Data
    start_fixes: List[StartFixes]
    nametags: ShiftJISStringData
    pal: U8Data
    frozen_ps: U8Data
    minor_scene: U8Data
    major_scene: U8Data
    display_name: List[DisplayName]
    connect_code: List[ConnectCode]
    slippi_uid: StringData
    language_option: U8Data
    match_id: StringData
    game_number: U32Data
    tiebreaker_number: U32Data

