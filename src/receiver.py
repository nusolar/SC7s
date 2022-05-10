from random import choices
from canparse import CANParser
from time import time
import serial
from threading import Thread
import can
import re

class Receiver:
    """Receives & decodes CAN packets from a radio transmitter."""
    def __init__(self,
        can_table: str = 'can_table.csv',
        log_file: str = 'log.txt',
        serial_port: str = '/dev/tty.usbserial-AC00QTXJ',
        baud_rate: int = 500000,
        interface: str = 'canusb'):
        #Initialize fields
        self.can_table = can_table
        self.log_file = log_file
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.interface = interface

    def get_packets(self) -> iter:
        """Generates CAN Packets."""

        can_parser = CANParser(self.can_table)
        if self.interface == 'canusb':
            with serial.Serial(self.serial_port, self.baud_rate) as receiver:
                while(True):
                    raw = receiver.read_until(b';').decode()
                    if len(raw) != 23: continue
                    raw = raw[1:len(raw) - 1]
                    raw = raw.replace('S', '')
                    raw = raw.replace('N', '')
                    packet = can_parser.parse(raw)
                    for item in packet:
                        yield item
        elif self.interface == 'pican':
            with can.interface.Bus(channel='can0', bustype='socketcan') as bus:
                for msg in bus:
                    # RegEx magic
                    tag = re.findall('(?<=ID: 0)[0-9]+', msg)[0]
                    data = re.findall('(?<= )([0-9a-f]{2})(?= )', msg)
                    data = ''.join(data) # concatenate all the hexits into a string
                    print(tag + data)
                    packet = can_parser.parse(tag + data)
                    for item in packet:
                        yield item
        else:
            raise Exception('Invalid interace')


    def get_packets_from_file(self, input_file_name: str) -> iter:
        """Generates CAN packets from file. Useful for testing."""
        with open(input_file_name) as input_file:
            can_parser = CANParser(self.can_table)
            for line in input_file:
                packet = can_parser.parse(line)
                # packet['time'] = time()
                for item in packet:
                    yield item


