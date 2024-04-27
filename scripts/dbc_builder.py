# TODO: The structure of this file works fine, but I think the code could
# be improved stylistically. This could be a good mini-project for someone
# looking to get their hands dirty with the code base and learn some more
# advanced Python (check out https://stackoverflow.com/a/71519690; algebraic
# data types are really nice!).

from typing import cast
from enum import Enum
from copy import deepcopy

from pathlib import Path
import cantools.database
from cantools.database.can.node import Node
from cantools.database.can.message import Message
from cantools.database.can.database import Database

from src import ROOT_DIR
from src.util import find

class DeviceType(Enum):
    MPPT = 0,
    MOTOR_CONTROLLER = 1,
    BMS = 2

class Device():
    """A Device on the CAN network.
    For the purposes of creating dbc files, a device is simpy something
    with a `kind` (MPPT, Motor Controller, etc.) and a `base_adress`.
    """
    def __init__(self, kind: DeviceType, base_address: int) -> None:
        self.kind         = kind
        self.base_address = base_address

class AbstractDbc():
    """An `AbstractDbc` contains information necessary to instantiate
    a CAN database for a list a given list of devices, all of which
    should be of the same device type.
    """
    def __init__(self, path: Path, devices: list[Device]) -> None:
        """Create an `AbstractDbc` from the dbc file at `path` for
        the devices in `devices`.

        The file at `path` is expected to be a dbc file for a single
        device at base address 0x0 (the CAN ids for signals in the
        files are therefore effectively offsets from the base adress).
        The device present in this file should be of the same type
        as the devices in `devices`.
        """
        self.path    = path
        self.devices = devices

    def create_real_dbc(self) -> cantools.database.Database:
        """ Create the CAN database for the devices present in `self`.
        """
        abstract_db = cast(Database, cantools.database.load_file(self.path))
        real_nodes:    list[Node]    = []
        real_messages: list[Message] = []

        abstract_mppt             = find(abstract_db.nodes, lambda node: node.name == "ABSTRACT_MPPT")
        abstract_motor_controller = find(abstract_db.nodes, lambda node: node.name == "ABSTRACT_MOTOR_CONTROLLER")
        abstract_bms              = find(abstract_db.nodes, lambda node: node.name == "ABSTRACT_BMS")

        for dev in self.devices:
            match dev.kind:
                case DeviceType.MPPT:
                    assert abstract_mppt is not None
                    node_name = f"MPPT_{hex(dev.base_address)}"
                    abstract_messages = [msg for msg in abstract_db.messages
                                              if msg.senders[0] == "ABSTRACT_MPPT"]
                    specifics = abstract_mppt.dbc
                case DeviceType.MOTOR_CONTROLLER:
                    assert abstract_motor_controller is not None
                    node_name = f"MOTOR_CONTROLLER_{hex(dev.base_address)}"
                    abstract_messages = [msg for msg in abstract_db.messages
                                              if msg.senders[0] == "ABSTRACT_MOTOR_CONTROLLER"]
                    specifics = abstract_motor_controller.dbc
                case _:
                    raise Exception(f"Unknown device type: {dev.kind}")

            real_nodes.append(cantools.database.Node(node_name, dbc_specifics=specifics))
            for msg in abstract_messages:
                real_msg = deepcopy(msg)
                real_msg.frame_id = dev.base_address + msg.frame_id
                real_msg._senders = [node_name]
                real_messages.append(real_msg)

        return cantools.database.Database(messages=real_messages, nodes=real_nodes)



if __name__ == "__main__":
    # This script constructs CAN DBC files for the devices in the solar car.
    # 'Abstract' DBC files are expected to specify messages for a device at
    # base address 0x0, in accordance with the CAN frames specification provided
    # by the device vendor.
    #
    # We use these files to create real dbc files for real devices at actual
    # base address.
    #
    # This script only serves to simplify DBC file creation and only needs to
    # be re-run when we need to update these files (e.g. the devices on the
    # CAN network have changed).

    # Make a dbc file for all our MPPTs
    adbc = AbstractDbc(
        ROOT_DIR.joinpath("resources", "abstract_mppt.dbc"),
        [Device(DeviceType.MPPT, 0x600), Device(DeviceType.MPPT, 0x610), Device(DeviceType.MPPT, 0x620)]
    )
    db = adbc.create_real_dbc()
    cantools.database.dump_file(db, ROOT_DIR.joinpath("resources", "mppt.dbc"))

    # Make a dbc file for all our motor controllers
    adbc = AbstractDbc(
        ROOT_DIR.joinpath("resources", "abstract_motor_controller.dbc"),
        [Device(DeviceType.MOTOR_CONTROLLER, 0x400)]
    )
    db = adbc.create_real_dbc()
    cantools.database.dump_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))

