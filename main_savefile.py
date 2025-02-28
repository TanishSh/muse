#!/usr/bin/env python3
from datetime import datetime
import signal
import sys
from pythonosc import dispatcher
from pythonosc import osc_server

# Settings
ip = "0.0.0.0"
port = 5001
filePath = 'OSC-Python-Recording.csv'

# Write CSV header immediately
with open(filePath, 'w') as f:
    header = "TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,Right_AUX,Left_AUX,Marker\n"
    f.write(header)
print("CSV header written to", filePath)

# Global variable to store the last EEG reading (if needed for repeating rows)
last_eeg = None

def eeg_handler(address: str, *args):
    global last_eeg
    # Always record each EEG OSC message as soon as it's received
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # Build CSV row: timestamp, EEG values, and an empty marker field
    row = f"{timestamp}," + ",".join(map(str, args)) + ",\n"
    try:
        with open(filePath, 'a') as f:
            f.write(row)
    except Exception as e:
        print("Error writing EEG row:", e)
    print(f"Received EEG: {args}")
    print(f"Saved EEG row: {row.strip()}")
    # Store the last EEG message (if you need to use it when data pause)
    last_eeg = args

def marker_handler(address: str, marker_num: int):
    # Write a marker row with empty EEG fields, plus the marker value
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    row = f"{timestamp},,,,,,," + f"/Marker/{marker_num}\n"
    try:
        with open(filePath, 'a') as f:
            f.write(row)
    except Exception as e:
        print("Error writing marker row:", e)
    print(f"Received Marker: {marker_num}")
    print(f"Saved Marker row: {row.strip()}")
    # For example, if marker 2 stops recording, shut down the server
    if marker_num == 2:
        print("Stopping server as Marker 2 received.")
        sys.exit(0)

def signal_handler(sig, frame):
    print("Shutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    # Create dispatcher and map OSC addresses to handlers
    disp = dispatcher.Dispatcher()
    disp.map("/muse/eeg", eeg_handler)
    # Map markers. They can be sent as /Marker/1 or /Marker/2.
    disp.map("/Marker/1", lambda addr, *args: marker_handler(addr, 1))
    disp.map("/Marker/2", lambda addr, *args: marker_handler(addr, 2))
    
    # Set up the OSC UDP server
    server = osc_server.ThreadingOSCUDPServer((ip, port), disp)
    signal.signal(signal.SIGINT, signal_handler)

    print(f"Listening on {ip}:{port}")
    server.serve_forever()
