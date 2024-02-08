import pyvisa

rm = pyvisa.ResourceManager()

rsrc = rm.open_resource('USB0::4883::32888::P0006292::0::INSTR',
                                read_termination='\n')

from signal_plotter import animate_plotting

time_run = 0
dt = 0.1
dt_print = 1

time_history = 30


def get_value():
    return rsrc.query('measure:power?');
    
animate_plotting(get_value, history_duration=time_history, step_time=dt, print_time=dt_print)
