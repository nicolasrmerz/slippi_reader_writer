import copy
from dataclasses import dataclass

from slp_dataclasses.common import ArrayData, BinData, U8Data, U16Data


@dataclass
class MessageSplitter(BinData):
    command_byte: U8Data
    fixed_size_block: ArrayData
    actual_size: U16Data
    internal_command: U8Data
    last_message: U8Data


class GeckoCode:
    def __init__(self, ms_template):
        self.gecko_cmd_byte = None
        self.gecko_code = None
        self.message_splitter_list = list()
        self.ms_template = ms_template

    def add_message(self, cmd_byte, stream, version):
        msg = copy.deepcopy(self.ms_template)
        msg.command_byte.val = cmd_byte

        msg.read(stream, version, ignore_fields=["command_byte"])

        self.message_splitter_list.append(msg)

    def write_message_splitter_list(self, stream, version):
        for m in self.message_splitter_list:
            m.write(stream, version)
