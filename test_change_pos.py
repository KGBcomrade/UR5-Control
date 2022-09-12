import rtde_control
import rtde_receive
import time

host = "10.201.2.179"
import numpy as np

rtde_r = rtde_receive.RTDEReceiveInterface(host)
rtde_r.isConnected()

rtde_c = rtde_control.RTDEControlInterface(host)

for i in range(10):
    time.sleep(1)
    
    pos = rtde_r.getActualTCPPose()
    new_pos = rtde_r.getActualTCPPose()
    new_pos[0] += -.05
    rtde_c.moveL(new_pos)
    new_getter = rtde_r.getActualTCPPose()
    print(new_getter)
    print(pos)
    print(rtde_r.getTargetTCPPose())

