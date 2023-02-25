'''
Поворачивает клешню робота ровно вертикально. 
'''

import yaml

with open('p_main.yaml') as conf_file:
    config = yaml.safe_load(conf_file)
    
## Robot init
import rtde_control
import rtde_receive
rtde_c = rtde_control.RTDEControlInterface(config['ip'])
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'], frequency=50)
print(rtde_r.getRobotStatus())

print(rtde_r.getActualTCPPose())
c_pose = rtde_r.getActualTCPPose()
new_pose = c_pose[0:3] + [2.222, -2.222, 0]

rtde_c.moveL(new_pose, *config['speed'])
# rtde_r.getActualJointPositionsHistory
print(rtde_r.getActualTCPPose())