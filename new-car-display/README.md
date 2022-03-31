# Preliminary Solar Car Display
Chibueze Onyenemezu, 2021-2022

The display is a GUI made with Python's Tkinter library.
It reads from Receiver.py and constantly updates the values on the screen. *not included*

## Car Display
This the the root of the display. Initially, it opens in fullscreen mode but there is a button that toggles full screen. You can also use the escape key to toggle.
There are 2 frames: The main display (HomeFrame) and the gps display (gps_display). The program starts with HomeFrame and a button in that frame is used to switch to the other one.

## HomeFrame
The home frame shows the status of various values that may be of interest to the driver. Currently, we display velocity, cruise control status, CAN connection status, main current, main voltage, and the lowest voltage in the battery management system.
Home frame contains 2 frames: mainframe and info_frame. Mainframe (left) shows the velocity and gps display button. Info_frame (right) shows the rest of the statuses. Both frames use grid to postition and display their contents.

The updater() function calls a function in Receiver.py that returns the current values of the variables we want to change. It calls itself recursively every second. *not included*

## GPS Display
