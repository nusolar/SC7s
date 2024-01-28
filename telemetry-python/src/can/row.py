from __future__ import annotations
from typing import Optional
from datetime import datetime
import json
from typing import Optional, Dict

from cantools.database.can.database import Database
import can.message

from src.util import find
from dataclasses import dataclass,field


@dataclass
class CanValue:
    """ 
    Representation of a CAN value object, which manages the common occurence of getting multiple
    values for a specific CAN tag before wanting to send it, through simple averaging.
    
    Parameters
    ----------
    value : Optional[Union[int, float]]
        The current value of the CAN tag.
    is_averaged : bool
        Indicates whether to perform simple averaging.
    n : int
        The count of values received for averaging.

    Methods
    -------
    fetch() -> Optional[Union[int, float]]
        Retrieves the current value, considering averaging if enabled.

    update(value)
        Updates the current value, incorporating simple averaging if enabled.

    Returns
    -------
    None
        Does not return anything.
    """
    value: Optional[int | float] = None
    is_averaged: bool = True
    n: int = 0
    
    def __post_init__(self):
        """
        Perform post-initialization tasks.

        Returns
        -------
        None
            Does not return anything.
        """
        if self.value is not None:
            self.n = 1

    def fetch(self: CanValue) -> Optional[int | float]:
        """
        Retrieves the current value, considering averaging if enabled.

        Returns
        -------
        Optional[Union[int, float]]
            The current value.
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
        Updates the current value, incorporating simple averaging if enabled.

        Parameters
        ----------
        value : Union[int, float]
            The new value to update.

        Returns
        -------
        None
            Does not return anything.
        """
        if not self.is_averaged:
            self.value = value
        else:
            if self.value is None:
                self.value = 0
            self.value = (self.n * self.value + value) / (self.n + 1)
            self.n += 1

@dataclass
class Row:
    """
    Represents a row of data containing signals with their values.

    Parameters
    ----------
    sigdef : Union[Database, Dict[str, CanValue]]
        Signal definition, either a Database or a dictionary of CanValue objects.
    name : str
        The name of the row.
    timestamp : Optional[float], optional
        The timestamp associated with the row.
    signals : Dict[str, CanValue]
        A dictionary of signals with their CanValue objects.

    Raises
    ------
    Exception
        Raised for an unknown type of sigdef.
        
    Returns
    -------
    None
        Does not return anything.
    """
    name: str
    signals: Dict[str, CanValue] = field(default_factory=dict)
    timestamp: Optional[float] = None

    def __post_init__(self, sigdef: Database | dict[str, CanValue]) -> None:
        """
        Initialize the Row object depenfing on the signal definition type.

        Parameters
        ----------
        sigdef : Union[Database, Dict[str, CanValue]]
            Signal definition, either a Database or a dictionary of CanValue objects.

        Returns
        -------
        None
            Does not return anything.
        """
        if isinstance(sigdef, Database):
            for msg in [msg for msg in sigdef.messages if self.name in msg.senders]:
                for signal in msg.signals:
                    self.signals[signal.name] = CanValue(is_averaged=signal.is_float)
        elif isinstance(sigdef, dict):
            self.signals = sigdef
        else:
            raise Exception(f"Unknown type of sigdef: {type(sigdef)}")

    def owns(self, msg: can.message.Message, db: Database) -> bool:
        """
        Check if the row owns a CAN message.

        Parameters
        ----------
        msg : can.message.Message
            The CAN message to check ownership.
        db : Database
            The database containing message definitions.

        Returns
        -------
        bool
            True if the row owns the message, False otherwise.
        """
        found = find(db.messages, lambda m:  m.frame_id == msg.arbitration_id)
        if found is None:
            return False

        return self.name in found.senders

    def stamp(self):
        """
        Stamp the row with the current timestamp.
        """
        self.timestamp = datetime.now().timestamp()

    def serialize(self, indent=None) -> str:
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
        return json.dumps({
            "timestamp": self.timestamp,
            "name"     : self.name,
            "signals"  : {k: v.fetch() for k, v in self.signals.items()}
        }, indent=indent)

    @classmethod
    def deserialize(cls, s: str) -> Row:
        """
        Deserialize a JSON-formatted string into a Row object.

        Parameters
        ----------
        s : str
            JSON-formatted string representing the serialized row.

        Returns
        -------
        Row
            Deserialized Row object.
        """
        d = json.loads(s)
        signals = {k: CanValue(v) for k, v in d["signals"].items()}
        return Row(signals, d["name"], timestamp=d["timestamp"])
