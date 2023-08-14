import copy
import json
import os
import struct
from itertools import zip_longest
from typing import Optional, Union

from dacite import from_dict

from slp_dataclasses import (
    EventPayloads,
    FrameList,
    GameEnd,
    GameStart,
    MessageSplitter,
    PostFrameUpdate,
    PreFrameUpdate,
)
from slp_dataclasses.eventpayloads import generate_payload_size_dict
from slp_dataclasses.gecko import GeckoCode


class SlpBin:
    def __init__(self, config_dir):
        self.event_payloads: Optional[EventPayloads] = None
        self.payload_size_dict: dict = dict()
        self.version: str = ""
        self.pre_frames: FrameList = FrameList()
        self.post_frames: FrameList = FrameList()
        self.game_start: GameStart = self.init_dataclass(
            config_dir, "game_start_defaults.json", GameStart
        )
        self.gecko = self.init_gecko(config_dir)
        self.pre_frame_update_template: PreFrameUpdate = self.init_dataclass(
            config_dir, "pre_frame_defaults.json", PreFrameUpdate
        )
        self.post_frame_update_template: PostFrameUpdate = self.init_dataclass(
            config_dir, "post_frame_defaults.json", PostFrameUpdate
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
        }

        self.metadata: Optional[bytes] = None

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
            ), "Read payload size differs from payload size defined in EventPayloads"
            total_read = new_stream_loc

        assert (
            total_read - start_offset == self.total_bin_len
        ), "Mismatch between actual read size and size listed in UBJSON header"

        # Read till end to get metadata
        self.metadata = stream.read()

    def parse_gecko_split(self, cmd_byte, stream):
        self.gecko.add_message(cmd_byte, stream, self.version)

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

    def parse_game_end(self, cmd_byte, stream):
        self.game_end.command_byte.val = cmd_byte

        self.game_end.read(stream, self.version, ignore_fields=["command_byte"])

    def parse_gecko_code(self, cmd_byte, stream):
        self.gecko_cmd_byte = cmd_byte
        self.gecko_code = stream.read(self.payload_size_dict[cmd_byte])

    def write_gecko_code(self, stream):
        if self.gecko_code:
            stream.write(struct.pack(">B", self.gecko_cmd_byte))
            stream.write(self.gecko_code)

    def parse_pre_frame_update(self, cmd_byte, stream):
        pfu = copy.deepcopy(self.pre_frame_update_template)
        pfu.command_byte.val = cmd_byte

        pfu.read(stream, self.version, ignore_fields=["command_byte"])
        self.pre_frames.add_frame(pfu)

    def parse_post_frame_update(self, cmd_byte, stream):
        pfu = copy.deepcopy(self.post_frame_update_template)
        pfu.command_byte.val = cmd_byte

        pfu.read(stream, self.version, ignore_fields=["command_byte"])
        self.post_frames.add_frame(pfu)

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

        for pres, posts in zip(self.pre_frames, self.post_frames):
            for pre in pres:
                if pre:
                    pre.write(stream, self.version)
            for post in posts:
                if post:
                    post.write(stream, self.version)

        self.game_end.write(stream, self.version)

        total_written = stream.tell() - start_offset

        stream.write(self.metadata)

        stream.seek(location_0)
        self.write_ubjson_header(stream, total_written)


if __name__ == "__main__":
    slp_bin = SlpBin("configs")

    with open("samples/offline_2.slp", "rb") as f:
        slp_bin.read(f)

    with open("samples/test_out.slp", "wb") as f:
        slp_bin.write(f)
