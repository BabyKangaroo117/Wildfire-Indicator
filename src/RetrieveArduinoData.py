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
            while(ser.readline().decode('utf-8').strip() != "start"):
                pass    
            self.temp = ast.literal_eval(ser.readline().decode('utf-8').strip())
            self.humidity = ast.literal_eval(ser.readline().decode('utf-8').strip())

