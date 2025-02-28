#!/usr/bin/env python3
import subprocess
import sys

def capture_tcpdump(interface="en0", port=5001, output_file="tcpdump_output.txt"):
    # Build the tcpdump command with -l for line-buffered output.
    cmd = ["sudo", "tcpdump", "-i", interface, "-vv", "-X", "-l", f"udp port {port}"]

    with open(output_file, "w") as file:
        # Launch tcpdump, capturing its stdout
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        
        try:
            # Read and write each line as it comes in.
            for line in process.stdout:
                file.write(line)
                file.flush()
                # Optionally, print to the terminal as well.
                print(line, end="")
        except KeyboardInterrupt:
            print("Terminating tcpdump capture...")
            process.terminate()
            sys.exit(0)

if __name__ == "__main__":
    capture_tcpdump()
