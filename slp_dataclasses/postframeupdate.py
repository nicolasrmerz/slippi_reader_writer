from dataclasses import dataclass

from .common import BinData, F32Data, S32Data, U8BitFlagData, U8Data, U16Data, U32Data


@dataclass
class PostFrameUpdate(BinData):
    command_byte: U8Data
    frame_number: S32Data
    player_index: U8Data
    is_follower: U8Data
    internal_character_id: U8Data
    action_state_id: U16Data
    x_position: F32Data
    y_position: F32Data
    facing_direction: F32Data
    percent: F32Data
    shield_size: F32Data
    last_hitting_attack_id: U8Data
    current_combo_count: U8Data
    last_hit_by: U8Data
    stocks_remaining: U8Data
    action_state_frame_counter: F32Data
    state_bit_flags_1: U8BitFlagData
    state_bit_flags_2: U8BitFlagData
    state_bit_flags_3: U8BitFlagData
    state_bit_flags_4: U8BitFlagData
    state_bit_flags_5: U8BitFlagData
    misc_as: F32Data
    ground_air_state: U8Data
    last_ground_id: U16Data
    jumps_remaining: U8Data
    l_cancel_status: U8Data
    hurtbox_collision_state: U8Data
    self_induced_air_x_speed: F32Data
    self_induced_y_speed: F32Data
    attack_based_x_speed: F32Data
    attack_based_y_speed: F32Data
    self_induced_ground_x_speed: F32Data
    hitlag_frames_remaining: F32Data
    animation_index: U32Data

    def to_numpy(self):
        import numpy as np

        d = [self.action_state_frame_counter.val, self.hitlag_frames_remaining.val]
        return np.array(d).astype(np.float32)
