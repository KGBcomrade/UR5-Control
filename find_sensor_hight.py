import numpy as np
import yaml
import time

## sacred staff
import os
import dotenv; dotenv.load_dotenv()
from sacred import Experiment
from sacred.observers import MongoObserver, FileStorageObserver
import pymongo
ex = Experiment('hight_test')
if "username" in os.environ and "host" in os.environ and "password" in os.environ:
    client = pymongo.MongoClient(
        username=os.environ['username'],
        password=os.environ['password'],
        host=os.environ['host'],
        port=27018,
        authSource=os.environ['database'],
        tls=True,
        tlsCAFile=
        "/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt",
    )
    ex.observers.append(
        MongoObserver(client=client, db_name=os.environ['database']))
else:
    ex.observers.append(FileStorageObserver('logdir'))
    input("WARNING! No password for db. Confirm logging locally")

params_file = 'params.yaml'
import sys
for argv in sys.argv[1:]:
    if argv.endswith('.yaml'):
        params_file = argv
        break

ex.add_config(params_file)

with open(params_file) as conf_file:
    config = yaml.safe_load(conf_file)
    
## Robot init
import rtde_control
import rtde_receive
rtde_c = rtde_control.RTDEControlInterface(config['ip'])
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'], frequency=50)


## Params
config['safe_hight'] = 396      ## beginning hight im mm
config['minimal_possible_hight'] = 385      ## dangerous to pass hight im mm

# config['safe_hight'] = 391      ## beginning hight im mm
# config['minimal_possible_hight'] = 385      ## dangerous to pass hight im mm


touching_y = 4    ## coordinates of touching in mm
tenso_difference = 0.7      ## gramms to detect touching
depth_steps = [0.1, 0.02]
small_indent = 0.1      # на сколько робот поднимется после первого косания для второго захода
config['speed'] = [0.01, 0.01]

use_sensor_signal = False
# todo add control of power signal


if use_sensor_signal:
    # init PowerMeter
    import pyvisa

    rm = pyvisa.ResourceManager()

    rsrc = rm.open_resource(config['power_meter_address'],
                                    read_termination='\n')

# init Arduino
import serial
arduino = serial.Serial(port=config['arduino_address'], baudrate=115200, timeout=.1)

# ## For tests
# class arduino:
#     def read_all():
#         z = rtde_r.getActualTCPPose()[2]
#         if (z*1e3 < 330):
#             return "1 "*20
#         else:
#             return '0 '*20

class Rotor():
    '''Class for calculating rotation of 2d vector'''
    def __init__(self, angle):
        '''
        angle -- in degrees
        '''
        self._angle = np.radians(angle)
        self._main_mat = np.array([[np.cos(self._angle), -np.sin(self._angle)], [np.sin(self._angle), np.cos(self._angle)]])
        self._inv_mat = np.array([[np.cos(self._angle), np.sin(self._angle)], [-np.sin(self._angle), np.cos(self._angle)]])

        
    def rotate(self, coord):
        '''
        returns new massive with rotated x and y coordinate
        '''
        beg = np.array(coord[:2])
        res = np.dot(self._main_mat, beg)
        return np.concatenate([res, coord[2:]])
    def inverse(self, coord):
        beg = np.array(coord[:2])
        res = np.dot(self._inv_mat, beg)
        return np.concatenate([res, coord[2:]])
    
    
rotor = Rotor(config['sensor_angle'])


net_step=np.array(config['grid']['steps'])
p0 = np.array(config['left_upper_corner'])
p1 = np.array(config['right_down_corner'])
p0 = rotor.rotate(p0)
p1 = rotor.rotate(p1)

def put_hight_value_in_config(sensor_hight, file_name):
    """
    Opens config file and replaces old sensor_, minimal_ 
    and safe_  hights with new determined
    """
    import fileinput

    for line in fileinput.input(files=file_name, inplace=True):
        if line.count("sensor_hight:") == 1:
            line = f"sensor_hight: {sensor_hight}\n"
        
        if line.count("minimal_possible_hight:") == 1:
            line = f"minimal_possible_hight: {sensor_hight-0.6}\n"
        
        if line.count("safe_hight:") == 1:
            line = f"safe_hight: {sensor_hight+0.4}  # in millimeters (+0.4 of sensor)\n"
        
        sys.stdout.write(line)
        

@ex.automain
def touch_sensor(_run):
    sensor_shape = np.abs(p1-p0)
    print("Sensor shape is", *[format(x, ".1f") for x in sensor_shape])
        

    # print("Touching will take", (config['safe_hight'] - config['minimal_possible_hight'])//depth_step*(config['time_to_measure']+config['time_to_sleep'])//60, 'minutes')

    begining_of_fiber_coord = p0*[1, 0.5] + p1*[0, 0.5]     # beginning of relative coordinate system in rotated coord system.   
    direction_signs = np.sign(p1-p0)*[1, -1]    # directions for increasing coordinates


    safe_hight = config['safe_hight']/1e3

    c_state = rtde_r.getActualTCPPose()
    if c_state[2] < safe_hight:
        rtde_c.moveL(c_state[:2] + [safe_hight] + c_state[3:6], *config['speed'])
    
    net_save_hight = safe_hight
    

    ## touching here was loop
    rel_point = [sensor_shape[0]/2, touching_y]
    
    point = rotor.inverse(begining_of_fiber_coord + rel_point*direction_signs)/1e3 
    # rotating back into initial coordinate system and converting to mm-s
    point = point.tolist()   
    
    print(*[format(x, ".1f") for x in rel_point], end='\t')
    print(*[format(x, ".4f") for x in point])
    
    point_results = {"target_coordinate": point,
                        "relative_coordinate": rel_point,
                        "base_coordinate":[],
                        "vector_force":[],
                        "z_coord":[],
                        'tenso_signal': [],
                        'final_power': [],
                    #  'inner_powers': [],
                        'power_error': [],
                    #  'inner_tenso_signals': [],
                        }
    

    c_state = rtde_r.getTargetTCPPose()
    rtde_c.moveL(c_state[:2] + [net_save_hight] + c_state[3:6], *config['speed'])
    rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])

    time.sleep(2)       # чтобы тензодатчик успокоился после перемещения
    
    tenso_string = arduino.read_all()
    tenso_values = tenso_string.split()
    # point_results['inner_tenso_signals'].append(tenso_values)
    if (len(tenso_values) == 0):
        tenso_value = None
    else:
        try:
            tenso_values = np.array([float(x) for x in tenso_values[-11:-1]])
            tenso_value = tenso_values.mean()
            print(f"Got {len(tenso_values)} tenso-signals. Mean is {tenso_value}. Error is {np.sqrt(np.mean((tenso_values-tenso_value)**2))}")
        except ValueError:
            tenso_value = None
    
    null_tenso_signal = tenso_value
    
    def iteraterate(target_depthes):
        for depth in target_depthes:
            ## moving
            rtde_c.moveL(point + [depth] + c_state[3:6], *config['speed'])
            
            # _run.log_scalar("all_powers", 0)
            # sleeping
            time.sleep(config['time_to_sleep'])
            arduino.read_all()  # removing values during movement
            inner_powers = []
            start_time = time.time()
            while( time.time()-start_time < config['time_to_measure']):
                if use_sensor_signal:
                    p = float(rsrc.query('measure:power?'))
                    inner_powers.append(p)
                    # _run.log_scalar("all_powers", p)
            # point_results['inner_powers'].append(inner_powers[::10])
            if use_sensor_signal:
                inner_powers = np.array(inner_powers)
                
                power = inner_powers.mean()
                _run.log_scalar('power', power)
                point_results['final_power'].append(power)
                point_results['power_error'].append(np.sqrt(np.mean((inner_powers-power)**2)))
            
            ## logging
            point_results['z_coord'].append(depth)
            _run.log_scalar('z_coord', depth)
                                
            tenso_string = arduino.read_all()
            tenso_values = tenso_string.split()
            if (len(tenso_values) == 0):
                tenso_value = None
            else:
                try:
                    tenso_value = np.mean( [float(x) for x in tenso_values[-1:]])
                except ValueError:
                    tenso_value = None
            point_results['tenso_signal'].append(tenso_value)
            _run.log_scalar("tenso_signal", tenso_value)
            print('hight is', format(depth*1e3, ".2f"), 'tenso signal is', tenso_value)
            
            if np.abs(tenso_value - null_tenso_signal) >= tenso_difference:
                # Reached touching. Hight is {depth}
                _run.log_scalar('point_results', point_results)
                return depth*1e3
        raise Exception("Didn't found sensor until minimal possible hight")
        
    target_depthes = np.arange(config['safe_hight'], config['minimal_possible_hight'], -depth_steps[0])/1e3
    
    first_depth = iteraterate(target_depthes)
    print("Reached first touching. Hight is\n", format(first_depth*1e3, ".2f"))
            
    target_depthes = np.arange(first_depth+small_indent, config['minimal_possible_hight'], -depth_steps[1])/1e3
    second_depth = iteraterate(target_depthes)
    print("Reached second touching. Hight is\n", format(second_depth*1e3, ".2f"))
    rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])

    # changing sensor hight in config file
    put_hight_value_in_config(second_depth, params_file)


        
    
