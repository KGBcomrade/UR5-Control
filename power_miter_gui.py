import pyvisa

rm = pyvisa.ResourceManager()

for addr in rm.list_resources():
     try:
         print(addr, '-->', rm.open_resource(addr).query('*IDN?').strip())
     except pyvisa.VisaIOError:
         pass
   
# my_instrument = rm.open_resource('GPIB0::14::INSTR')
# print(my_instrument.query('*IDN?'))

rsrc = rm.open_resource('USB0::4883::32888::P0006292::0::INSTR',
                                read_termination='\n')

print("Unit is", rsrc.query('power:dc:unit?'))

print("Power is", rsrc.query('measure:power?'))

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
    

hist = History(100)
# print(hist.values)

def get_value():
    return rsrc.query('measure:power?');
    # return 10       # tests
    
while True:
    time.sleep(dt)
    time_run += dt
    
    value = get_value()
    
    hist.append(value)
    plt.clf()
    plt.plot(hist.values)
    plt.ylim(bottom=0)
    plt.pause(0.0005)
    
    
    if time_run > dt_print:
        print(value)
        # print(hist.values)    
        time_run = 0
    