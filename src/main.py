import queue
import tkinter as tk
from tkinter import ttk
import os
import json
import select
import time
import threading
import signal
from typing import Dict, Any
from RetrieveArduinoData import RetrieveArduino
from MatlabScriptRunner import MatlabRunner


class SensorProcess:
    def __init__(self):
        self.pipe_read, self.pipe_write = os.pipe()
        self.matlab_queue = queue.Queue()
        self.matlab_runner = None
        self.smoke_detection_counter = 0
        
    def start(self):
        # Create MatlabRunner in main thread before forking
        self.matlab_runner = MatlabRunner()
        
        pid = os.fork()
        if pid == 0:
            os.close(self.pipe_read)
            self.run_sensor_loop()
        else:
            os.close(self.pipe_write)
            # Start MATLAB process in a separate thread
            self.start_matlab_thread()
            return pid
    
    def matlab_worker(self):
        """Thread function to run MATLAB script"""
        try:
            # Instead of creating a new MatlabRunner, use the existing one
            if self.matlab_runner:
                self.matlab_runner.run_script('/home/joey/Repos/Wildfire-Indicator/src/smoke_detection.m')
        except Exception as e:
            print(f"Error in MATLAB thread: {e}")
            
    def start_matlab_thread(self):
        """Start MATLAB in a separate thread"""
        matlab_thread = threading.Thread(target=self.matlab_worker)
        matlab_thread.daemon = True
        matlab_thread.start()
            
    def run_sensor_loop(self):
        arduino_data = RetrieveArduino() 
        arduino_data.GetData()
        data = {
            "temperature": 0,
            "humidity": 0,
            "smoke_detected": False 
        }
                
        while True:
            arduino_data = RetrieveArduino() 
            arduino_data.GetData()
            data["temperature"] = arduino_data.temp
            data["humidity"] = arduino_data.humidity
            
            # Check for MATLAB output
            try:
                matlab_output = self.matlab_queue.get_nowait()
                if matlab_output == "SMOKE_DETECTED":
                    self.smoke_detection_counter += 1
                    # Require 3 consecutive smoke detections to trigger the warning
                    if self.smoke_detection_counter >= 3:
                        data["smoke_detected"] = True
                else:
                    self.smoke_detection_counter = 0
                    data["smoke_detected"] = False
            except queue.Empty:
                # No MATLAB output available, continue with current state
                pass
            
            try:
                message = json.dumps(data).encode('utf-8') + b'\n'
                os.write(self.pipe_write, message)
            except OSError:
                break
                
            time.sleep(1)
        
        os.close(self.pipe_write)
        os._exit(0)
            
    def run_sensor_loop(self):
        arduino_data = RetrieveArduino() 
        arduino_data.GetData()
        data = {
            "temperature": 0,
            "humidity": 0,
            "smoke_detected": False 
        }
                
        while True:
            arduino_data = RetrieveArduino() 
            arduino_data.GetData()
            data["temperature"] = arduino_data.temp
            data["humidity"] = arduino_data.humidity
            
            # Check for MATLAB output
            try:
                matlab_output = self.matlab_queue.get_nowait()
                if matlab_output == "SMOKE_DETECTED":
                    self.smoke_detection_counter += 1
                    # Require 3 consecutive smoke detections to trigger the warning
                    if self.smoke_detection_counter >= 3:
                        data["smoke_detected"] = True
                else:
                    self.smoke_detection_counter = 0
                    data["smoke_detected"] = False
            except queue.Empty:
                # No MATLAB output available, continue with current state
                pass
            
            try:
                message = json.dumps(data).encode('utf-8') + b'\n'
                os.write(self.pipe_write, message)
            except OSError:
                break
                
            time.sleep(1)
        
        os.close(self.pipe_write)
        os._exit(0)

class MatlabOutputHandler:
    """Handles MATLAB output and updates the smoke detection status"""
    def __init__(self, queue):
        self.queue = queue

    def handle_output(self, output: str):
        """Process MATLAB output and put results in queue"""
        try:
            # Parse the prediction line
            if "Prediction:" in output:
                # Split the line into parts
                parts = output.split("(")
                prediction = parts[0].split(":")[1].strip()
                accuracy = float(parts[1].strip("%)"))
                
                # Check if it's a smoke prediction with accuracy >= 80%
                if prediction == "smoke" and accuracy >= 80:
                    self.queue.put("SMOKE_DETECTED")
                else:
                    self.queue.put("NO_SMOKE")
        except (IndexError, ValueError) as e:
            print(f"Error parsing MATLAB output: {e}")
            self.queue.put("NO_SMOKE")    

class EnvironmentalMonitor:
    def __init__(self, root: tk.Tk, pipe_fd: int):
        self.root = root
        self.root.title("Environmental Monitor")
        self.pipe_fd = pipe_fd
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure("Warning.TLabel", foreground="red", font=('Helvetica', 10, 'bold'))
        self.style.configure("HighRisk.TLabel", foreground="dark red", font=('Helvetica', 10, 'bold'))
        self.style.configure("Normal.TLabel", font=('Helvetica', 12))
        self.style.configure("Header.TLabel", font=('Helvetica', 14, 'bold'))
        
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.sensor_data = {
            "temperature": 0.0,
            "humidity": 0.0,
            "smoke_detected": False
        }
        
        self.create_sensor_displays()
        self.create_warning_displays()
        self.check_sensor_data()

    def create_sensor_displays(self):
        ttk.Label(self.main_frame, text="Temperature", style="Header.TLabel").grid(row=0, column=0, pady=5)
        self.temp_label = ttk.Label(self.main_frame, text="--°C", style="Normal.TLabel")
        self.temp_label.grid(row=1, column=0, pady=5)
        
        ttk.Label(self.main_frame, text="Humidity", style="Header.TLabel").grid(row=0, column=1, pady=5, padx=20)
        self.humidity_label = ttk.Label(self.main_frame, text="--%", style="Normal.TLabel")
        self.humidity_label.grid(row=1, column=1, pady=5, padx=20)
        
    def create_warning_displays(self):
        # Smoke warning
        self.smoke_label = ttk.Label(self.main_frame, text="", style="Warning.TLabel")
        self.smoke_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Fire risk warning
        self.fire_risk_label = ttk.Label(self.main_frame, text="", style="HighRisk.TLabel")
        self.fire_risk_label.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Dry warning
        self.dry_label = ttk.Label(self.main_frame, text="", style="Warning.TLabel")
        self.dry_label.grid(row=4, column=0, columnspan=2, pady=10)
    
    def check_sensor_data(self):
        ready_to_read, _, _ = select.select([self.pipe_fd], [], [], 0)
        
        if self.pipe_fd in ready_to_read:
            try:
                data = os.read(self.pipe_fd, 1024)
                if data:
                    self.sensor_data = json.loads(data.decode('utf-8'))
                    self.update_display()
            except (OSError, json.JSONDecodeError) as e:
                print(f"Error reading sensor data: {e}")
        
        self.root.after(100, self.check_sensor_data)
    
    def assess_fire_risk(self) -> tuple[bool, str]:
        temp = self.sensor_data['temperature']
        humidity = self.sensor_data['humidity']
        
        if temp >= 40 and humidity <= 15:
            return True, "EXTREME FIRE RISK! High temperature and very low humidity!"
        elif temp >= 35 and humidity <= 20:
            return True, "HIGH FIRE RISK! High temperature and low humidity!"
        elif temp >= 30 and humidity <= 30:
            return True, "ELEVATED FIRE RISK! Watch temperature and humidity levels."
        return False, ""
    
    def update_display(self):
        self.temp_label.config(text=f"{self.sensor_data['temperature']:.1f}°C")
        self.humidity_label.config(text=f"{self.sensor_data['humidity']:.1f}%")
        
        # Check smoke detection
        if self.sensor_data['smoke_detected']:
            self.smoke_label.config(text="⚠ SMOKE DETECTED! Check for fire hazards!")
        else:
            self.smoke_label.config(text="")
            
        # Check fire risk conditions
        fire_risk, risk_message = self.assess_fire_risk()
        if fire_risk:
            self.fire_risk_label.config(text=f"⚠ {risk_message}")
        else:
            self.fire_risk_label.config(text="")
            
        # Check humidity
        if self.sensor_data['humidity'] < 30:
            self.dry_label.config(text="⚠ LOW HUMIDITY WARNING! Consider using a humidifier.")
        else:
            self.dry_label.config(text="")

def main():
    # Set up signal handling in main thread
    def signal_handler(sig, frame):
        print('\nShutting down...')
        # Cleanup code here
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    sensor_process = SensorProcess()
    child_pid = sensor_process.start()
    
    root = tk.Tk()
    app = EnvironmentalMonitor(root, sensor_process.pipe_read)
    
    try:
        root.mainloop()
    finally:
        os.close(sensor_process.pipe_read)
        if child_pid:
            os.kill(child_pid, 9)
            os.waitpid(child_pid, 0)
        if sensor_process.matlab_runner:
            sensor_process.matlab_runner.cleanup_matlab()

if __name__ == "__main__":
    main()       



