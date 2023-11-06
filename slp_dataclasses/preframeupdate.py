from dataclasses import dataclass

from .common import (
    BinData,
    F32Data,
    S8Data,
    S32Data,
    U8Data,
    U16BitFlagData,
    U16Data,
    U32BitFlagData,
    U32Data,
)


@dataclass
class PreFrameUpdate(BinData):
    command_byte: U8Data
    frame_number: S32Data
    player_index: U8Data
    is_follower: U8Data
    random_seed: U32Data
    action_state_id: U16Data
    x_position: F32Data
    y_position: F32Data
    facing_direction: F32Data
    joystick_x: F32Data
    joystick_y: F32Data
    cstick_x: F32Data
    cstick_y: F32Data
    trigger: F32Data
    processed_buttons: U32BitFlagData
    physical_buttons: U16BitFlagData
    physical_l_trigger: F32Data
    physical_r_trigger: F32Data
    x_analog_for_ucf: S8Data
    percent: F32Data

    def to_numpy(self):
        import numpy as np

        d = [
            self.action_state_id.val,
            self.x_position.val,
            self.y_position.val,
            self.facing_direction.val,
            self.joystick_x.val,
            self.joystick_y.val,
            self.cstick_x.val,
            self.cstick_y.val,
            self.trigger.val,
            self.percent.val,
        ]
        return np.array(d).astype(np.float32)
