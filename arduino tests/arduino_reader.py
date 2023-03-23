# Importing Libraries
import serial
import time
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

while True:
    
    time.sleep(0.1)
    value = arduino.read_all()

    values = value.split()
    if len(value) > 0:
        print(values[-1])

