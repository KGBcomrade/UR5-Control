import time
import numpy as np
import matplotlib.pyplot as plt

from signal_plotter.plotter import animate_plotting


time_run = 0
dt = 0.1
dt_print = 1

time_history = 30


import serial
import time
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
    
def read_all_values():
    values = []
    while arduino.in_waiting:
        line = arduino.readline().decode().strip()
        if len(line) > 0:
            value = float(line)
            values.append(value)
    return values

def get_value():
    
    values = read_all_values()
    res = 0
    if len(values) > 0:
        res = np.mean([float(x) for x in values[-1:]])

    print(res, len(values))
    return res
    
animate_plotting(get_value, history_duration=time_history, step_time=dt, print_time=dt_print)
