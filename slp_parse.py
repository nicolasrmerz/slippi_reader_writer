from dataclasses import dataclass
import packaging
from typing import Union, List
from slp_dataclasses import EventPayloads, Start



@dataclass
class SlpBin:
    event_payloads: EventPayloads
    start: Start
