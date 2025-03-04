#!/usr/bin/env python3
from datetime import datetime
import asyncio
from bleak import BleakScanner, BleakClient
from pythonosc import dispatcher, osc_server
import sys
import threading

# BLE Settings
ESP32_BLE_NAME = "ESP32_LED_CONTROL"
SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

# Muse Settings
IP = "0.0.0.0"
PORT = 5001
FILE_PATH = 'OSC-Python-Recording.csv'

# Shared Resources
ble_client = None
tp10_values = []
loop = asyncio.new_event_loop()
ble_queue = asyncio.Queue()
server = None  # Global reference to OSC server

def normalize_tp10(raw_value):
    """Normalize RAW_TP10 to 0-7 scale using dynamic range"""
    tp10_values.append(raw_value)
    if len(tp10_values) > 100:
        tp10_values.pop(0)
    
    min_val = min(tp10_values)
    max_val = max(tp10_values)
    
    return max(0, min(7, int(7 * (raw_value - min_val) / (max_val - min_val))) if (max_val - min_val) != 0 else 0)

async def ble_worker():
    """Dedicated BLE communication worker"""
    global ble_client
    while True:
        try:
            if not ble_client or not ble_client.is_connected:
                devices = await BleakScanner.discover()
                for d in devices:
                    if d.name and ESP32_BLE_NAME in d.name:
                        ble_client = BleakClient(d.address)
                        await ble_client.connect()
                        print(f"Connected to {ESP32_BLE_NAME}")
                        break
            
            led_count = await ble_queue.get()
            if ble_client and ble_client.is_connected:
                await ble_client.write_gatt_char(CHARACTERISTIC_UUID, bytes([led_count]))
            ble_queue.task_done()
            
        except Exception as e:
            print(f"BLE Error: {str(e)}")
            if ble_client:
                await ble_client.disconnect()
            ble_client = None
            await asyncio.sleep(5)

def muse_eeg_handler(address: str, *args):
    """Handle Muse EEG data and send to ESP32"""
    raw_tp10 = args[3]
    led_count = normalize_tp10(raw_tp10)
    
    asyncio.run_coroutine_threadsafe(ble_queue.put(led_count), loop)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open(FILE_PATH, 'a') as f:
        f.write(f"{timestamp}," + ",".join(map(str, args)) + ",\n")
    print(f"Queued LED count: {led_count} | TP10: {raw_tp10:.2f}")

async def main():
    """Main async entry point"""
    global server
    with open(FILE_PATH, 'w') as f:
        f.write("TimeStamp,RAW_TP9,RAW_AF7,RAW_AF8,RAW_TP10,Right_AUX,Left_AUX,Marker\n")
    
    asyncio.create_task(ble_worker())
    
    disp = dispatcher.Dispatcher()
    disp.map("/muse/eeg", muse_eeg_handler)
    
    server = osc_server.ThreadingOSCUDPServer((IP, PORT), disp)
    print(f"Listening for Muse data on {IP}:{PORT}")
    await loop.run_in_executor(None, server.serve_forever)

if __name__ == "__main__":
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())

    threading.Thread(target=run_loop, daemon=True).start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down...")
        if server:
            server.shutdown()
        if ble_client:
            loop.run_until_complete(ble_client.disconnect())
        sys.exit(0)
