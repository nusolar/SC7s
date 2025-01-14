from typing import Literal
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
from tkinter import font
from tkdial import Meter

VIRTUAL_BUS_NAME = "virtual"

CAN_INTERFACE: Literal["virtual"] | Literal["canusb"] | Literal["pican"] = "virtual"
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD_RATE = 500000

WIDTH = 500
HEIGHT = 300
BCK_COLOR = "#1e1e2e"  # Your darker background
FG_COLOR = "#cdd6f4"   # Your softer text color
ACCENT_COLOR = "#89b4fa"  # Your highlight color
CANUSB_PORT = "/dev/ttyUSB0"

displayables = {"VehicleVelocity": 45.0,
                "Pack_SOC": 0.0,
                "Output_current": 0.0,
                "Avg_Opencell_Voltage": 0.0,
                "MotorTemp": 0.0,
                "Odometer": 0.0,
                "input_power1": 0.0,
                "input_power2": 0.0,
                "output_power1": 0.0,
                "output_power2": 0.0,
                "Low_array_power": 0,
                "Twelve_V": 45.0
}

class CarDisplay(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.title("NU Solar Car")
        self._frame = None
        self.switchFrame(HomeFrame)
        self.configure(background=BCK_COLOR)

        self.fullScreen = True
        self.attributes("-fullscreen", self.fullScreen)
        self.bind("<Escape>", self.toggleFullscreen)

        self.MyLeftPos = (self.winfo_screenwidth() - 500) / 2
        self.myTopPos = (self.winfo_screenheight() - 300) / 2
        self.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

        self.is_full = tk.StringVar()
        self.is_full.set("Exit Fullscreen")


        image = Image.open("src/logo.png")  # Update with the path to your image

        # Convert the image to a Tkinter-compatible format
        photo = ImageTk.PhotoImage(image)

        # Create a Label widget to display the image
        label = tk.Label(self, image=photo)
        label.pack(pady=10)

        # Keep a reference to the image (important to prevent garbage collection)
        label.image = photo


        fullscreen_btn = tk.Button(self, textvariable=self.is_full,
            command=self.toggleFullscreen, 
            font=("Inter", 12),
            bg=BCK_COLOR,
            fg=FG_COLOR,
            relief="flat",
            padx=10)
        fullscreen_btn.pack(side=tk.TOP, anchor=tk.NE, padx=20, pady=10)

    def toggleFullscreen(self, *args):
        self.fullScreen = not self.fullScreen
        self.attributes("-fullscreen", self.fullScreen)
        self.is_full.set("Exit Fullscreen" if self.fullScreen else "Fullscreen")
        self.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

    def switchFrame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.configure(background=BCK_COLOR)
        self._frame.pack(expand=True, fill=tk.BOTH)

class HomeFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        parent.configure(background=BCK_COLOR)
        self.bbox_charge = tk.StringVar(value="0.0")
        self.mppt_current = tk.StringVar(value="0.0")
        self.bboxvolt = tk.StringVar(value="0.0")
        self.motorc_temp = tk.StringVar(value="0.0")
        self.speed = tk.StringVar(value="0.0")
        self.efficiency = tk.StringVar(value="0.0")
        self.create_frames(parent)

    def create_frames(self, parent):
        self.mainframe = tk.Frame(self, bg=BCK_COLOR)
        self.info_frame = tk.Frame(self, bg=BCK_COLOR)

        # Updated meter with needle parameters
        self.meter1 = Meter(
            self.mainframe, 
            radius=450, 
            start=0, 
            end=80, 
            border_width=0, 
            integer=True,
            fg=ACCENT_COLOR, 
            text_color=FG_COLOR, 
            start_angle=195, 
            end_angle=-210,
            text_font="Inter 48", 
            scale_color=FG_COLOR, 
            needle_color="white",
            #needle_thickness=3,  # Adjust thickness of needle
            #needle_type="triangle",  # Can be "triangle" or "line"
            #display_text=False  # Hide the digital display on meter
        )
        self.meter1.grid(row=1, column=1, sticky=tk.N, padx=(0,650), pady=(0,300))

        # Rest of your original code for info display
        info_items = [
            ("Speed", self.speed, "mph"),
            ("Efficiency", self.efficiency, "mi/kWh"),
            ("Battery Charge", self.bbox_charge, "%"),
            ("Cell Current", self.mppt_current, "A"),
            ("Battery Voltage", self.bboxvolt, "V"),
            ("Motor Temp", self.motorc_temp, "°C"),
        ]

        for i, (label, var, unit) in enumerate(info_items):
            frame = tk.Frame(self.info_frame, bg=BCK_COLOR)
            frame.pack(fill=tk.X, pady=5)

            tk.Label(
                frame,
                text=label,
                font=("Inter", 24),
                bg=BCK_COLOR,
                fg=FG_COLOR
            ).pack(side=tk.LEFT)

            value_frame = tk.Frame(frame, bg=BCK_COLOR)
            value_frame.pack(side=tk.RIGHT)

            tk.Label(
                value_frame,
                textvariable=var,
                font=("Inter", 24, "bold"),
                bg=BCK_COLOR,
                fg=ACCENT_COLOR
            ).pack(side=tk.LEFT, padx=(0, 5))

            tk.Label(
                value_frame,
                text=unit,
                font=("Inter", 24),
                bg=BCK_COLOR,
                fg=FG_COLOR
            ).pack(side=tk.LEFT)

        # Grid configuration
        for i in range(2):
            self.info_frame.columnconfigure(i, weight=2)
        self.mainframe.columnconfigure(0, weight=1)

        for i in range(9):
            self.info_frame.rowconfigure(i, weight=1)

        self.mainframe.rowconfigure(0, weight=5)
        self.mainframe.rowconfigure(1, weight=2)
        self.mainframe.rowconfigure(2, weight=1)

        # Pack frames
        self.mainframe.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self.info_frame.pack(expand=False, fill=tk.BOTH, side=tk.RIGHT, padx=(0, 10))

        self.updater()

    def updater(self):
        self.meter1.set(displayables["Twelve_V"])
        self.speed.set(f"{displayables['VehicleVelocity']:.1f}")
        
        # Calculate efficiency
        total_power = displayables["input_power1"] + displayables["input_power2"]
        if total_power > 0:
            efficiency = displayables["VehicleVelocity"] / total_power
            self.efficiency.set(f"{efficiency:.1f}")
        else:
            self.efficiency.set("0.0")
            
        self.bbox_charge.set(f"{displayables['Low_array_power']:.1f}")
        self.mppt_current.set(f"{displayables['Output_current']:.1f}")
        self.bboxvolt.set(f"{displayables['Avg_Opencell_Voltage']:.1f}")
        self.motorc_temp.set(f"{displayables['MotorTemp']:.1f}")

        self.after(1000, self.updater)

    def register_updater(callback):
        pass
