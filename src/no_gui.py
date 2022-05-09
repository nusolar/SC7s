from receiver import Receiver

r = Receiver(serial_port='/dev/tty.usbserial-AC00QTXJ')

for item in r.get_packets():
    print(item)
