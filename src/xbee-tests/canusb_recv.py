import serial

#Initialize fields
serial_port = 'COM4'
baud_rate = 57600

#f = open("output_can.txt", "x")

with serial.Serial(serial_port, baud_rate) as receiver:
    while(True):
        raw = receiver.read_until(b';').decode()
        #outputs :S40ENBF49753D00000000;
        print(raw)
        #f.write(raw.replace(":", "") + "\n")
    #f.close()