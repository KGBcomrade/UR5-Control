import numpy as np
import yaml
import time


params_file = 'slip_code/p_slip.yaml'

with open(params_file) as conf_file:
    config = yaml.safe_load(conf_file)
    
# параметры (внутри params_file):

L = config['L']    # m, на сколько роботу подниматься
up_speed = config['up_speed']  # m/s, m/s^2 скорость подъема

come_back = config['come_back']    # опускаться ли обратно после завершения
back_speed = config['back_speed']     # m/s, m/s^2 скорость возвращения

use_thorlab_powermeter = False

## sacred staff
import os
import dotenv; dotenv.load_dotenv()
from sacred import Experiment
from sacred.observers import MongoObserver, FileStorageObserver
import pymongo
ex = Experiment('slipping test')
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
    # input("WARNING! No password for db. Confirm logging locally")
    print("WARNING! Logging locally")


ex.add_config(params_file)
## Robot init
import rtde_control
import rtde_receive
rtde_c = rtde_control.RTDEControlInterface(config['ip'])
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'], frequency=50)

if use_thorlab_powermeter:
    # init PowerMeter
    import pyvisa

    rm = pyvisa.ResourceManager()

    rsrc = rm.open_resource(config['power_meter_address'],
                                    read_termination='\n')

def modul(vector):
    return np.sqrt(np.sum([x*x for x in vector]))

@ex.automain
def touch_sensor(_run):

    initial_state = rtde_r.getTargetTCPPose()
    target_state = initial_state[0:2] + [initial_state[2] + L] + initial_state[3:6]
    
    rtde_c.moveL(target_state, *up_speed, asynchronous=True)
    
    
    
    c_state = rtde_r.getTargetTCPPose()
    i = 0
    while (initial_state[2]+L > 0.01+c_state[2]):
        i+=1
        c_state = rtde_r.getTargetTCPPose()

        ## logging
        if i%20 == 0:
            _run.log_scalar('tsp_pose', rtde_r.getActualTCPPose())
            _run.log_scalar('tsp_speed', rtde_r.getActualTCPSpeed())
            _run.log_scalar('target_speed', rtde_r.getTargetTCPSpeed())
            _run.log_scalar('tsp_force', rtde_r.getActualTCPForce())
                    
            _run.log_scalar('abs_tsp_speed', modul(rtde_r.getActualTCPSpeed()))
            _run.log_scalar('abs_target_speed', modul(rtde_r.getTargetTCPSpeed()))
            _run.log_scalar('abs_tsp_force', modul(rtde_r.getActualTCPForce()))
        
        if use_thorlab_powermeter:
            p = float(rsrc.query('measure:power?'))
            _run.log_scalar("all_powers", p)
        else:
            time.sleep(0.01)
                
        
    if come_back:
        rtde_c.moveL(initial_state, *back_speed)
            
