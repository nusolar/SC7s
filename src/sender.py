import json
from receiver import Receiver
import threading
import time
import csv
from datetime import datetime
from digi.xbee.devices import XBeeDevice

class CAN_value:
    """
    CAN value object, which manages the common occurence of getting multiple
    values for a specific CAN tag before wanting to send it, through simple averaging.
    """
    def __init__(self, value=None):
        self.value = value
        if value is None:
            self.n = 0
        else:
            self.n = 1

    def get_value(self) -> float:
        self.n = 0
        save = self.value
        self.value = None
        return save

    def pass_value(self, value):
        if self.value is None:
            self.value = 0
        self.value = (self.n * self.value + value) / (self.n + 1)
        self.n += 1


class Row:
    """
    Timestamped list of CAN_values
    """
    def __init__(self):
        self.timestamp = None
        self.lst = [CAN_value() for i in range(len(sendables))]

    def __str__(self):
        self.stamp()
        string = str(self.timestamp)
        for can_val in self.lst:
            string += " " + str(can_val.get_value())
        return string

    def stamp(self):
        self.timestamp = datetime.timestamp(datetime.now())

    def make_dict(self):
        row_dict = {"Timestamp": self.timestamp}
        for tag in sendables:
            row_dict[tag] = self.lst[tags_to_indices[tag]]
        return row_dict

# Set of CAN values to be sent to the base-station
sendables = {'15VS', '33VS', '19VS'}

# Dict mapping tags to indices into the row of CAN values
tags_to_indices = {}

# Global list of CAN values, with an initial timestamp. 
# Updated by the accumulator thread and periodically read from by the main thread, 
# which sends sends this list over the xbee radio. This will later
# become a row that is inserted into an SQL database, so it is called `row`.
row = Row()


def construct_tags_to_indices(table_file: str):
    """
    Determine the index into the row list from the CAN value name.
    This is a completely arbitray choice that will be determined later on
    once we have decided which CAN values we care about and how we want to
    order them.
    The index is determined by the order in which the tags appear in
    the table_file (normally can_table.csv).

    For example, if sendables == {'13VS', '15VS', 'VVEL', 'MVEL'},
    then the tags_to_indices would be constructud as
            -------------------------------------
            | 'VVEL' | 'MVEL' | '13VS' | '15VS' |
            -------------------------------------
            |   0    |   1    |   2    |   3    |
            -------------------------------------
    since they appear in that order can_table.csv
    """
    with open(table_file) as table:
        csv_reader = csv.DictReader(table)
        i = 0
        for row in csv_reader:
            if row['Tag'] in sendables:
                tags_to_indices[row['Tag']] = i
                i += 1

    # check that all the tags in sendables have a mapping
    for key in sendables:
        if key not in tags_to_indices:
            raise Exception("construct_tags_to_indices: tag in sendables not in table_file : " + str(key))

def accumulator_worker(lock: threading.Lock):
    """
    The worker for the accumulator thread, which reads from the CAN line and
    updates the row list.
    """
    r = Receiver(serial_port='/dev/tty.usbserial-AC00QTXJ')
    for packet in r.get_packets_from_file('../examples/collected_cleaned.dat'):
        time.sleep(0.01)
        if packet['Tag'] in sendables:
            with lock:
                row.lst[tags_to_indices[packet['Tag']]].pass_value(packet['data'])

def setup_xbee():
    #Xbee RF Modem info
    serial_port_xbee = "COM5" #rPi uses /dev/ttyUSB#
    baud_rate_xbee = 57600 # or 9600 for the other one
    REMOTE_NODE_ID = "Router"

    device = XBeeDevice(serial_port_xbee, baud_rate_xbee)

    device.open()

    xbee_network = device.get_network()

    remote = xbee_network.discover_device(REMOTE_NODE_ID)

    #check if it found the other modem
    if remote is None:
        print("Coudn't do it.")
        exit(1)

    return device, remote


if __name__ == "__main__":
    construct_tags_to_indices('can_table.csv')
    print("TABLE:", tags_to_indices)

    # lock for managing access to global row
    lock = threading.Lock()

    # start CAN accumulator daemon thread
    acc = threading.Thread(target=accumulator_worker, args=(lock,), daemon=True)
    acc.start()

    device, remote = setup_xbee()

    while(True):
        time.sleep(2)
        with lock:
            print("Sending data to %s >> %s..." % (remote.get_64bit_addr(), row))
            json_row = json.dumps(row.make_dict())
            device.send_data(remote, json_row)

    # TODO: change from printing to sending over xbee
    # while True:
    #     time.sleep(2)
    #     with lock:
    #         print(row)
