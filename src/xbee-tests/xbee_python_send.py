from ast import excepthandler
from curses import baudrate
from tokenize import String
from digi.xbee.devices import XBeeDevice
import time

#COM5 - 57600/8/N/1/N - AT
# serial_port = "COM5"
serial_port = "/dev/ttyUSB0" # On MacOS
baud_rate = 9600
DATA_TO_SEND = "First One" 
REMOTE_NODE_ID = "Node"

device = XBeeDevice(serial_port, baud_rate)
remote = None

def setup_xbee():
    global remote
    device.open()
    xbee_network = device.get_network()
    remote = xbee_network.discover_device(REMOTE_NODE_ID)

    if remote is None:
        #print("Coudn't connect to %s", remote.get_64bit_addr())
        raise Exception("Coudn't connect to %s", remote.get_64bit_addr())

def send_message(message):
    setup_xbee()
    device.send_data(remote, message)
    print(f"Sending to {remote.get_64bit_addr()} >> {message}")
    device.close()

def send_in_loop():
    setup_xbee()
    DATA_TO_SEND = 0
    print(f"to {remote.get_64bit_addr()}")
    tries = 0

    while True:
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        message = current_time + ": Message " + str(DATA_TO_SEND)
        
        try:
            device.send_data(remote, message)
            print(f"{current_time} Sending >> Message {DATA_TO_SEND}")
            DATA_TO_SEND += 1
            time.sleep(1) #send every second
        except:
            if tries > 5:
                print("This connection ain't workin'")
                device.close()
                exit(2)
            device.close()
            setup_xbee()
            tries += 1

print("Starting")
send_message(DATA_TO_SEND)
send_in_loop()
