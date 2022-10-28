import numpy as np
import yaml
import time

## sacred staff
import os
import dotenv; dotenv.load_dotenv()
from sacred import Experiment
from sacred.observers import MongoObserver, FileStorageObserver
import pymongo
ex = Experiment('sensor_test')
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
ex.add_config('params.yaml')

with open('params.yaml') as conf_file:
    config = yaml.safe_load(conf_file)
    
## Robot init
import rtde_control
import rtde_receive
rtde_c = rtde_control.RTDEControlInterface(config['ip'])
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'], frequency=50)

# init PowerMeter
import pyvisa

rm = pyvisa.ResourceManager()

rsrc = rm.open_resource(config['power_meter_address'],
                                read_termination='\n')

# init Arduino
import serial
arduino = serial.Serial(port=config['arduino_address'], baudrate=115200, timeout=.1)

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

sensor_shape = np.abs(p1-p0)
print("Sensor shape is", *[format(x, ".1f") for x in sensor_shape])
    
vertical_area = config['vertical_area']
horisontal_area = config['horisontal_area']

for i in range(len(horisontal_area)):
    if horisontal_area[i] < 0:
        horisontal_area[i] += sensor_shape[0]
if horisontal_area[1] > sensor_shape[0] or horisontal_area[0]  > sensor_shape[0] \
    or horisontal_area[1] < 0 or horisontal_area[0]  < 0:
    raise ValueError("Error in horisontal area param. Can't touch outside of sensor")
if horisontal_area[1] < horisontal_area[0]:
    raise ValueError("Error in horisontal area param. Error. Area is an empty set")
if np.abs(vertical_area[0]) > sensor_shape[1]/2 or np.abs(vertical_area[0]) > sensor_shape[1]/2:
    raise ValueError("Error in horisontal area param. Can't touch outside of sensor")
if horisontal_area[1] < horisontal_area[0]:
    raise ValueError("Error in horisontal area param. Error. Area is an empty set")

print("Target touching area is", horisontal_area, vertical_area)

horisontal_area[1] += net_step[0]*0.00001
vertical_area[1] += net_step[1]*0.00001
# to include last point

X, Y = np.arange(*horisontal_area, net_step[0]), np.arange(*vertical_area, net_step[1])
print("Target coordinates are", X, Y)
shape = len(X), len(Y)
print("Net shape is", shape)
print("Touching will take", config['sensor_depth_points']*(config['time_to_measure']+config['time_to_sleep'])*shape[0]*shape[1]//60, 'minutes')

relative_coords = \
[
    [[X[i], Y[j]] for j in range(len(Y))] 
     for i in range(len(X))
]

for i in range(1, len(relative_coords), 2):
    relative_coords[i] = relative_coords[i][::-1]

begining_of_fiber_coord = p0*[1, 0.5] + p1*[0, 0.5]     # beginning of relative coordinate system in rotated coord system.   

direction_signs = np.sign(p1-p0)*[1, -1]    # directions for increasing coordinates


@ex.automain
def touch_sensor(_run):
    safe_hight = config['safe_hight']/1e3

    c_state = rtde_r.getActualTCPPose()
    if c_state[2] < safe_hight:
        rtde_c.moveL(c_state[:2] + [safe_hight] + c_state[3:6], *config['speed'])
    
    net_save_hight = safe_hight
    

    for point_line in relative_coords:
        for rel_point in point_line:
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
                             'inner_powers': [],
                             'power_error': [],
                             'inner_tenso_signals': [],
                             }
            

            c_state = rtde_r.getTargetTCPPose()
            rtde_c.moveL(c_state[:2] + [net_save_hight] + c_state[3:6], *config['speed'])
            rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])
            
            if config['sensor_hight'] - config['max_sensor_depth'] < config['minimal_possible_hight']:
                raise ValueError("Robot was going to go to low. It can be dangerous for fiber! \nChange 'minimal_possible_hight' to continue.")
            target_depthes = np.linspace(config['sensor_hight'], 
                                         config['sensor_hight'] - config['max_sensor_depth'],
                                         config['sensor_depth_points'], 
                                         endpoint=True)/1e3
            
            # for depth in np.concatenate([target_depthes, target_depthes[::-1]]):
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
                    p = float(rsrc.query('measure:power?'))
                    inner_powers.append(p)
                    # _run.log_scalar("all_powers", p)
                point_results['inner_powers'].append(inner_powers[::10])
                inner_powers = np.array(inner_powers)
                
                power = inner_powers.mean()
                _run.log_scalar('power', power)
                point_results['final_power'].append(power)
                point_results['power_error'].append(np.sqrt(np.mean((inner_powers-power)**2)))
                
                ## logging
                point_results['base_coordinate'].append(rtde_r.getActualTCPPose())
                point_results['vector_force'].append(rtde_r.getActualTCPForce())

                point_results['z_coord'].append(depth)
                _run.log_scalar('z_coord', depth)
                                    
                tenso_string = arduino.read_all()
                tenso_values = tenso_string.split()
                point_results['inner_tenso_signals'].append(tenso_values)
                if (len(tenso_values) == 0):
                    tenso_value = None
                else:
                    try:
                        tenso_value = np.mean( [float(x) for x in tenso_values[-1:]])
                    except ValueError:
                        tenso_value = None
                point_results['tenso_signal'].append(tenso_value)
                _run.log_scalar("tenso_signal", tenso_value)
                
                
            _run.log_scalar('point_results', point_results)
            rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])
            
