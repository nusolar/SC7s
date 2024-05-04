from pathlib import Path
import cantools.database
import can
from cantools.database.can.database import Database
from src import ROOT_DIR
from src.util import add_dbc_file
from src.can.virtual import start_virtual_can_bus
from cantools.typechecking import SignalDictType

import customtkinter
import random
from tkdial import Meter
from time import sleep
from math import sin

from threading import Thread
from typing import NoReturn, cast

VIRTUAL_BUS_NAME = "virtbus"

# The database used for parsing with cantools
db = cast(Database, cantools.database.load_file(Path(ROOT_DIR).joinpath("resources", "mppt.dbc")))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "motor_controller.dbc"))
add_dbc_file(db, ROOT_DIR.joinpath("resources", "driver_controls.dbc"))

start_virtual_can_bus(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"), db)

displayables = {
    "Twelve_V": 0.0
}

# test_speed = 0

# def update_meter():
#     # meter1.set(displayables["Twelve_V"])
#     # print(displayables["Twelve_V"])
#     if test_speed < 80:
#         test_speed += 0.5
#     app.after(10, update_meter)  # 10 milliseconds delay

app = customtkinter.CTk()
app.geometry("950x950")

meter1 = Meter(app, radius=900, start=0, end=80, border_width=0, integer=True,
               fg="black", text_color="white", start_angle=195, end_angle=-210,
               text_font="DS-Digital 100", scale_color="white", needle_color="purple")
meter1.set_mark(60, 81) # set red marking from 60 to 80
meter1.grid(row=0, column=1, padx=20, pady=30)

# def reverse_meter(test_speed):
#     print('we got here')
#     if test_speed > 0:
#         test_speed -= 0.25
#         app.after(10, reverse_meter, test_speed)

def update_meter():
    meter1.set(displayables["Twelve_V"])
    app.after(10, update_meter)  # 10 milliseconds delay
    # else:
    #     reverse_meter(test_speed)

def update_speed(bus: can.ThreadSafeBus) -> NoReturn:
    while True:
        msg = bus.recv()
        if msg.arbitration_id == 0x603:
            decoded = cast(SignalDictType, db.decode_message(msg.arbitration_id, msg.data))
            displayables["Twelve_V"] = decoded["Twelve_V"]

#meter1.set(20)
test_speed = 0
# while(test_speed <= 80):
#     meter1.set(test_speed)
#     test_speed += 0.5
#     print(test_speed)
#     sleep(0.01)

update_meter()

updater = Thread(target=update_speed, args=(can.ThreadSafeBus(VIRTUAL_BUS_NAME, bustype="virtual"),), daemon=True)
updater.start()

app.mainloop()
# print("test")
# test_speed = 0
# sleep(1)
# while(test_speed <= 80):
#     meter1.set(test_speed)
#     test_speed += 0.5
#     print(test_speed)
#     sleep(0.01)