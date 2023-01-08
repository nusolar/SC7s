from typing import Union
import can
import cantools.database
from time import sleep
from threading import Thread
import random
import sqlite3

VIRTUAL_BUS_NAME = "virtbus"

UINT8_MAX = 0xFF

# (mean, stddev) for different signals
# Very loosely based on real data
MPIV_STATS   = (9.75, 0.1)
MPIC_STATS   = (0.0005, 0.0001)
MPOV_STATS   = (10.3, 0.1)
MPOC_STATS   = (6e-5, 1e-5)
MPMST_STATS  = (23.8, 0.1)
MPCT_STATS   = (30.4, 0.1)
MP12V_STATS  = (12.0, 0.05)
MP3V_STATS   = (3.0, 0.05)
MPMOV_STATS  = (109.1, 0.0)
MPMIC_STATS  = (7.0, 0.0)
MPPCOV_STATS = (10.5, 0.2)
MPPCT_STATS  = (23.65, 0.01)

test_counter = random.randint(0, UINT8_MAX)

def inc_counter() -> int:
    """
    Increment test counter with modular arithmetic.
    """
    global test_counter

    test_counter = (test_counter + 1) % (UINT8_MAX + 1)

    return test_counter

def handler(node: str, id_offset, sig_start: int) -> Union[float, int]:
    """
    Make a mock value for a signal.
    """
    if "MPPT" in node:
        match (id_offset, sig_start):
            case (0x0, 0):
                return random.normalvariate(*MPIV_STATS)
            case (0x0, 32):
                return random.normalvariate(*MPIC_STATS)
            case (0x1, 0):
                return random.normalvariate(*MPOV_STATS)
            case (0x1, 32):
                return random.normalvariate(*MPOC_STATS)
            case (0x2, 0):
                return random.normalvariate(*MPMST_STATS)
            case (0x2, 32):
                return random.normalvariate(*MPCT_STATS)
            case (0x3, 0):
                return random.normalvariate(*MP12V_STATS)
            case (0x3, 32):
                return random.normalvariate(*MP3V_STATS)
            case (0x4, 0):
                return random.normalvariate(*MPMOV_STATS)
            case (0x4, 32):
                return random.normalvariate(*MPMIC_STATS)
            case (0x5, 0):
                return 0 # RX error counter is 0, for simplicity
            case (0x5, 8):
                return 0 # TX error counter is 0, for simplicity
            case (0x5, 16):
                return 0 # TX overflow counter is 0, for simplicity
            case (0x5, num) if num in range(24, 40):
                return 0 # No error / limit flags are set, for simplicity
            case (0x5, 40):
                return 1 # Mode = 1 for "on." 0 is for "standby."
            case (0x5, 56):
                return inc_counter() # Increment test counter every time
            case (0x6, 0):
                return random.normalvariate(*MPPCOV_STATS)
            case (0x6, 32):
                return random.normalvariate(*MPPCT_STATS)
            case (0x7, 0):
                return 0 # TODO: maybe collect real data for sweep measurments
            case (0x7, 32):
                return 0 # TODO: maybe collect real data for sweep measurments
            case _:
                raise Exception(f"Unknown id offset / signal offset ({id_offset}, {sig_start})")
    else:
        raise Exception("Unknown node")

def worker(bus: can.interface.Bus, my_messages:  list[cantools.database.Message]) -> None:
    """
    Constantly sends messages on the `bus`.
    """
    while True:
        for msg in my_messages:
            d = {}
            for sig in msg.signals:
                # print(msg.senders)
                d[sig.name] = handler(msg.senders[0], msg.frame_id % 16, sig.start)
            data = msg.encode(d)
            bus.send(can.Message(arbitration_id=msg.frame_id, data=data))
            sleep(0.1)
        sleep(1)

if __name__ == "__main__":
    conn   = sqlite3.connect('virt.db')
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS virtdata (
                Three_V REAL
           )
        """
    )

    # Load in the CAN database file
    db = cantools.database.load_file("out.dbc")

    # Give a copy of the virtual bus to the main thread, for receiving
    bus = can.interface.Bus(VIRTUAL_BUS_NAME, bustype='virtual') # type: ignore

    # Create a thread for each node in the database file. 
    # Each thread gets a copy of the bus for writing.
    # Each thread sends only the messages that the corresponding device would send.
    dev_threads: list[Thread] = []
    for i, node in enumerate(db.nodes): # type: ignore
        dev_threads.append(Thread(target=worker,
                                  args=(can.interface.Bus(VIRTUAL_BUS_NAME, bustype="virtual"),
                                        [msg for msg in db.messages if msg.senders[0] == db.nodes[i].name]),
                                  daemon=True))

    # Start the threads.
    # They are daemons so we don't need to join 
    for thread in dev_threads:
        thread.start()

    while True:
        msg = bus.recv()

        assert msg is not None

        # print({"base_address": hex(16 * (msg.arbitration_id // 16))} # type: ignore
              # | db.decode_message(msg.arbitration_id, msg.data))     # type: ignore

        
        for k, v in db.decode_message(msg.arbitration_id, msg.data).items():
            if k == "Three_V":
                cursor.execute(
                    """
                    INSERT INTO virtdata VALUES (?)
                    """,
                    (v,)
                )
                conn.commit()
            print({k: v})
