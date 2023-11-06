import copy
import hashlib
import json
import os
import struct
from dataclasses import dataclass, fields
from itertools import zip_longest
from typing import Optional, Union
import numpy as np

from dacite import from_dict

from slp_dataclasses import (
    EventPayloads,
    FrameBookend,
    FrameStart,
    GameEnd,
    GameStart,
    ItemList,
    ItemUpdate,
    MessageSplitter,
    PostFrameUpdate,
    PreFrameUpdate,
    PrePostFrameList,
    StartBookendFrameList,
)
from slp_dataclasses.eventpayloads import generate_payload_size_dict
from slp_dataclasses.gecko import GeckoCode


class SlpBin:
    def __init__(self, config_dir):

        self.event_payloads: Optional[EventPayloads] = None
        self.payload_size_dict: dict = dict()
        self.version: str = ""
        self.pre_frames: PrePostFrameList = PrePostFrameList()
        self.item_updates: ItemList = ItemList()
        self.post_frames: PrePostFrameList = PrePostFrameList()
        self.frame_starts: StartBookendFrameList = StartBookendFrameList()
        self.frame_bookends: StartBookendFrameList = StartBookendFrameList()
        self.game_start: GameStart = self.init_dataclass(
            config_dir, "game_start_defaults.json", GameStart
        )
        self.gecko = self.init_gecko(config_dir)
        self.gecko_code = None
        self.gecko_cmd_byte = None
        self.pre_frame_update_template: PreFrameUpdate = self.init_dataclass(
            config_dir, "pre_frame_defaults.json", PreFrameUpdate
        )
        self.item_update_template: ItemUpdate = self.init_dataclass(
            config_dir, "item_update_defaults.json", ItemUpdate
        )
        self.post_frame_update_template: PostFrameUpdate = self.init_dataclass(
            config_dir, "post_frame_defaults.json", PostFrameUpdate
        )
        self.frame_start_template: FrameStart = self.init_dataclass(
            config_dir, "frame_start_defaults.json", FrameStart
        )

        self.frame_bookend_template: FrameBookend = self.init_dataclass(
            config_dir, "frame_bookend_defaults.json", FrameBookend
        )

        self.game_end: GameEnd = self.init_dataclass(
            config_dir, "game_end_defaults.json", GameEnd
        )

        self.CMD_BYTE_PARSER_MAP = {
            0x10: self.parse_gecko_split,
            0x36: self.parse_game_start,
            0x37: self.parse_pre_frame_update,
            0x38: self.parse_post_frame_update,
            0x3D: self.parse_gecko_code,
            0x39: self.parse_game_end,
            0x3A: self.parse_frame_start,
            0x3B: self.parse_item_update,
            0x3C: self.parse_frame_bookend,
        }

        self.metadata: Optional[bytes] = None
        self.pre_global_frame_number = (
            self.post_global_frame_number
        ) = (
            self.start_global_frame_number
        ) = self.item_global_frame_number = self.bookend_global_frame_number = -123

        self.original_ordered_payloads = list()
    def init_dataclass(self, config_dir, filename, class_type):
        with open(os.path.join(config_dir, filename), "r") as f:
            data = json.load(f)
        return from_dict(data_class=class_type, data=data)

    def init_gecko(self, config_dir):
        ms_template = self.init_dataclass(
            config_dir, "message_splitter_defaults.json", MessageSplitter
        )
        return GeckoCode(ms_template)

    def read_ubjson_header(self, stream):
        # 15 characters:
        # { U 3 r a w [ $ U # l X X X X
        # X X X X is total size of the binary
        ubjson_header = stream.read(15)
        bin_len = struct.unpack(">L", ubjson_header[-4:])[0]

        return bin_len

    def read(self, stream):
        self.total_bin_len = self.read_ubjson_header(stream)
        start_offset = stream.tell()
        self.event_payloads = EventPayloads.read(stream)
        self.payload_size_dict = generate_payload_size_dict(self.event_payloads)

        total_read = stream.tell()
        while total_read - start_offset < self.total_bin_len:
            cmd_byte = struct.unpack(">B", stream.read(1))[0]
            if cmd_byte in self.CMD_BYTE_PARSER_MAP:
                self.CMD_BYTE_PARSER_MAP[cmd_byte](cmd_byte, stream)
            elif cmd_byte in self.payload_size_dict:
                print(f"Warning: Unknown payload command byte found: {cmd_byte}")
                _ = stream.read(self.payload_size_dict[cmd_byte])
            else:
                raise NotImplementedError(
                    f"Command byte {cmd_byte} not defined in CMD_BYTE_PARSER_MAP nor in EventPayloads"
                )

            new_stream_loc = stream.tell()
            assert (
                new_stream_loc - total_read - 1 == self.payload_size_dict[cmd_byte]
            ), f"Read payload size differs from payload size defined in EventPayloads. Read = {new_stream_loc - total_read - 1}, Payload = {self.payload_size_dict[cmd_byte]}"
            total_read = new_stream_loc

        assert (
            total_read - start_offset == self.total_bin_len
        ), "Mismatch between actual read size and size listed in UBJSON header"

        # Read till end to get metadata
        self.metadata = stream.read()

    def parse_gecko_split(self, cmd_byte, stream):
        self.gecko.add_message(cmd_byte, stream, self.version)
        self.original_ordered_payloads.append(self.gecko.message_splitter_list[-1])

    @staticmethod
    def parse_version(stream):
        return struct.unpack(">BBBB", stream.read(4))

    def parse_game_start(self, cmd_byte, stream):
        self.game_start.command_byte.val = cmd_byte
        major, minor, build, unused = self.parse_version(stream)
        (
            self.game_start.version.major.val,
            self.game_start.version.minor.val,
            self.game_start.version.build.val,
            self.game_start.version.unused.val,
        ) = (major, minor, build, unused)
        self.version = f"{major}.{minor}.{build}"

        self.game_start.read(
            stream, self.version, ignore_fields=["command_byte", "version"]
        )

        self.original_ordered_payloads.append(self.game_start)

    def parse_game_end(self, cmd_byte, stream):
        self.game_end.command_byte.val = cmd_byte

        self.game_end.read(stream, self.version, ignore_fields=["command_byte"])

        self.original_ordered_payloads.append(self.game_end)

    def parse_gecko_code(self, cmd_byte, stream):
        self.gecko_cmd_byte = cmd_byte
        self.gecko_code = stream.read(self.payload_size_dict[cmd_byte])

        self.original_ordered_payloads.append(self.gecko_code)

    def write_gecko_code(self, stream):
        if self.gecko_code and self.gecko_cmd_byte:
            stream.write(struct.pack(">B", self.gecko_cmd_byte))
            stream.write(self.gecko_code)
        elif len(self.gecko):
            self.gecko.write_message_splitter_list(stream, self.version)

    def parse_pre_frame_update(self, cmd_byte, stream):
        pfu = copy.deepcopy(self.pre_frame_update_template)
        pfu.command_byte.val = cmd_byte

        pfu.read(stream, self.version, ignore_fields=["command_byte"])
        if pfu.frame_number.val < self.pre_global_frame_number:
            print(
                f"Pre rollback from {self.pre_global_frame_number} to {pfu.frame_number.val}"
            )
        self.pre_global_frame_number = pfu.frame_number.val
        self.pre_frames.add_frame(pfu)

        self.original_ordered_payloads.append(pfu)

    def parse_post_frame_update(self, cmd_byte, stream):
        pfu = copy.deepcopy(self.post_frame_update_template)
        pfu.command_byte.val = cmd_byte

        pfu.read(stream, self.version, ignore_fields=["command_byte"])
        if pfu.frame_number.val < self.post_global_frame_number:
            print(
                f"Post rollback from {self.post_global_frame_number} to {pfu.frame_number.val}"
            )
        self.post_global_frame_number = pfu.frame_number.val
        self.post_frames.add_frame(pfu)

        self.original_ordered_payloads.append(pfu)

    def parse_frame_start(self, cmd_byte, stream):
        fs = copy.deepcopy(self.frame_start_template)
        fs.command_byte.val = cmd_byte

        fs.read(stream, self.version, ignore_fields=["command_byte"])
        if fs.frame_number.val < self.start_global_frame_number:
            print(
                f"Start rollback from {self.start_global_frame_number} to {fs.frame_number.val}"
            )
        self.start_global_frame_number = fs.frame_number.val
        self.frame_starts.add_frame(fs)

        self.original_ordered_payloads.append(fs)

    def parse_item_update(self, cmd_byte, stream):
        iu = copy.deepcopy(self.item_update_template)
        iu.command_byte.val = cmd_byte

        iu.read(stream, self.version, ignore_fields=["command_byte"])
        if iu.frame_number.val < self.item_global_frame_number:
            print(
                f"Item rollback from {self.item_global_frame_number} to {iu.frame_number.val}"
            )
        self.item_global_frame_number = iu.frame_number.val
        self.item_updates.add_item(iu)

        self.original_ordered_payloads.append(iu)

    def parse_frame_bookend(self, cmd_byte, stream):
        fb = copy.deepcopy(self.frame_bookend_template)
        fb.command_byte.val = cmd_byte

        fb.read(stream, self.version, ignore_fields=["command_byte"])
        if fb.frame_number.val < self.bookend_global_frame_number:
            print(
                f"Bookend rollback from {self.bookend_global_frame_number} to {fb.frame_number.val}"
            )
        self.bookend_global_frame_number = fb.frame_number.val
        self.frame_bookends.add_frame(fb)

        self.original_ordered_payloads.append(fb)

    def write_ubjson_header(self, stream, size):
        stream.write(
            b"{U" + struct.pack(">B", 3) + b"raw[$U#l" + struct.pack(">I", size)
        )

    def write(self, stream):
        # if for whatever odd reason this stream does not start at 0
        location_0 = stream.tell()
        self.write_ubjson_header(stream, 0)
        start_offset = stream.tell()

        # Main payload writes
        self.event_payloads.write(stream, self.version)
        self.game_start.write(stream, self.version)
        self.write_gecko_code(stream)

        for start, pres, item_update, posts, bookend in zip_longest(
            self.frame_starts,
            self.pre_frames,
            self.item_updates,
            self.post_frames,
            self.frame_bookends,
        ):
            if start:
                start.write(stream, self.version)
            if pres:
                for pre in pres:
                    if pre:
                        pre.write(stream, self.version)
            if item_update:
                for item in item_update:
                    item.write(stream, self.version)
            if posts:
                for post in posts:
                    if post:
                        post.write(stream, self.version)
            if bookend:
                bookend.write(stream, self.version)

        self.game_end.write(stream, self.version)

        total_written = stream.tell() - start_offset

        stream.write(self.metadata)

        stream.seek(location_0)
        self.write_ubjson_header(stream, total_written)

    def to_numpy(self, file_path):
        d = list()
        for _, pres, _, posts, _ in zip_longest(
            self.frame_starts,
            self.pre_frames,
            self.item_updates,
            self.post_frames,
            self.frame_bookends,
        ):
            pres_np = []
            posts_np = []
            if pres:
                for pre in pres:
                    if pre:
                        pres_np.append(pre.to_numpy())
            if posts:
                for post in posts:
                    if post:
                        posts_np.append(post.to_numpy())

            frame_data = []
            for pre_zip, post_zip in zip(pres_np, posts_np):
                frame_data.append(np.concatenate([pre_zip, post_zip]))
            frame_data = np.concatenate(frame_data)
            d.append(frame_data)

        return np.array(d)


    def dump_original_ordered_payload_names(self, file_path):
        with open(file_path, "w") as f:
            for p in self.original_ordered_payloads:
                s = type(p).__name__
                if hasattr(p, "frame_number"):
                    # f.write(type(p).__name__ + ", " + str(p.frame_number.val) + "\n")
                    s = s + ", " + str(p.frame_number.val)
                s = s + ", " + str(hash_obj(p))
                f.write(s + "\n")


def hash_obj(obj):
    s = "".join(
        [
            str(getattr(obj, field.name).val)
            for field in fields(obj)
            if hasattr(getattr(obj, field.name), "val")
        ]
    )
    m = hashlib.sha256()
    m.update(s.encode())

    return str(m.hexdigest())[:8]
    # for f in obj.fields:


if __name__ == "__main__":
    slp_bin = SlpBin("configs")

    with open("samples/netplay.slp", "rb") as f:
        # with open("samples/offline_2.slp", "rb") as f:
        slp_bin.read(f)

    np_data = slp_bin.to_numpy(None)

    # with open("samples/test_out.slp", "wb") as f:
    #     slp_bin.write(f)
