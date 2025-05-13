#!/usr/bin/env python3
import time
import os
import subprocess
import sys

def watch_logs():
    """Watch for application logs in real-time"""
    print("Watching for application logs...")
    print("Please upload Factura Volti.pdf in the NiceGUI interface now...")
    print("Press Ctrl+C to stop watching")
    
    # Start a background process to capture logs
    process = subprocess.Popen(
        ["ps", "aux"], 
        stdout=subprocess.PIPE
    )
    output, _ = process.communicate()
    
    # Look for the invoice_app_main.py process
    for line in output.decode().split('\n'):
        if 'invoice_app_main.py' in line:
            print(f"Found process: {line}")
    
    # Monitor console output
    try:
        while True:
            process = subprocess.Popen(
                ["tail", "-n", "20", "/tmp/invoice_app.log"] if os.path.exists("/tmp/invoice_app.log") else 
                ["tail", "-n", "20", "/var/log/system.log"],
                stdout=subprocess.PIPE
            )
            output, _ = process.communicate()
            if output:
                print(output.decode())
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopped watching logs")

if __name__ == "__main__":
    watch_logs() 