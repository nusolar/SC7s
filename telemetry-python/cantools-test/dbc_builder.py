from pathlib import Path
from enum import Enum
import cantools.database
from copy import deepcopy

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
        abstract_db: cantools.database.Database = cantools.database.load_file(self.path) # type: ignore
        real_nodes: list[cantools.database.Node]       = []
        real_messages: list[cantools.database.Message] = []

        abstract_mppt             = [node for node in abstract_db.nodes if node.name == "ABSTRACT_MPPT"][0]
        # abstract_motor_controller = [node for node in db.nodes if node.name == "ABSTRACT_MOTOR_CONTROLLER"][0]
        # abstract_bms              = [node for node in db.nodes if node.name == "ABSTRACT_BMS"][0]

        for dev in self.devices:
            match dev.kind:
                case DeviceType.MPPT:
                    node_name = f"MPPT_{hex(dev.base_address)}"
                    specifics = abstract_mppt.dbc
                    real_nodes.append(cantools.database.Node(node_name, dbc_specifics=specifics))
                    abstract_mppt_messages = [msg for msg in abstract_db.messages if msg.senders[0] == "ABSTRACT_MPPT"]

                    for msg in abstract_mppt_messages:
                        real_msg = deepcopy(msg)
                        real_msg.frame_id = dev.base_address + msg.frame_id
                        real_msg._senders = [node_name]
                        real_messages.append(real_msg)

                case _:
                    raise Exception(f"Unknown device type: {dev.kind}")
        return cantools.database.Database(messages=real_messages, nodes=real_nodes)



if __name__ == "__main__":
    adbc = AbstractDbc(Path("abstract.dbc"), [Device(DeviceType.MPPT, 0x600), Device(DeviceType.MPPT, 0x610)])
    db = adbc.create_real_dbc()
    cantools.database.dump_file(db, "out.dbc")

