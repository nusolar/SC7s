from curses import baudrate
from digi.xbee.devices import XBeeDevice
import serial

#Xbee RF Modem info
serial_port_xbee = "COM5" #rPi uses /dev/ttyUSB#
baud_rate_xbee = 57600 # or 9600 for the other one
REMOTE_NODE_ID = "Router"

#CANUSB info
serial_port_can = 'COM4' #rPi uses /dev/ttyUSB#
baud_rate_can = 57600 # or 9600 for the other one

#f = open("output_can.txt", "x")

device = XBeeDevice(serial_port_xbee, baud_rate_xbee)

device.open()

xbee_network = device.get_network()

remote = xbee_network.discover_device(REMOTE_NODE_ID)

#check if it found the other modem
if remote is None:
    print("Coudn't do it.")
    exit(1)

#read CAN from other serial port and send
with serial.Serial(serial_port_can, baud_rate_can) as receiver:
    while(True):
        raw = receiver.read_until(b';').decode()
        #outputs :S40ENBF49753D00000000;
        print("Sending data to %s >> %s..." % (remote.get_64bit_addr(), raw))
        device.send_data(remote, raw)

device.close()
#COM5 - 57600/8/N/1/N - AT