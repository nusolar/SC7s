from time import sleep
from threading import Thread

import can
import cantools.database
from cantools.database.can.database import Database

from src.can.stats import mock_value

def device_worker(bus: can.ThreadSafeBus, my_messages: list[cantools.database.Message]) -> None:
    """
    Constantly sends messages on the `bus`.

    Parameters
    ----------
    bus : can.ThreadSafeBus
        object that ensures messages are sent in a thread-safe manner
    my_message : list[cantools.database.Message]
        list of messages being sent
    
    Returns
    ----------
    None
    """
    while True:
        for msg in my_messages:
            d = {}
            for sig in msg.signals:
                d[sig.name] = mock_value(msg.senders[0], sig.name)
            data = msg.encode(d)
            bus.send(can.Message(arbitration_id=msg.frame_id, data=data))
            sleep(0.1)
        sleep(1)

def start_virtual_can_bus(bus: can.ThreadSafeBus, db: Database) -> list[Thread]:
    """
    Create a thread for each node in the database file. 
    Each thread gets a copy of the bus for writing.
    Each thread sends only the messages that the corresponding device would send.

    This function starts all these threads and returns a handle to them so that
    they can be joined if needed.

    Parameters
    ----------
    bus : can.ThreadSafeBus
        object that ensures messages are sent in a thread-safe manner
    db : Database
        database of nodes

    Returns
    ----------
    None
    """
    dev_threads: list[Thread] = []
    for i, _ in enumerate(db.nodes):
        dev_threads.append(Thread(target=device_worker,
                                  args=(bus,
                                        [msg for msg in db.messages if msg.senders[0] == db.nodes[i].name]),
                                  daemon=True))

    for thread in dev_threads:
        thread.start()

    return dev_threads
