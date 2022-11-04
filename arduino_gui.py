import time
import numpy as np
import matplotlib.pyplot as plt


class History():
    
    def __init__(self, N_points):
        self.array = np.zeros(N_points)
        self.beg = 0
        self.end = N_points
    
    @property
    def values(self):
        return np.concatenate([self.array[self.beg:], self.array[:self.end]])
    
    def append(self, element):
        self.beg+=1
        self.end+=1
        if self.end >= self.array.size:
            self.beg -= self.array.size
            self.end -= self.array.size
        self.array[self.end-1] = element
        

time_run = 0
dt = 0.1
dt_print = 1

time_history = 30
N_points = int(time_history//dt)
hist_beg = 0


import serial
import time
arduino = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)
    

hist = History(100)

def get_value():
    value = arduino.read_all()
    
    # time.sleep(0.1)
    values = value.split()
    res = 0
    if len(values) > 0:
        res = np.mean([float(x) for x in values[-1:]])

    print(res, len(values))
    return res
    # return 10       # tests
    
while True:
    time.sleep(dt)
    time_run += dt
    
    value = get_value()
    
    hist.append(value)
    plt.clf()
    plt.plot(hist.values)
    # plt.ylim(bottom=0)
    plt.pause(0.0005)
    
    
    if time_run > dt_print:
        print(value)
        # print(hist.values)    
        time_run = 0
    