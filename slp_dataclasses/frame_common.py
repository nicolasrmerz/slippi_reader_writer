from itertools import zip_longest
from typing import Union

from slp_dataclasses.preframeupdate import PreFrameUpdate
from slp_dataclasses.postframeupdate import PostFrameUpdate

# How to offset from the very first frame of the game to 0
# the lowest frame_number is -123
FRAME_OFFSET = 123


class FrameList:
    def __init__(self):
        self.flist: list[list[Union[PreFrameUpdate, PostFrameUpdate]]] = [
            [],
            [],
            [],
            [],
        ]

    def add_frame(self, f: Union[PreFrameUpdate, PostFrameUpdate]):
        p_index = f.player_index.val
        frame_num = f.frame_number.val + FRAME_OFFSET
        sub_list = self.flist[p_index]

        # TODO: I think this is how rollback works? If frame_number decreases, there's been a rollback
        if frame_num == len(sub_list):
            sub_list.append(f)
        else:
            sub_list[frame_num] = f

    def __len__(self):
        return max([len(x) for x in self.flist])

    # Iterate over frame numbers
    def __iter__(self):
        # for (f0, f1, f2, f3) in zip_longest(self.flist):
        for f in zip_longest(*self.flist):
            yield f
