# Importing Libraries
import serial
import time
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
def write_read(x):
    # arduino.write(bytes(x, 'utf-8'))
    time.sleep(0.15)
    data = arduino.readline()
    return data
while True:
    # num = input("Enter a number: ") # Taking input from user
    # value = write_read(num)
    
    # value = write_read(10)
    # value = arduino.readline()
    value = arduino.read_all()
    
    time.sleep(0.1)

    # value = arduino.read()
    # if value != b'':
    #     print(float(value))
    # print(value) # printing the value
    values = value.split()
    if len(value) > 0:
        print(value.split()[-1])

