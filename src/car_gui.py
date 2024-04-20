from typing import Literal

import tkinter as tk
from tkinter import ttk
from tkinter import font

from src.can.row import Row
from src.util import unwrap, find

VIRTUAL_BUS_NAME = "virtual"

CAN_INTERFACE: Literal["virtual"] | Literal["canusb"] | Literal["pican"] = "virtual"
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD_RATE = 500000

WIDTH = 500
HEIGHT = 300
BCK_COLOR = "#381b4d" #dark purple
FG_COLOR = "#ebebeb" #silver
CANUSB_PORT = "/dev/ttyUSB0"

class CarDisplay(tk.Tk):
    def __init__(self, rows: list[Row], *args, **kwargs):
        super().__init__()
        self.title("NU Solar Car")
        self._frame = None
        self.switchFrame(HomeFrame, rows)
        self.configure(background=BCK_COLOR, padx=15, pady=15)

        #Fullscreen
        self.fullScreen = True
        self.attributes("-fullscreen", self.fullScreen)
        self.bind("<Escape>", self.toggleFullscreen)

        #set center screen window with following coordinates
        #self is tk.Tk
        self.MyLeftPos = (self.winfo_screenwidth() - 500) / 2
        self.myTopPos = (self.winfo_screenheight() - 300) / 2
        self.geometry( "%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

        #full screen button
        self.is_full = tk.StringVar()
        self.is_full.set("Minimize") #initial text
        fullscreen_btn = tk.Button(self, textvariable=self.is_full,
            command = self.toggleFullscreen, font=("Helvetica", 15), height=2)
        fullscreen_btn.pack(side=tk.TOP, anchor=tk.NW)

    #for toggling full screen with esc
    def toggleFullscreen(self, *args):
        self.fullScreen = not self.fullScreen
        self.attributes("-fullscreen", self.fullScreen)

        #set button text
        if self.fullScreen == True:
            self.is_full.set("Minimize")
        else:
            self.is_full.set("Full Screen")

        #center window
        self.geometry( "%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

    def switchFrame(self, frame_class, rows: list[Row]):
        new_frame = frame_class(self, rows)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.configure(background=BCK_COLOR)
        self._frame.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)


class HomeFrame(tk.Frame):
    def __init__(self, parent, rows: list[Row]):
        tk.Frame.__init__(self, parent)
        parent.configure(background=BCK_COLOR)
        #all stringvars
        self.speed = tk.StringVar(value= "0.0")
        self.bbox_charge = tk.StringVar(value= "0.0")
        # self.bbox_avgtemp = StringVar(value= "0.0")
        # self.bbox_maxtemp = StringVar(value= "0.0")
        self.mppt_current = tk.StringVar(value= "0.0")
        self.bboxvolt = tk.StringVar(value= "0.0")
        # self.regen_enabled = StringVar(value= "0.0")
        # self.odometer = StringVar(value= "0.0")
        # self.vehicle_direction = StringVar(value= "0.0")
        self.motorc_temp = tk.StringVar(value= "0.0")

        self.create_frames(parent)
        self.updater(rows)


    def create_frames(self, parent):
        #frame that shows the velocity and buttons
        self.i = 0
        self.mainframe = tk.Frame(self, bg=BCK_COLOR)

        #frame with all the deets
        self.info_frame = tk.Frame(self, bg=BCK_COLOR)

        #font styles
        info_font = ("Helvetica", 20, "bold")
        vel_font = ("Helvetica", 160, "bold", "italic")
        custom_font = font.Font(family=vel_font[0], size=vel_font[1], weight=vel_font[2], slant=vel_font[3])
        #velocity label
        speed_label = ttk.Label(self.mainframe, textvariable=self.speed,
            font=custom_font, background=BCK_COLOR, foreground=FG_COLOR)
        speed_label.grid(column=0, row=0, sticky=tk.S)

        #mph label
        units_label = ttk.Label(self.mainframe, text="MPH", font=custom_font,
            background=BCK_COLOR, foreground=FG_COLOR)
        units_label.grid(column=0, row=1, sticky=tk.N, padx=(0, 300))


        #info labels
        #battery box charge
        bbox_charge_label = ttk.Label(self.info_frame, text = "Bbox Charge:", font = info_font)
        bbox_charge_label.grid(column = 0, row = 0, sticky = tk.W)

        bbox_charge_status = ttk.Label(self.info_frame, textvariable = self.bbox_charge, font = info_font)
        bbox_charge_status.grid(column = 1, row = 0, sticky = tk.E)

        #batter box average temp
        # bbox_avgtemp_label = ttk.Label(self.info_frame, text = "Bbox Average Temp:", font = info_font)
        # bbox_avgtemp_label.grid(column = 0, row = 1, sticky = W)

        # bbox_avgtemp_status = ttk.Label(self.info_frame, textvariable = self.bbox_avgtemp, font = info_font)
        # bbox_avgtemp_status.grid(column = 1, row = 1, sticky = E)

        #battery box max temp
        # bbox_maxtemp_label = ttk.Label(self.info_frame, text = "Bbox Max Temp:", font = info_font)
        # bbox_maxtemp_label.grid(column = 0, row = 2, sticky = W)

        # bbox_maxtemp_status = ttk.Label(self.info_frame, textvariable = self.bbox_maxtemp, font = info_font)
        # bbox_maxtemp_status.grid(column = 1, row = 2, sticky = E)

        #current out from cells
        mppt_current_label = ttk.Label(self.info_frame, text = "Current out from Cells:", font = info_font)
        mppt_current_label.grid(column = 0, row = 3, sticky = tk.W)

        mppt_current_status = ttk.Label(self.info_frame, textvariable = self.mppt_current, font = info_font)
        mppt_current_status.grid(column = 1, row = 3, sticky = tk.E)

        #secondary voltage of battery box
        bboxvolt_label = ttk.Label(self.info_frame, text = "Secondary Voltage of Battery Box:", font = info_font)
        bboxvolt_label.grid(column = 0, row = 4, sticky = tk.W)

        bboxvolt_status = ttk.Label(self.info_frame, textvariable = self.bboxvolt, font = info_font)
        bboxvolt_status.grid(column = 1, row = 4, sticky = tk.E)

        #regen enabled?
        # regen_enabled_label = ttk.Label(self.info_frame, text = "Regen Enable?", font = info_font)
        # regen_enabled_label.grid(column = 0, row = 5, sticky = W)

        # regen_enabled_status = ttk.Label(self.info_frame, textvariable = self.regen_enabled, font = info_font)
        # regen_enabled_status.grid(column = 1, row = 5, sticky = E)

        #distance traveled
        # odometer_label = ttk.Label(self.info_frame, text = "Distance Traveled:", font = info_font)
        # odometer_label.grid(column = 0, row = 6, sticky = W)
   
        # odometer_status = ttk.Label(self.info_frame, textvariable = self.odometer, font = info_font)
        # odometer_status.grid(column = 1, row = 6, sticky = E)

        #direction of vehicle
        # vehicle_direction_label = ttk.Label(self.info_frame, text = "Direction of Vehicle:", font = info_font)
        # vehicle_direction_label.grid(column = 0, row = 7, sticky = W)

        # vehicle_direction_status = ttk.Label(self.info_frame, textvariable = self.vehicle_direction, font = info_font)
        # vehicle_direction_status.grid(column = 1, row = 7, sticky = E)

        #motor controller temperature
        motorc_temp_label = ttk.Label(self.info_frame, text = "Motor Controller Temperature:", font = info_font)
        motorc_temp_label.grid(column = 0, row = 8, sticky = tk.W)

        motorc_temp_status = ttk.Label(self.info_frame, textvariable = self.motorc_temp, font = info_font)
        motorc_temp_status.grid(column = 1, row = 8, sticky = tk.E)

        
        #set color
        for child in self.info_frame.winfo_children():
            child.configure(background=BCK_COLOR, foreground=FG_COLOR) # type: ignore

        #space out columns
        for ii in range(2):
            self.info_frame.columnconfigure(ii, weight=2)

        self.mainframe.columnconfigure(0, weight=1)

        #space out rows
        for ii in range(9):
            self.info_frame.rowconfigure(ii, weight=1)

        self.mainframe.rowconfigure(0, weight=5) #make velocity box biggest
        self.mainframe.rowconfigure(1, weight=2) #make mph second biggest
        self.mainframe.rowconfigure(2, weight=1) #button is smallest

        #pack statements
        #expand - add extra available space
        #padx = (left, right)
        self.mainframe.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self.info_frame.pack(expand=False, fill=tk.BOTH, side=tk.RIGHT, padx=(0, 10))


    def updater(self, rows: list[Row]):
        # call the registered callback function

        mppt_0x600 = unwrap(find(rows, lambda r: r.name == "MPPT_0x600"))
        mc_0x400 = unwrap(find(rows, lambda r: r.name == "MOTOR_CONTROLLER_0x400"))

        self.speed.set(round(mc_0x400.signals["VehicleVelocity"].value, 3)) # type: ignore
        breakpoint()
        self.bbox_charge.set(round(mppt_0x600.signals["Low_array_power"].value, 3)) # type: ignore
        # self.bbox_avgtemp.set(round(displayables["bbox_avgtemp"], 3))
        # self.bbox_maxtemp.set(round(displayables["bbox_maxtemp"], 3))
        self.mppt_current.set(str(round(mppt_0x600.signals["Output_current"].value, 3))) #type: ignore
        self.bboxvolt.set(round(mc_0x400.signals["Avg_Opencell_Voltage"].value, 3)) #type: ignore 
        # self.regen_enabled.set(round(displayables["regen_enabled"], 3))
        # self.odometer.set(round(displayables["Odometer"], 3))
        # self.vehicle_direction.set(round(displayables["vehicle_direction"], 3))
        self.motorc_temp.set(round(mc_0x400.signals["MotorTemp"].value, 3)) #type: ignore 

        self.after(1000, self.updater, rows)



def register_updater(callback):
    ...
