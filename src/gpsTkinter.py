import tkinter as tk
import tkintermapview
import random

# Create Tkinter window
root = tk.Tk()
root.title("Real-Time GPS Tracking")

# Create map widget
map_widget = tkintermapview.TkinterMapView(root, width=800, height=600)
map_widget.pack()

# Set initial map view (e.g., NCM Motorsports Park location)
map_widget.set_position(37.0025, -86.3680)  # Longitude shifted to the right
map_widget.set_zoom(16)

# Create a marker for the GPS location
marker = map_widget.set_marker(37.0025, -86.3680, text="Car Position")

# Function to simulate GPS updates and update the map
def update_map():
    # Simulate some changes in latitude and longitude (replace with real GPS data)
    new_lat = 37.0025 + random.uniform(-0.0001, 0.0001)  # Simulated GPS data change
    new_lon = -86.3680 + random.uniform(-0.0005, 0.0005)  # Simulated GPS data change with larger shift

    # Update the marker position with the new GPS coordinates
    marker.set_position(new_lat, new_lon)

    # Update the map to reflect the new marker position
    map_widget.set_position(new_lat, new_lon)

    # Schedule the next update after 100 milliseconds (0.1s)
    root.after(100, update_map)

# Start the update process
update_map()

# Start the Tkinter mainloop
root.mainloop()