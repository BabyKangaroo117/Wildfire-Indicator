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
        # Create two pipes: one for sensor data, one for MATLAB output
        self.sensor_pipe_read, self.sensor_pipe_write = os.pipe()
        self.matlab_pipe_read, self.matlab_pipe_write = os.pipe()
        self.matlab_queue = queue.Queue()
        self.matlab_runner = None
        
    def start(self):
        print("Starting SensorProcess...")
        # Create MatlabRunner before forking
        self.matlab_runner = MatlabRunner()
        
        # First fork for sensor process
        sensor_pid = os.fork()
        
        if sensor_pid == 0:  # Sensor child process
            print("In sensor child process...")
            os.close(self.sensor_pipe_read)
            os.close(self.matlab_pipe_read)
            os.close(self.matlab_pipe_write)  # Sensor doesn't need MATLAB pipe
            try:
                self.run_sensor_loop()
            finally:
                print("Sensor process exiting...")
                os._exit(0)
                
        # Parent process continues here
        print(f"Sensor child PID: {sensor_pid}")
        
        # Second fork for MATLAB process
        matlab_pid = os.fork()
        
        if matlab_pid == 0:  # MATLAB child process
            print("In MATLAB child process...")
            os.close(self.sensor_pipe_read)
            os.close(self.sensor_pipe_write)
            os.close(self.matlab_pipe_read)
            try:
                if self.matlab_runner:
                    self.matlab_runner.run_script(
                        '/home/joey/Repos/Wildfire-Indicator/src/smoke_detection.m',
                        self.matlab_pipe_write)
            finally:
                print("MATLAB process exiting...")
                os.close(self.matlab_pipe_write)
                os._exit(0)
                
        # Parent process continues here
        print(f"MATLAB child PID: {matlab_pid}")
        os.close(self.sensor_pipe_write)
        os.close(self.matlab_pipe_write)
        
        return sensor_pid, matlab_pid  # Return both PIDs
    
            
    def process_matlab_output(self):
        """Process MATLAB output in parent process only"""
        try:
            ready_to_read, _, _ = select.select([self.matlab_pipe_read], [], [], 0)
            
            if self.matlab_pipe_read in ready_to_read:
                output = os.read(self.matlab_pipe_read, 1024).decode('utf-8')
                for line in output.splitlines():
                    if line:
                        # Put processed output in queue for GUI
                        self.matlab_queue.put(line)
        except Exception as e:
            print(f"Error processing MATLAB output: {e}")

         
            

    def run_sensor_loop(self):
        """Run sensor loop in child process"""
        print("Starting sensor loop in child process...")
        try:
            arduino_data = RetrieveArduino() 
            
            while True:
                try:
                    arduino_data.GetData()
                    data = {
                        "temperature": arduino_data.temp,
                        "humidity": arduino_data.humidity,
                        "smoke_detected": False
                    }
                    
                    # Send sensor data through pipe
                    message = json.dumps(data).encode('utf-8') + b'\n'
                    bytes_written = os.write(self.sensor_pipe_write, message)
                    print(f"Wrote {bytes_written} bytes of sensor data")
                    
                except OSError as e:
                    print(f"Pipe write error: {e}")
                    break
                except Exception as e:
                    print(f"Sensor loop error: {e}")
                    break
                    
                time.sleep(1)
                
        finally:
            print("Closing sensor pipe in child...")
            os.close(self.sensor_pipe_write)

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
    def __init__(self, root: tk.Tk, sensor_pipe: int, matlab_pipe: int):
        self.root = root
        self.root.title("Environmental Monitor")
        self.sensor_pipe = sensor_pipe
        self.matlab_pipe = matlab_pipe
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure("Warning.TLabel", foreground="red", font=('Helvetica', 10, 'bold'))
        self.style.configure("HighRisk.TLabel", foreground="dark red", font=('Helvetica', 10, 'bold'))
        self.style.configure("Normal.TLabel", font=('Helvetica', 12))
        self.style.configure("Header.TLabel", font=('Helvetica', 14, 'bold'))
        
        # Create main frame ONCE
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure root grid weights
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        self.sensor_data = {
            "temperature": 0.0,
            "humidity": 0.0,
            "smoke_detected": False
        }
        
        # Create output text widget for MATLAB data
        self.output_text = tk.Text(self.main_frame, height=5, width=50)
        self.output_text.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Create output handler for MATLAB data
        self.matlab_queue = queue.Queue()
        self.matlab_handler = MatlabOutputHandler(self.matlab_queue)
        
        self.create_sensor_displays()
        self.create_warning_displays()
        self.check_sensor_data()
        self.check_matlab_data()
        print("Finished Tkinter Initialization")
    
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
    
    def check_matlab_data(self):
        """Check for MATLAB data"""
        try:
            ready_to_read, _, _ = select.select([self.matlab_pipe], [], [], 0)
            
            if self.matlab_pipe in ready_to_read:
                output = os.read(self.matlab_pipe, 1024).decode('utf-8')
                self.output_text.insert(tk.END, output)
                self.output_text.see(tk.END)
        except Exception as e:
            print(f"Error in check_matlab_data: {e}")
        # Schedule next check
        self.root.after(100, self.check_matlab_data)
    
    def check_sensor_data(self):
        """Check for sensor data"""
        try:
            ready_to_read, _, _ = select.select([self.sensor_pipe], [], [], 0)
            
            if self.sensor_pipe in ready_to_read:
                data = os.read(self.sensor_pipe, 1024)
                if data:
                    print(f"Received raw data: {data}")
                    self.sensor_data = json.loads(data.decode('utf-8'))
                    print(f"Processed sensor data: {self.sensor_data}")
                    
                    # Check for smoke detection from MATLAB
                    try:
                        matlab_result = self.matlab_queue.get_nowait()
                        print(f"MATLAB result: {matlab_result}")
                        self.sensor_data['smoke_detected'] = (matlab_result == "SMOKE_DETECTED")
                    except queue.Empty:
                        pass
                    
                    self.update_display()
        except Exception as e:
            print(f"Error in check_sensor_data: {e}")
        
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
        """Update the GUI display"""
        try:
            print(f"Updating display with: {self.sensor_data}")
            self.temp_label.config(text=f"{self.sensor_data['temperature']:.1f}°C")
            self.humidity_label.config(text=f"{self.sensor_data['humidity']:.1f}%")
            
            # Check smoke detection
            if self.sensor_data['smoke_detected']:
                print("Smoke detected - updating warning")
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
                self.dry_label.config(text="⚠ LOW HUMIDITY WARNING! Look out for fires.")
            else:
                self.dry_label.config(text="")
                
        except Exception as e:
            print(f"Error updating display: {e}")
def main():
    def signal_handler(sig, frame):
        print('\nShutting down...')
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    sensor_process = SensorProcess()
    sensor_pid, matlab_pid = sensor_process.start()  # Get both PIDs
    
    root = tk.Tk()
    app = EnvironmentalMonitor(root, 
                             sensor_process.sensor_pipe_read,
                             sensor_process.matlab_pipe_read)
    
    try:
        root.mainloop()
    finally:
        os.close(sensor_process.sensor_pipe_read)
        os.close(sensor_process.matlab_pipe_read)
        # Kill both child processes
        if sensor_pid:
            os.kill(sensor_pid, 9)
            os.waitpid(sensor_pid, 0)
        if matlab_pid:
            os.kill(matlab_pid, 9)
            os.waitpid(matlab_pid, 0)

if __name__ == "__main__":
    main()
