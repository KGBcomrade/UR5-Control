import rtde_control
import rtde_receive
import time

host = "10.201.2.179"
import numpy as np

rtde_r = rtde_receive.RTDEReceiveInterface(host)
rtde_r.isConnected()

rtde_c = rtde_control.RTDEControlInterface(host)

for i in range(10):
    # time.sleep(1)
    print("Disconnection", rtde_r.disconnect())
    print("reconnection", rtde_r.reconnect())
    
    pos = rtde_r.getActualTCPPose()
    new_pos = rtde_r.getActualTCPPose()
    new_pos[0] += -.01
    rtde_c.moveL(new_pos)
    new_getter = rtde_r.getActualTCPPose()
    print("new 'acctual' pose", new_getter)
    print("old pose          ", pos)
    print("target pos        ", rtde_r.getTargetTCPPose())

