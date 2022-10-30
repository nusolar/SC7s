import argparse
from src.can.receiver import Receiver

parser = argparse.ArgumentParser()

parser.add_argument("--interface", "--interface",
        help="Interface to CAN bus, either 'canusb' or 'pican'")
parser.add_argument("--serial-port", "--serial_port",
        help="Serial port for the canusb, e.g '/dev/tty.usbserial-AC00QTXJ'")
args = parser.parse_args()

r = Receiver(serial_port=args.serial_port, interface=args.interface)

for item in r.get_packets():
    print(item)
