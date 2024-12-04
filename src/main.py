import time
from RetrieveArduinoData import RetrieveArduino

arduino = RetrieveArduino()

if __name__ == "__main__":
    while(True):
        arduino.GetData()
        print("Hello")
        print(arduino.temp)
        print(arduino.humidity)
        



