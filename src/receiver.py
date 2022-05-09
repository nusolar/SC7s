from random import choices
from canparse import CANParser
from time import time
import serial
from threading import Thread

class Receiver:
    """Receives & decodes CAN packets from a radio transmitter."""
    def __init__(self,
        can_table: str = 'can_table.csv',
        log_file: str = 'log.txt',
        serial_port: str = '/dev/tty.usbserial-AC00QTXJ',
        baud_rate: int = 500000):
        #Initialize fields
        self.can_table = can_table
        self.log_file = log_file
        self.serial_port = serial_port
        self.baud_rate = baud_rate

    def get_packets(self) -> iter:
        """Generates CAN Packets."""
        with serial.Serial(self.serial_port, self.baud_rate) as receiver:
            can_parser = CANParser(self.can_table)
            while(True):
                raw = receiver.read_until(b';').decode()
                if len(raw) != 23: continue
                raw = raw[1:len(raw) - 1]
                raw = raw.replace('S', '')
                raw = raw.replace('N', '')
                packet = can_parser.parse(raw)
                # packet['time'] = time()
                for item in packet:
                    yield item

    def get_packets_from_file(self, input_file_name: str) -> iter:
        """Generates CAN packets from file. Useful for testing."""
        with open(input_file_name) as input_file:
            can_parser = CANParser(self.can_table)
            for line in input_file:
                packet = can_parser.parse(line)
                # packet['time'] = time()
                for item in packet:
                    yield item


