from dataclasses import dataclass
from typing import List, Union

from .common import BinData, F32Data, S8Data, S16Data, S32Data, U8Data, U16Data, U32Data


@dataclass
class ItemUpdate(BinData):
    command_byte: U8Data
    frame_number: S32Data
    type_id: S16Data
    state: U8Data
    facing_direction: F32Data
    x_velocity: F32Data
    y_velocity: F32Data
    x_position: F32Data
    y_position: F32Data
    damage_taken: U16Data
    expiration_timer: F32Data
    spawn_id: U32Data
    misc_1: U8Data
    misc_2: U8Data
    misc_3: U8Data
    misc_4: U8Data
    owner: S8Data


# How to offset from the very first frame of the game to 0
# the lowest frame_number is -123
FRAME_OFFSET = 123


class ItemList:
    def __init__(self):
        self.ilist: list[list[ItemUpdate]] = [[]]
        self.counter = 0

    def add_item(self, i: ItemUpdate):
        frame_num = i.frame_number.val + FRAME_OFFSET
        if frame_num > self.counter:
            for _ in range(frame_num - self.counter):
                self.ilist.append([])
            self.counter = frame_num
        # TODO: I think this is how rollback works? If frame_number decreases, there's been a rollback
        elif frame_num < self.counter:
            self.ilist = self.ilist[:frame_num]
            self.ilist.append([])
            self.counter = frame_num

        self.ilist[self.counter].append(i)

    def __len__(self):
        return self.counter

    # Iterate over frame numbers
    def __iter__(self):
        # for (f0, f1, f2, f3) in zip_longest(self.flist):
        for items in self.ilist:
            yield items
