import tkinter as tk
import tkintermapview
import random
from tkinter import ttk
from tkinter import font
from tkdial import Meter  # Assuming you want to keep this import for Meter control
from typing import Literal
from PIL import Image, ImageTk  # Ensure you have this imported at the top of your script

# Global dictionary for displayables (including GPS data)
displayables = {
    "VehicleVelocity": 0.0,
    "Pack_SOC": 0.0,
    "Output_current": 0.0,
    "Avg_Opencell_Voltage": .0,
    "MotorTemp": 0.0,
    "BboxTemp":0.0, #electrical said they'll get us this
    "Odometer": 0.0,
    "input_power1": 0.0,
    "input_power2": 0.0,
    "output_power1": 0.0,
    "output_power2": 0.0,
    "Low_array_power": 0.0,
    "latitude": 37.0025,  # Preset latitude
    "longitude": -86.3680,  # Preset longitude
    "distance_traveled": 0.0  # Initial distance traveled
}

WIDTH = 500
HEIGHT = 300
BCK_COLOR = "#341539"
FG_COLOR = "#ffeaff"
FONT= ("Cooper Std Black", 20)
LARGE_FONT= ("Cooper Std Black", 40)

class CarDisplay(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.title("NU Solar Car")
        self._frame = None
        self.switchFrame(HomeFrame)
        self.configure(background=BCK_COLOR, padx=15, pady=15)

        # Fullscreen
        self.fullScreen = True
        self.attributes("-fullscreen", self.fullScreen)
        self.bind("<Escape>", self.toggleFullscreen)

        # Set center screen window with following coordinates
        self.MyLeftPos = (self.winfo_screenwidth() - 500) / 2
        self.myTopPos = (self.winfo_screenheight() - 300) / 2
        self.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

        # Full screen button
        self.is_full = tk.StringVar()
        self.is_full.set("Minimize")  # initial text
        fullscreen_btn = tk.Button(self, textvariable=self.is_full,
                                   command=self.toggleFullscreen, font=FONT, height=2)
        fullscreen_btn.pack(side=tk.TOP, anchor=tk.NW)

    def toggleFullscreen(self, *args):
        self.fullScreen = not self.fullScreen
        self.attributes("-fullscreen", self.fullScreen)

        # Set button text
        if self.fullScreen:
            self.is_full.set("Minimize")
        else:
            self.is_full.set("Full Screen")

        # Center window
        self.geometry("%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

    def switchFrame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.configure(background=BCK_COLOR)
        self._frame.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)


class HomeFrame(tk.Frame):
    def __init__(self, parent):
        tk.Frame.__init__(self, parent)
        parent.configure(background=BCK_COLOR)
        self.speed = tk.StringVar(value="0.0")
        self.bbox_charge = tk.StringVar(value="0.0")
        self.mppt_current = tk.StringVar(value="0.0")
        self.bboxTemp = tk.StringVar(value="0.0")
        self.motorc_temp = tk.StringVar(value="0.0")
        self.distance_traveled = tk.StringVar(value="0.0")

        self.create_frames(parent)
        self.updater()

        # Create the map widget for GPS in the upper right quarter
        self.create_map_widget()

    def create_frames(self, parent):
        self.i = 0
        self.mainframe = tk.Frame(self, bg=BCK_COLOR)
        # Configure mainframe rows and columns to ensure full stretching
        self.mainframe.columnconfigure(2, weight=1)  # Ensure the rightmost column stretches
        for col in range(5):
            self.mainframe.columnconfigure(col, weight=1)


        # Frame with all the deets
        self.info_frame = tk.Frame(self, bg=BCK_COLOR)

        # Velocity and MPH label
        """         speed_label = ttk.Label(self.mainframe, textvariable=self.speed,
            font=custom_font, background=BCK_COLOR, foreground=FG_COLOR)
        speed_label.grid(column=0, row=0, sticky=tk.S)

        units_label = ttk.Label(self.mainframe, text="MPH", font=("Helvetica", 40, "italic"),
            background=BCK_COLOR, foreground=FG_COLOR)
        units_label.grid(column=0, row=1, sticky=tk.N) """

        # Info labels
        
        #bbox_charge_label = ttk.Label(self.info_frame, text="Bbox Charge:", font=info_font)
        #bbox_charge_label.grid(column=0, row=0, sticky=tk.W)

        #bbox_charge_status = ttk.Label(self.info_frame, textvariable=self.bbox_charge, font=info_font)
        #bbox_charge_status.grid(column=1, row=0, sticky=tk.E)

        # Space out columns
        for ii in range(2):
            self.info_frame.columnconfigure(ii, weight=2)

        self.mainframe.columnconfigure(0, weight=1)

        # Space out rows
        for ii in range(9):
            self.info_frame.rowconfigure(ii, weight=1)

        self.mainframe.rowconfigure(0, weight=5)  # make velocity box biggest
        self.mainframe.rowconfigure(1, weight=2)  # make mph second biggest

        # Pack statements
        self.mainframe.pack(expand=True, fill=tk.BOTH, side=tk.LEFT)
        self.info_frame.pack(expand=False, fill=tk.BOTH, side=tk.RIGHT, padx=(0, 10))

        # Load the image
        image = Image.open("nusolarLogo.png")  # Replace with your image file path
        image = image.resize((400, 100))  # Resize the image as needed
        photo = ImageTk.PhotoImage(image)

        # Create a label for the image
        image_label = tk.Label(self.mainframe, image=photo, bg=BCK_COLOR)
        image_label.image = photo  # Keep a reference to avoid garbage collection

        # Place the image in the lower-left corner
        image_label.grid(row=2, column=0, sticky=tk.NSEW, padx=50, pady=10)

        # Meter Control (similar to what was in your original code for displaying vehicle velocity)
        """meter1 = Meter(self.mainframe, radius=550, start=0, end=80, border_width=0, integer=True, fg='black', text_color='white', start_angle=195, end_angle=-210, text_font='DS-Digital 100', scale_color='white', needle_color='purple')
        meter1.set_mark(60, 81)
        meter1.grid(row=0, column=0, sticky=tk.NW, padx=(100, 100), pady=(10, 10))"""
        
        # Meter Frame
        meter_frame = tk.Frame(self.mainframe, bg=BCK_COLOR)
        meter_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, padx=10, pady=10)  # Place in row 0, column 2

        # Create the meter widget inside the meter_frame
        meter = Meter(
            meter_frame,
            radius=550,
            start=0,
            end=80,
            border_width=0,
            integer=True,
            fg="black",
            text_color="white",
            start_angle=195,
            end_angle=-210,
            text_font="DS-Digital 100",
            scale_color="white",
            needle_color="purple",
        )
        meter.set_mark(60, 81)  # Set markers as needed
        meter.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)  # Pack within the frame

                
        # Add this function to dynamically update the battery widget
        def update_battery(canvas, actual_value, normalized_value):
            canvas.delete("all")  # Clear previous drawings

            # Battery outline
            canvas.create_rectangle(10, 10, 110, 60, outline=FG_COLOR, width=3)

            # Battery tip
            canvas.create_rectangle(110, 25, 120, 45, outline=FG_COLOR, fill=FG_COLOR)

            # Battery fill based on normalized charge level
            fill_width = (normalized_value / 100) * 100  # Scale to the width of the battery
            canvas.create_rectangle(10, 10, 10 + fill_width, 60, outline="", fill="#4caf50")  # Green fill

        # Battery Frame
        battery_frame = tk.Frame(self.mainframe, bg=BCK_COLOR)
        battery_canvas = tk.Canvas(battery_frame, width=120, height=70, bg=BCK_COLOR, highlightthickness=0)
        battery_canvas.grid(row=0, column=0, padx=10, pady=10)

        # Battery level text below the canvas
        battery_level_label = ttk.Label(
            battery_frame,
            textvariable=self.bbox_charge,
            font=LARGE_FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        battery_level_label.grid(row=1, column=0, padx=10, pady=5)
        battery_frame.grid(row=2, column=4, sticky=tk.SW, padx=0, pady=10)
        
        low_array_power_text_label = ttk.Label(
            battery_frame,
            text="Battery Level",
            font=FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        low_array_power_text_label.grid(row=2, column=0, padx=10)

        # Schedule updates for the battery widget
        def schedule_battery_update():
            actual_value = displayables["Low_array_power"]  # Actual power value
            normalized_value = min(max(actual_value, 0), 100)  # Normalize to 0-100
            self.bbox_charge.set(f"{actual_value:.1f}")  # Show actual value as text
            update_battery(battery_canvas, actual_value, normalized_value)
            self.after(500, schedule_battery_update)  # Update every 500ms

        schedule_battery_update()
        
        # Motor Controller Temperature Widget
        motor_temp_frame = tk.Frame(self.mainframe, bg=BCK_COLOR)
        self.motor_temp_canvas = tk.Canvas(motor_temp_frame, width=70, height=200, bg=BCK_COLOR, highlightthickness=0)
        self.motor_temp_canvas.grid(row=0, column=0, padx=10, pady=10)

        motor_temp_label = ttk.Label(
            motor_temp_frame,
            textvariable=self.motorc_temp,
            font=LARGE_FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        motor_temp_label.grid(row=1, column=0, padx=10, pady=5)

        motor_temp_text_label = ttk.Label(
            motor_temp_frame,
            text="MC Temp",
            font=FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        motor_temp_text_label.grid(row=2, column=0, padx=10)
        motor_temp_frame.grid(row=2, column=1, sticky=tk.NSEW, padx=50, pady=10)
        
        
        # Battery Box Temperature Widget
        battery_temp_frame = tk.Frame(self.mainframe, bg=BCK_COLOR)
        self.battery_temp_canvas = tk.Canvas(battery_temp_frame, width=70, height=200, bg=BCK_COLOR, highlightthickness=0)
        self.battery_temp_canvas.grid(row=0, column=0, padx=10, pady=10)

        battery_temp_label = ttk.Label(
            battery_temp_frame,
            textvariable=self.bboxTemp,  # Assuming "BatteryBoxTemp" will be stored in "bboxvolt"
            font=LARGE_FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        battery_temp_label.grid(row=1, column=0, padx=10, pady=5)

        battery_temp_text_label = ttk.Label(
            battery_temp_frame,
            text="BBox Temp",
            font=FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        battery_temp_text_label.grid(row=2, column=0, padx=10)
        battery_temp_frame.grid(row=2, column=2, sticky=tk.NSEW, padx=50, pady=10)
        
        # Current Level Frame
        current_level_frame = tk.Frame(self.mainframe, bg=BCK_COLOR)
        # Canvas for current level visualization
        self.current_level_canvas = tk.Canvas(current_level_frame, width=70, height=200, bg=BCK_COLOR, highlightthickness=0)
        self.current_level_canvas.grid(row=0, column=0, padx=10, pady=10)

        # Label for current level value
        current_level_label = ttk.Label(
            current_level_frame,
            textvariable=self.mppt_current,  # Output current value
            font=LARGE_FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        current_level_label.grid(row=1, column=0, padx=10, pady=5)
        current_level_frame.grid(row=2, column=3, sticky=tk.NSEW, padx=50, pady=10)

        # Label for widget description
        current_level_text_label = ttk.Label(
            current_level_frame,
            text="Current Level",
            font=FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        current_level_text_label.grid(row=2, column=0, padx=10)

        
        self.update_motor_temp()
        self.update_battery_temp()
        self.update_current_level()
        
    def update_motor_temp(self):
        temp_level = min(max(float(self.motorc_temp.get()), 0), 200)  # Clamp temperature between 0 and 200
        fill_height = (temp_level / 200) * 200  # Normalize fill height based on canvas size

        self.motor_temp_canvas.delete("all")  # Clear existing drawing
        self.motor_temp_canvas.create_rectangle(
            15, 200 - fill_height, 55, 200, fill="#FF4500", outline=""  # Orange fill
        )
        self.motor_temp_canvas.create_rectangle(
            15, 0, 55, 200, outline=FG_COLOR, width=2  # Border
        )
        self.after(500, self.update_motor_temp)  # Schedule updates every 500ms
        
        
    def update_battery_temp(self):
        temp_level = min(max(float(self.bboxTemp.get()), 0), 150)  # Clamp temperature between 0 and max temp (150)
        fill_height = (temp_level / 150) * 200  # Normalize height for canvas size

        self.battery_temp_canvas.delete("all")  # Clear previous drawings
        self.battery_temp_canvas.create_rectangle(
            15, 200 - fill_height, 55, 200, fill="#FF4500", outline=""  # Orange fill
        )
        self.battery_temp_canvas.create_rectangle(
            15, 0, 55, 200, outline=FG_COLOR, width=2  # Border
        )
        self.after(500, self.update_battery_temp)  # Schedule updates every 500ms
        
    def update_current_level(self):
        current_value = min(max(float(displayables["Output_current"]), 0), 100)  # Clamp between 0 and 100
        fill_height = (current_value / 100) * 200  # Normalize to canvas height

        self.current_level_canvas.delete("all")  # Clear previous drawings
        self.current_level_canvas.create_rectangle(
            15, 200 - fill_height, 55, 200, fill="#4caf50", outline=""  # Green fill
        )
        self.current_level_canvas.create_rectangle(
            15, 0, 55, 200, outline=FG_COLOR, width=2  # Border
        )

        self.after(500, self.update_current_level)  # Update every 500ms
        
    
    def create_map_widget(self):
        # Create a frame to hold the map
        self.map_frame = tk.Frame(self.mainframe, bg=BCK_COLOR, width=800, height=500)
        self.map_frame.grid(row=0, column=3, columnspan=2, sticky=tk.NSEW, padx=10, pady=10)

        # Create Tkinter map widget
        self.map_widget = tkintermapview.TkinterMapView(self.map_frame, width=800, height=500)
        self.map_widget.pack(expand=True, fill=tk.BOTH)

        # Set initial map view based on displayables
        self.map_widget.set_position(displayables["latitude"], displayables["longitude"])
        self.map_widget.set_zoom(16)

        # Create a marker for the GPS location
        self.marker = self.map_widget.set_marker(displayables["latitude"], displayables["longitude"], text="Car Position")

        # Add labels for distance traveled
        units_label = ttk.Label(
            self.map_frame,
            text="Miles Traveled",
            font=FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        units_label.pack(side=tk.BOTTOM)

        distance_label = ttk.Label(
            self.map_frame,
            textvariable=self.distance_traveled,
            font=LARGE_FONT,
            background=BCK_COLOR,
            foreground=FG_COLOR,
        )
        distance_label.pack(side=tk.BOTTOM, pady=10)

        # Function to simulate GPS updates and update the map
        def update_map():
            new_lat = displayables["latitude"] + random.uniform(-0.0001, 0.0001)  # Simulated GPS data change
            new_lon = displayables["longitude"] + random.uniform(-0.0005, 0.0005)  # Simulated GPS data change with larger shift

            # Calculate distance traveled (simplified, for demonstration purposes)
            delta_lat = abs(new_lat - displayables["latitude"])
            delta_lon = abs(new_lon - displayables["longitude"])
            distance_increment = (delta_lat**2 + delta_lon**2)**0.5 * 69  # Approximate miles per degree

            displayables["distance_traveled"] += distance_increment
            self.distance_traveled.set(f"{displayables['distance_traveled']:.2f}")

            # Update the displayables with new coordinates
            displayables["latitude"] = new_lat
            displayables["longitude"] = new_lon

            # Update the marker position
            self.marker.set_position(new_lat, new_lon)
            self.map_widget.set_position(new_lat, new_lon)  # Update the map to reflect the new marker position

            self.after(100, update_map)  # Update every 100 ms

        # Start the GPS update loop
        update_map()


    def updater(self):
        # Update the variables based on displayables
        self.speed.set(round(displayables["VehicleVelocity"], 3))  # type: ignore
        self.bbox_charge.set(round(displayables["Low_array_power"], 3))  # type: ignore
        self.mppt_current.set(str(round(displayables["Output_current"], 3)))  # type: ignore
        self.bboxTemp.set(round(displayables["BboxTemp"], 3))  # type: ignore
        self.motorc_temp.set(round(displayables["MotorTemp"], 3))  # type: ignore
        self.after(1000, self.updater)

# Start the app
def main():
    app = CarDisplay()
    app.mainloop()

if __name__ == "__main__":
    main()
