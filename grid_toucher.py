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
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'])

## init PowerMeter
import pyvisa

rm = pyvisa.ResourceManager()

rsrc = rm.open_resource(config['power_meter_address'],
                                read_termination='\n')

## init Arduino
import serial
arduino = serial.Serial(port=config['arduino_address'], baudrate=115200, timeout=.1)

@ex.automain
def touch_sensor(_run):

    c_state = rtde_r.getActualTCPPose()
    if c_state[2] < config['safe_hight']:
        rtde_c.moveL(c_state[:2] + [config['safe_hight']] + c_state[3:6], *config['speed'])
    
    net_step=config['grid']['steps']
    p0 = config['left_upper_corner']
    p1 = config['right_down_corner']
    net_step[0] *= np.sign(p1[0]-p0[0])
    net_step[1] *= np.sign(p1[1]-p0[1])
    shape = [int((p1[0]-p0[0])//net_step[0]+1), int((p1[1]-p0[1])//net_step[1]+1)]
    print("Shape is", shape)
    net_save_hight = config['safe_hight']

    net_corner = p0
    net_massive = [
        [ [net_corner[0]+i*net_step[0], net_corner[1]+j*net_step[1]]
        for i in range(shape[0])]
        for j in range(shape[1])
    ]
    for i in range(1, len(net_massive), 2):
        net_massive[i] = net_massive[i][::-1]
        
    for point_line in net_massive:
        for point in point_line:
            print(point)
            point_results = {"target_coordinate": point,
                             "base_coordinate":[],
                             "vector_force":[],
                             "deformation":[],
                             "base_coordinate":[],
                             'tenso_signal': [],
                             'final_power': [],
                             }
            
            rtde_r.disconnect()
            rtde_r.reconnect()
    
            c_state = rtde_r.getTargetTCPPose()
            rtde_c.moveL(c_state[:2] + [net_save_hight] + c_state[3:6], *config['speed'])
            rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])
            
            target_depthes = np.linspace(config['sensor_hight'], 
                                         config['sensor_hight'] - config['max_sensor_depth'],
                                         config['sensor_depth_points'], 
                                         endpoint=True)
            
            for depth in target_depthes:
                ## moving
                rtde_c.moveL(point + [depth] + c_state[3:6], *config['speed'])
                time.sleep(config['wait_time'])
                ## logging
                point_results['base_coordinate'].append(rtde_r.getActualTCPPose())
                point_results['vector_force'].append(rtde_r.getActualTCPForce())

                point_results['deformation'].append(depth)
                _run.log_scalar('deformation', depth)
                                    
                tenso_string = arduino.read_all()
                tesno_values = tenso_string.split()
                if (len(tesno_values) == 0):
                    tenso_value = None
                else:
                    tenso_value = float(tesno_values[-1])
                point_results['tenso_signal'].append(tenso_value)
                _run.log_scalar("tesno_signal", tenso_value)
                
                power = float(rsrc.query('measure:power?'))
                _run.log_scalar('power', power)
                point_results['final_power'].append(power)
                
                
            _run.log_scalar('point_results', point_results)
            rtde_c.moveL(point + [net_save_hight] + c_state[3:6], *config['speed'])
            
