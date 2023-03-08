from collections.abc import Callable

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation



def animate_plotting(
        read_value_func: Callable[[], float],
        history_duration: float = 30.0, step_time: float = 0.1, print_time: float = None, ylim=None):
    """creates plot and updates it in real time using values
    from `read_value_func`. It keeps history for some time, then erases old values.

    Args:
        read_value_func (Callable[[], float]): returns values to plot
        history_duration (float, optional): time to keep history. Defaults to 30.0.
        step_time (float, optional): time between calls of read_value_func. Defaults to 0.1.
        print_time (float, optional): time between printing values to std.out. If None, doesn't print. Defaults to None.
        ylim ()
    """

    class History():
        
        def __init__(self, N_points):
            self.array = np.zeros(N_points)
            self.beg = -N_points
            self.end = 0
        
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
            
    N_points = int(history_duration/step_time+0.01) + 1
    hist = History(N_points)
    xdata = np.linspace(-history_duration, 0, N_points)
    
    fig, ax = plt.subplots()
    ln, = plt.plot([], [])
    plt.xlabel("time (s)")
    
    def init():
        ax.set_xlim(xdata[0], xdata[-1])
        return ln,

    def update(frame):
        hist.append(read_value_func())
        ln.set_data(xdata, hist.values)
        ax.relim()      # Recompute the data limits based on current artists
        ax.autoscale()
        # print(ax.get_yticklabels())
        # ax.set_yticks(ax.get_yticks())
        # ax.set_yticklabels(ax.get_yticks())
        return ln,
    
    '''
        ax.relim()
        ax.autoscale_view(True,True,True)
        
        такая конфигурация вроде дает неправильную y ось.
        '''
    

    

    ani = FuncAnimation(fig, update, frames=np.linspace(0, 2*np.pi, 128),
                    init_func=init, blit=True)
    plt.show()