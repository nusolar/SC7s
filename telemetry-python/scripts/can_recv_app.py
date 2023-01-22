# database stuff for contacts list
# this is the code that only interacts with the user

import time
import src.backend.can_db as can_db
from digi.xbee.devices import XBeeDevice
import json

PORT = "/dev/tty.usbserial-A21SPQED"
BAUD_RATE = 57600

# open database connection
connection = can_db.connect()
can_db.create_tables(connection)


def make_row(row_dict):
    pass


def main():

    device = XBeeDevice(PORT, BAUD_RATE)


    try:
        device.open()

        def data_receive_callback(xbee_message):
            # xbee_message.remote_device.get_64bit_addr()
            # print(xbee_message.data.decode())
            json_row = json.loads(xbee_message.data)
            print(json_row)
            can_db.add_row(connection, json_row)

        device.add_data_received_callback(data_receive_callback)

        print("Waiting for data...\n")
        input()
        time.sleep(1000)

    finally:
        if device is not None and device.is_open():
            device.close()


if __name__ == '__main__':
    main()
