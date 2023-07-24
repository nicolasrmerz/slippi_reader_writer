import json
import os
import struct
from typing import Optional

from dacite import from_dict

from slp_dataclasses import EventPayloads, GameStart
from slp_dataclasses.eventpayloads import generate_payload_size_dict


class SlpBin:
    def __init__(self, config_dir):
        self.event_payloads: Optional[EventPayloads] = None
        self.payload_size_dict: dict = dict()
        self.version: str = ""
        # pre_frame_update_template: PreFrameUpdate
        # post_frame_update_template: PostFrameUpdate
        self.game_start = self.init_game_start(config_dir)

        self.CMD_BYTE_PARSER_MAP = {
            0x36: self.parse_game_start,
        }

    def init_game_start(self, config_dir):
        with open(os.path.join(config_dir, "start_defaults.json"), "r") as f:
            data = json.load(f)
        return from_dict(data_class=GameStart, data=data)

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

        total_written = stream.tell() - start_offset

        stream.seek(location_0)
        self.write_ubjson_header(stream, total_written)


if __name__ == "__main__":
    slp_bin = SlpBin("configs")

    with open("samples/offline.slp", "rb") as f:
        slp_bin.read(f)

    with open("samples/test_out.slp", "wb") as f:
        slp_bin.write(f)
