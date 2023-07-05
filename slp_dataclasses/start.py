from dataclasses import dataclass
from typing import List

from .common import (ArrayData, F32Data, S8Data, S16Data, S32Data,
                     ShiftJISStringData, StringData, U8BitFlagData, U8Data,
                     U16Data, U32Data)


@dataclass
class Version:
    major: U8Data
    minor: U8Data
    build: U8Data
    unused: U8Data


@dataclass
class PlayerData:
    external_character_id: U8Data
    player_type: U8Data
    stock_start_count: U8Data
    costume_index: U8Data
    gib_pad_x64: ArrayData
    team_shade: U8Data
    handicap: U8Data
    team_id: U8Data
    gib_pad_x6A: ArrayData
    player_bitfield: U8BitFlagData
    gib_pad_x6D: ArrayData
    cpu_level: U8Data
    damage_start: U16Data
    damage_spawn: U16Data
    gib_pad_x74: ArrayData
    offense_ratio: F32Data
    defense_ratio: F32Data
    model_scale: F32Data


@dataclass
class GameInfoBlock:
    game_bitfield_1: U8BitFlagData
    game_bitfield_2: U8BitFlagData
    game_bitfield_3: U8BitFlagData
    game_bitfield_4: U8BitFlagData
    gib_pad_x04: ArrayData
    bomb_rain: U8Data
    gib_pad_x07: U8Data
    is_teams: U8Data
    gib_pad_x09: ArrayData
    item_spawn_behavior: S8Data
    self_destruct_score_value: S8Data
    gib_pad_x0D: U8Data
    stage: U16Data
    game_timer: U32Data
    gib_pad_x11: ArrayData
    item_spawn_bitfield_1: U8BitFlagData
    item_spawn_bitfield_2: U8BitFlagData
    item_spawn_bitfield_3: U8BitFlagData
    item_spawn_bitfield_4: U8BitFlagData
    item_spawn_bitfield_5: U8BitFlagData
    gib_pad_x28: ArrayData
    unk_float_x3C: F32Data
    damage_ratio: F32Data
    unk_float_x44: F32Data
    gib_pad_x34: ArrayData
    player_data: List[PlayerData]


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
    connect_code_hash: U16Data
    connect_code_num: StringData
    null_terminator: U8Data


@dataclass
class Start:
    command_byte: U8Data
    version: Version
    game_info_block: GameInfoBlock
    random_seed: U32Data
    start_fixes: List[StartFixes]
    nametags: List[ShiftJISStringData]
    pal: U8Data
    frozen_ps: U8Data
    minor_scene: U8Data
    major_scene: U8Data
    display_name: List[DisplayName]
    connect_code: List[ConnectCode]
    slippi_uid: List[StringData]
    language_option: U8Data
    match_id: StringData
    game_number: U32Data
    tiebreaker_number: U32Data
