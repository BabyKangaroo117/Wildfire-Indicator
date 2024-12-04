import serial
import math
import time
import ast
class RetrieveArduino:
    def __init__(self) -> None:
        self.port = "/dev/ttyACM0"
        self.baudrate = 9600
        self.timeout = 1
        self.temp = 0
        self.humidity = 0

    def GetData(self):
        with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:

            while(ser.readline().decode('utf8').rstrip != "start"):
                pass # Sync data collection
            self.temp = float(ser.readline().decode('utf-8').rstrip())
            self.humidity = float(ser.readline().decode('utf-8').rstrip())
