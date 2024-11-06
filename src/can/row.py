from __future__ import annotations
from typing import Optional
from datetime import datetime
import msgpack

from cantools.database.can.database import Database
import can.message

from src.util import find

class CanValue:
    """
    CAN value object, which manages the common occurence of getting multiple
    values for a specific CAN tag before wanting to send it, through simple averaging.
    """
    def __init__(self: CanValue, value: Optional[float] = None, is_averaged = True) -> None:
        """
        Initializes the CAN value Object.
        """
        self.value: Optional[int | float] = value
        self.is_averaged = is_averaged
        if value is None:
            self.n = 0
        else:
            self.n = 1

    def fetch(self: CanValue) -> Optional[int | float]:
        """
        Retrieves the CAN value, and if the is_averaged is set to true, resets CAN value.

        Parameters
        ----------
        None

        Returns
        ----------
        int, float
            value stored in the CAN
        """
        if not self.is_averaged:
            return self.value
        else:
            self.n = 0
            save = self.value
            self.value = None
            return save

    def update(self: CanValue, value):
        """
        Updates the CAN value.
        If is_averaged is false, updates CAN value by replacing value field.
        If is_averaged is true, updates CAN value by calculating new average of CAN values.

        Parameters
        ----------
        value : int, float, None
            value to be updated to the CAN
        
        Returns
        ----------
        None
        """
        if not self.is_averaged:
            self.value = value
        else:
            if self.value is None:
                self.value = 0
            self.value = (self.n * self.value + value) / (self.n + 1)
            self.n += 1


class Row:
    """
    ROW object, represents a row of CAN signal data, 
    containing name associated with signals, timestamp of when the row was stamped,
    and a dictionary mapping each signal name to a CanValue Object
    """
    def __init__(self, sigdef: Database | dict[str, CanValue], name: str, timestamp: Optional[float] = None) -> None:
        """
        Initializes the ROW Object.
        """
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
        """
        Checks if the ROW object "owned" or sent a CAN message in the provided database.

        Parameters
        ----------
        msg : can.message.Message
            a CAN message
        db : Database
            a database

        Results:
        ----------
        bool 
            true if name of the row matches the sender of the message, else false.

        """
        found = find(db.messages, lambda m:  m.frame_id == msg.arbitration_id)
        if found is None:
            return False

        return self.name in found.senders

    def stamp(self):
        self.timestamp = datetime.now().timestamp()

    @staticmethod
    def signal_names(node_name: str, db: Database) -> list[str]:
        return [s.name for m in db.messages if node_name in m.senders for s in m.signals]


    def serialize(self) -> bytes:
        """
        Serialize the row to a JSON-formatted string.

        Parameters
        ----------
        indent : int, optional
            Number of spaces to use for indentation in the output.

        Returns
        -------
        str
            JSON-formatted string representing the serialized row.
        """
        if self.timestamp is None:
            raise Exception("Attempt to serialize unstamped row")

        #Create a sorted array from the signal made out of the values of the keys in each signal sorted by key alphabetically
        signals = [v.fetch() for v in self.signals.values()]

        #Serialize row data using msgpack
        return msgpack.packb(
            [self.timestamp, self.name, signals],
            use_bin_type=True
        ) # type: ignore

    @classmethod
    def deserialize(cls, b: bytes, db: Database) -> Row:
        """
        Deserialize a JSON-formatted string into a Row object.

        Parameters
        ----------
        s : str
            JSON-formatted string representing the serialized row.
        db: Database
            cantools configuration database.

        Returns
        -------
        Row
            Deserialized Row object.
        """
        #Deserialize data using message pack and create signal dictionary by
        # giving values in array a named key according to their position in array 
        timestamp, name, values = msgpack.unpackb(b, raw=False, strict_map_key=False)

        #Get keys of device from dbc file
        keys = Row.signal_names(name, db)
        d_sig = { keys[i]:values[i] for i in range(len(values)) }
        signals = { k: CanValue(v) for k, v in d_sig.items() }
        return Row(signals, name, timestamp)
