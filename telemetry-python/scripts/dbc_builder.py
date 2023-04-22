from typing import cast
from enum import Enum
from copy import deepcopy

from pathlib import Path
import cantools.database
from cantools.database.can.node import Node
from cantools.database.can.message import Message
from cantools.database.can.database import Database
from src import ROOT_DIR

class DeviceType(Enum):
    MPPT = 0,
    MOTOR_CONTROLLER = 1,
    BMS = 2

class Device():
    def __init__(self, kind: DeviceType, base_address: int) -> None:
        self.kind         = kind
        self.base_address = base_address

class AbstractDbc():
    def __init__(self, path: Path, devices: list[Device]) -> None:
        self.path    = path
        self.devices = devices

    def create_real_dbc(self) -> cantools.database.Database:
        abstract_db = cast(Database, cantools.database.load_file(self.path))
        real_nodes:    list[Node]    = []
        real_messages: list[Message] = []

        abstract_mppt             = next((node for node in abstract_db.nodes \
                                            if node.name == "ABSTRACT_MPPT"),
                                         None)
        abstract_motor_controller = next((node for node in abstract_db.nodes \
                                            if node.name == "ABSTRACT_MOTOR_CONTROLLER"),
                                         None)
        abstract_bms              = next((node for node in abstract_db.nodes \
                                            if node.name == "ABSTRACT_BMS"),
                                         None)

        for dev in self.devices:
            match dev.kind:
                case DeviceType.MPPT:
                    assert abstract_mppt is not None
                    node_name = f"MPPT_{hex(dev.base_address)}"
                    abstract_mppt_messages = [msg for msg in abstract_db.messages \
                                              if msg.senders[0] == "ABSTRACT_MPPT"]
                    specifics = abstract_mppt.dbc
                case DeviceType.MOTOR_CONTROLLER:
                    assert abstract_motor_controller is not None
                    node_name = f"MOTOR_CONTROLLER_{hex(dev.base_address)}"
                    abstract_mppt_messages = [msg for msg in abstract_db.messages \
                                              if msg.senders[0] == "ABSTRACT_MOTOR_CONTROLLER"]
                    specifics = abstract_motor_controller.dbc
                case _:
                    raise Exception(f"Unknown device type: {dev.kind}")

            real_nodes.append(cantools.database.Node(node_name, dbc_specifics=specifics))
            for msg in abstract_mppt_messages:
                real_msg = deepcopy(msg)
                real_msg.frame_id = dev.base_address + msg.frame_id
                real_msg._senders = [node_name]
                real_messages.append(real_msg)

        return cantools.database.Database(messages=real_messages, nodes=real_nodes)



if __name__ == "__main__":
    adbc = AbstractDbc(Path(ROOT_DIR).joinpath("resources", "abstract_mppt.dbc"),
                       [Device(DeviceType.MPPT, 0x600), Device(DeviceType.MPPT, 0x610)])
    db = adbc.create_real_dbc()
    cantools.database.dump_file(db, Path(ROOT_DIR).joinpath("resources", "mppt.dbc"))

    adbc = AbstractDbc(Path(ROOT_DIR).joinpath("resources", "abstract_motor_controller.dbc"),
                       [Device(DeviceType.MOTOR_CONTROLLER, 0x400), Device(DeviceType.MOTOR_CONTROLLER, 0x500)])
    db = adbc.create_real_dbc()
    cantools.database.dump_file(db, Path(ROOT_DIR).joinpath("resources", "motor_controller.dbc"))

