import tkinter as tk
from tkinter import ttk
import os
import json
import select
import time
import random
from typing import Dict, Any
from RetrieveArduinoData import RetrieveArduino
class SensorProcess:
    def __init__(self):
        self.pipe_read, self.pipe_write = os.pipe()
        
    def start(self):
        pid = os.fork()
        if pid == 0:
            os.close(self.pipe_read)
            self.run_sensor_loop()
        else:
            os.close(self.pipe_write)
            return pid
            
    def run_sensor_loop(self):
        arduino_data = RetrieveArduino() 
        arduino_data.GetData()
        data = {
            "temperature": 0,
            "humidity": 0,
            "high_temp": False,
            "low_humidity": False 
        }
                
        while True:
            arduino_data = RetrieveArduino() 
            arduino_data.GetData()
            data["temperature"] = arduino_data.temp
            data["humidity"] = arduino_data.humidity 
            
            try:
                message = json.dumps(data).encode('utf-8') + b'\n'
                os.write(self.pipe_write, message)
            except OSError:
                break
                
            time.sleep(1)
        
        os.close(self.pipe_write)
        os._exit(0)

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
            "high_temp": False,
            "low_humidity": False
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

if __name__ == "__main__":
    main()       



