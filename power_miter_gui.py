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
from signal_plotter.plotter import animate_plotting


time_run = 0
dt = 0.1
dt_print = 1

time_history = 30
    


def get_value():
    return rsrc.query('measure:power?');
    
# v = 10
# def get_value():
#     global v
#     v += np.random.normal(0, 0.5)
#     return v    # tests
    
    
animate_plotting(get_value, history_duration=time_history, step_time=dt, print_time=dt_print)
