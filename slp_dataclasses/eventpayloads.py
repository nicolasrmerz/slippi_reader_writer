from dataclasses import dataclass
from typing import List

from .common import U8Data, U16Data


def generate_payload_size_dict(epl):
    d = {e.command_byte.val: e.payload_size.val for e in epl.other_cmds}
    d[epl.command_byte.val] = epl.payload_size.val

    return d


@dataclass
class BasePayload:
    command_byte: U8Data
    payload_size: U8Data

    def write(self, stream, given_version):
        self.command_byte.write(stream, given_version)
        self.payload_size.write(stream, given_version)


@dataclass
class OtherEventPayloads(BasePayload):
    payload_size: U16Data

    # TODO: Figure out best way for inheritance to avoid code duplication
    @staticmethod
    def read(stream):
        epl = OtherEventPayloads(
            command_byte=U8Data(val=0), payload_size=U16Data(val=0)
        )
        epl.command_byte.read(stream, False)
        epl.payload_size.read(stream, False)

        return epl


@dataclass
class EventPayloads(BasePayload):
    other_cmds: List[OtherEventPayloads]

    # TODO: Figure out best way for inheritance to avoid code duplication
    @staticmethod
    def read(stream):
        epl = EventPayloads(
            command_byte=U8Data(val=0), payload_size=U8Data(val=0), other_cmds=list()
        )
        epl.command_byte.read(stream, False)
        epl.payload_size.read(stream, False)

        # payload size is included in the payload size
        payload_size = epl.payload_size.val - 1

        # each other payload is 1-byte command_byte + 2-byte payload_size
        for _ in range(payload_size // 3):
            epl.other_cmds.append(OtherEventPayloads.read(stream))

        return epl

    def write(self, stream, given_version):
        super().write(stream, given_version)

        for pl in self.other_cmds:
            pl.write(stream, given_version)
