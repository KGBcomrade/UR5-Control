from threading import Thread
from plotter import animate_plotting
from numpy import random

time_run = 0
dt = 0.01
dt_print = 1

time_history = 3

class Winner():
    def __init__(self, step=0.5) -> None:
        self.current_value = 0
        self.step = step
    
    def get_value(self):
        self.current_value += random.normal(0, self.step)
        return self.current_value  

win = Winner()

animate_plotting(win.get_value, 
                 history_duration=time_history,
                 step_time=dt)
