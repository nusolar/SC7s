from receiver import Receiver

r = Receiver()

for item in r.get_packets():
    print(item)
