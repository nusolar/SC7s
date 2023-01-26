import can
import cantools.database

if __name__ == "__main__":
    # Load in the CAN database file
    db = cantools.database.load_file("out.dbc")

    with can.interface.Bus(channel='can0', bustype='socketcan') as bus:  # type: ignore
        while True:
            msg = bus.recv()
            print({**{"id": msg.arbitration_id}, **db.decode_message(msg.arbitration_id, msg.data)} #type: ignore

