from pythonosc import dispatcher, osc_server
from datetime import datetime
import csv
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print("Error getting local IP:", e)
        return "127.0.0.1"

csv_file = "muse_data.csv"
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Timestamp", "Metric", "Value"])

def save_data(address, *args):
    timestamp = datetime.now().isoformat()
    metric = address.split("/")[-1]
    value = args[0] if args else None
    print(f"[SERVER] Received {metric}: {value} at {timestamp}")
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, metric, value])

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 5000

    print(f"[SERVER] Local IP detected as: {local_ip}")
    print("[SERVER] IMPORTANT: Ensure your Muse S OSC output is set to this IP and port:", port)

    disp = dispatcher.Dispatcher()
    osc_paths = [
        "/muse/elements/delta_absolute",
        "/muse/elements/theta_absolute",
        "/muse/elements/alpha_absolute",
        "/muse/elements/beta_absolute",
        "/muse/elements/gamma_absolute",
        "/muse/elements/heart_rate"
    ]
    for path in osc_paths:
        disp.map(path, save_data)

    try:
        server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), disp)
        print(f"[SERVER] Listening for OSC messages on {local_ip}:{port}")
        print(f"[SERVER] Data will be saved to: {csv_file}")
        print("[SERVER] Press Ctrl+C to stop the server...")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Server stopped.")
