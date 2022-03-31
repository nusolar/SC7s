import tkinter as tk
from tkinter import ttk

#import gps frame that's in same folder
import solar_car_display

BACK_COLOR = "#381b4d" #dark purple
FRG_COLOR = "#ebebeb" #silver

class gps_display(tk.Frame):
    def __init__(self, parent):

        tk.Frame.__init__(self, parent)
        parent.configure(background=BACK_COLOR)
        self.configure(background=BACK_COLOR)
        self.parent = parent
        
        #font styles
        info_font = ("Helvetica", 12, "bold", "italic")
        vel_font = ("Helvetica", 60, "bold", "italic")
        btn_font = ("Helvetica", 20, "bold")
        
        #for now, use canvas for grid
        canvas = tk.Canvas(self, width=30, height=5, background="black")
        
        #container for bottom
        container = tk.Frame(self, bg=BACK_COLOR)
        
        #speed label
        self.vel = tk.StringVar()
        self.vel.set(28.6)
        self.vel_label = tk.Label(container, textvariable=self.vel, font=vel_font,
            background=BACK_COLOR, foreground=FRG_COLOR)
        
        #mph label
        self.mph_label = tk.Label(container, text="MPH", font=info_font,
            background=BACK_COLOR, foreground=FRG_COLOR)
        
        #back button
        self.home_btn = tk.Button(container, text="Main", font=btn_font, width=10, height=2,
            command = lambda: parent.switchFrame(solar_car_display.HomeFrame))

        #make elements appear
        canvas.pack(expand=True, side="top", fill="both", pady=10)
        self.home_btn.pack(side="left", anchor="s")
        self.mph_label.pack(side="right", anchor="s", pady=(0, 15), padx=10)
        self.vel_label.pack(side="right", anchor="s")
        container.pack(fill="x", side=tk.BOTTOM)