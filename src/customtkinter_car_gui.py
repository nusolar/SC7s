import customtkinter as ctk
from customtkinter import BOTH, BOTTOM, E, LEFT, N, NW, RIGHT, S, SE, TOP, W
from typing import Literal
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkdial import Meter
VIRTUAL_BUS_NAME = 'virtual'
CAN_INTERFACE: Literal['virtual'] | Literal['canusb'] | Literal['pican'] = 'virtual'
SERIAL_PORT = '/dev/ttyUSB0'
SERIAL_BAUD_RATE = 500000
WIDTH = 500
HEIGHT = 300
BCK_COLOR = '#381b4d'
FG_COLOR = '#ebebeb'
CANUSB_PORT = '/dev/ttyUSB0'
displayables = {'VehicleVelocity': 0.0, 'Pack_SOC': 0.0, 'Output_current': 0.0, 'Avg_Opencell_Voltage': 0.0, 'MotorTemp': 0.0, 'Odometer': 0.0, 'input_power1': 0.0, 'input_power2': 0.0, 'output_power1': 0.0, 'output_power2': 0.0, 'Low_array_power': 0}

class CarDisplay(ctk.CTk):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.title('NU Solar Car')
        self._frame = None
        self.switchFrame(HomeFrame)
        self.configure(background=BCK_COLOR, padx=15, pady=15)
        self.fullScreen = True
        self.attributes('-fullscreen', self.fullScreen)
        self.bind('<Escape>', self.toggleFullscreen)
        self.MyLeftPos = (self.winfo_screenwidth() - 500) / 2
        self.myTopPos = (self.winfo_screenheight() - 300) / 2
        self.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))
        self.is_full = ctk.StringVar()
        self.is_full.set('Minimize')
        fullscreen_btn = ctk.CTkButton(self, textvariable=self.is_full, command=self.toggleFullscreen, font=('Helvetica', 15), height=2)
        fullscreen_btn.pack(side=tk.TOP, anchor=tk.NW)

    def toggleFullscreen(self, *args):
        self.fullScreen = not self.fullScreen
        self.attributes('-fullscreen', self.fullScreen)
        if self.fullScreen == True:
            self.is_full.set('Minimize')
        else:
            self.is_full.set('Full Screen')
        self.geometry('%dx%d+%d+%d' % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

    def switchFrame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.configure(background=BCK_COLOR)
        self._frame.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)

class HomeFrame(ctk.CTkFrame):

    def __init__(self, parent):
        ctk.CTkFrame.__init__(self, parent)
        parent.configure(background=BCK_COLOR)
        self.speed = ctk.StringVar(value='0.0')
        self.bbox_charge = ctk.StringVar(value='0.0')
        self.mppt_current = ctk.StringVar(value='0.0')
        self.bboxvolt = ctk.StringVar(value='0.0')
        self.motorc_temp = ctk.StringVar(value='0.0')
        self.create_frames(parent)
        self.updater()

    def create_frames(self, parent):
        self.i = 0
        self.mainframe = ctk.CTkFrame(self, bg_color=BCK_COLOR)
        self.info_frame = ctk.CTkFrame(self, bg_color=BCK_COLOR)
        info_font = ('Helvetica', 20, 'bold')
        vel_font = ('Helvetica', 160, 'bold', 'italic')
        custom_font = ctk.CTkFont(family=vel_font[0], size=vel_font[1], weight=vel_font[2], slant=vel_font[3])
        speed_label = ctk.CTkLabel(self.mainframe, textvariable=self.speed, font=custom_font, background=BCK_COLOR, foreground=FG_COLOR)
        speed_label.grid(column=0, row=0, sticky=tk.S)
        meter1 = Meter(radius=900, start=0, end=80, border_width=0, integer=True, fg='black', text_color='white', start_angle=195, end_angle=-210, text_font='DS-Digital 100', scale_color='white', needle_color='purple')
        meter1.set_mark(60, 81)
        meter1.grid(row=0, column=1, sticky=tk.n, padx=(0, 300))
        bbox_charge_label = ctk.CTkLabel(self.info_frame, text='Bbox Charge:', font=info_font)
        bbox_charge_label.grid(column=0, row=0, sticky=tk.W)
        bbox_charge_status = ctk.CTkLabel(self.info_frame, textvariable=self.bbox_charge, font=info_font)
        bbox_charge_status.grid(column=1, row=0, sticky=tk.E)
        mppt_current_label = ctk.CTkLabel(self.info_frame, text='Current out from Cells:', font=info_font)
        mppt_current_label.grid(column=0, row=3, sticky=tk.W)
        mppt_current_status = ctk.CTkLabel(self.info_frame, textvariable=self.mppt_current, font=info_font)
        mppt_current_status.grid(column=1, row=3, sticky=tk.E)
        bboxvolt_label = ctk.CTkLabel(self.info_frame, text='Secondary Voltage of Battery Box:', font=info_font)
        bboxvolt_label.grid(column=0, row=4, sticky=tk.W)
        bboxvolt_status = ctk.CTkLabel(self.info_frame, textvariable=self.bboxvolt, font=info_font)
        bboxvolt_status.grid(column=1, row=4, sticky=tk.E)
        motorc_temp_label = ctk.CTkLabel(self.info_frame, text='Motor Controller Temperature:', font=info_font)
        motorc_temp_label.grid(column=0, row=8, sticky=tk.W)
        motorc_temp_status = ctk.CTkLabel(self.info_frame, textvariable=self.motorc_temp, font=info_font)
        motorc_temp_status.grid(column=1, row=8, sticky=tk.E)
        for child in self.info_frame.winfo_children():
            child.configure(background=BCK_COLOR, foreground=FG_COLOR)
        for ii in range(2):
            self.info_frame.columnconfigure(ii, weight=2)
        self.mainframe.columnconfigure(0, weight=1)
        for ii in range(9):
            self.info_frame.rowconfigure(ii, weight=1)
        self.mainframe.rowconfigure(0, weight=5)
        self.mainframe.rowconfigure(1, weight=2)
        self.mainframe.rowconfigure(2, weight=1)
        self.mainframe.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self.info_frame.pack(expand=False, fill=tk.BOTH, side=tk.RIGHT, padx=(0, 10))

    def updater(self):
        self.speed.set(round(displayables['VehicleVelocity'], 3))
        self.bbox_charge.set(round(displayables['Low_array_power'], 3))
        self.mppt_current.set(str(round(displayables['Output_current'], 3)))
        self.bboxvolt.set(round(displayables['Avg_Opencell_Voltage'], 3))
        self.motorc_temp.set(round(displayables['MotorTemp'], 3))
        self.after(1000, self.updater)

def register_updater(callback):
    ...