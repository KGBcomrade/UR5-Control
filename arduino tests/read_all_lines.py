# Importing Libraries
import serial
import time
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

def read_all_lines():
    lines = []
    while arduino.in_waiting:
        line = arduino.readline().decode().strip()
        lines.append(line)
    return lines

while True:
    time.sleep(0.1)

    values = read_all_lines()
    if len(values) > 0:
        # print(values[-1])
        print(values)

