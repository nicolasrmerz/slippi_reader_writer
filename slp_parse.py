from dataclasses import dataclass
import packaging
from typing import Union, List
from slp_dataclasses import EventPayloads, Start
from dacite import from_dict
import json



@dataclass
class SlpBin:
    event_payloads: EventPayloads
    start: Start

if __name__ == "__main__":
    with open('configs/start_defaults.json', 'r') as f:
        data = json.load(f)

    slp_bin = from_dict(data_class=Start, data=data)
    print(slp_bin)
