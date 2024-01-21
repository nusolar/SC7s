from __future__ import annotations
from typing import Optional
from datetime import datetime
import json, msgpack
import pickle
from src import ROOT_DIR
from pathlib import Path
from cantools.database.can.database import Database
import can.message

from src.util import find

class CanValue:
    """
    CAN value object, which manages the common occurence of getting multiple
    values for a specific CAN tag before wanting to send it, through simple averaging.
    """
    def __init__(self: CanValue, value: Optional[float] = None, is_averaged = True) -> None:
        self.value: Optional[int | float] = value
        self.is_averaged = is_averaged
        if value is None:
            self.n = 0
        else:
            self.n = 1

    def fetch(self: CanValue) -> Optional[int | float]:
        if not self.is_averaged:
            return self.value
        else:
            self.n = 0
            save = self.value
            self.value = None
            return save

    def update(self: CanValue, value):
        if not self.is_averaged:
            self.value = value
        else:
            if self.value is None:
                self.value = 0
            self.value = (self.n * self.value + value) / (self.n + 1)
            self.n += 1


class Row:
    def __init__(self, sigdef: Database | dict[str, CanValue], name: str, timestamp: Optional[float] = None) -> None:
        self.timestamp: Optional[float] = timestamp
        self.name = name
        self.signals: dict[str, CanValue] = {}

        if isinstance(sigdef, Database):
            for msg in [msg for msg in sigdef.messages if name in msg.senders]:
                for signal in msg.signals:
                    self.signals[signal.name] = CanValue(is_averaged=signal.is_float)
        elif isinstance(sigdef, dict):
            self.signals = sigdef
        else:
            raise Exception("Unknown type of sigdef: {type(sigdef)}")

    def owns(self, msg: can.message.Message, db: Database) -> bool:
        found = find(db.messages, lambda m:  m.frame_id == msg.arbitration_id)
        if found is None:
            return False

        return self.name in found.senders

    def stamp(self):
        self.timestamp = datetime.now().timestamp()

    @classmethod
    def sorted_signal_names(cls, node_name: str, db: Database) -> list[str]:
        return sorted([s.name for m in db.messages if node_name in m.senders for s in m.signals])

    def serialize(self) -> str:
        if self.timestamp is None:
            raise Exception("Attempt to serialize unstamped row")

        #Create a sorted array from the signal made out of the values of the keys in each signal sorted by key alphabetically
        signals = {k: v.fetch() for k, v in self.signals.items()}       
        sig_keys = list(signals.keys())
        sig_keys.sort()
        signals = [signals[sig_keys[i]] for i in range(len(sig_keys))]
        #Serialize row data using msgpack
        return msgpack.packb(
            [self.timestamp, self.name, *signals],
            use_bin_type=True
        ) # type: ignore

    @classmethod
    def deserialize(cls, s: str, db: Database) -> Row:
        #Deserialize data using message pack and create signal dictionary by giving values in array a named key according to their position in array 
        d = msgpack.unpackb(s, raw=False, strict_map_key=False)
        #Get keys of device from dbc file
        keys = Row.sorted_signal_names(d[1], db)
        vals = d[2:]
        d_sig = {keys[i]:vals[i] for i in range(len(vals))}
        signals = {k: CanValue(v) for k, v in d_sig.items()}
        return Row(signals, d[1], timestamp=d[0])
