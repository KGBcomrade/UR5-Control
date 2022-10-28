import numpy as np
import yaml
import time

with open('params.yaml') as conf_file:
    config = yaml.safe_load(conf_file)
    
# ## Robot init
# import rtde_control
# import rtde_receive
# rtde_c = rtde_control.RTDEControlInterface(config['ip'])
# rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'], frequency=50)

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

print(p0, p1)

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

horisontal_area[1] +=net_step[0]*0.00001
vertical_area[1] +=net_step[1]*0.00001
# to include last point

X, Y = np.arange(*horisontal_area, net_step[0]), np.arange(*vertical_area, net_step[1])
print("Target coordinates are", X, Y)
shape = len(X), len(Y)
print("Shape is", shape)

relative_coords = \
[
    [[X[i], Y[j]] for j in range(len(Y))] 
     for i in range(len(X))
]


for i in range(1, len(relative_coords), 2):
    relative_coords[i] = relative_coords[i][::-1]

# print(*relative_coords, sep='\n')


begining_of_fiber_coord = p0*[1, 0.5] + p1*[0, 0.5]     # beginning of relative coordinate system in rotated coord system.   

direction_signs = np.sign(p1-p0)*[1, -1]    # directions for increasing coordinates
for point_line in relative_coords:
    for rel_point in point_line:
        point = rotor.inverse(begining_of_fiber_coord + rel_point*direction_signs)/1e3 
        # rotating back into initial coordinate system and converting to mm-s
        point = point.tolist()   
        
        print()
        print(" in rotated coordinate system", *[format(x, ".3f") for x in begining_of_fiber_coord + rel_point*direction_signs])
        
        print(*[format(x, ".0f") for x in rel_point])
        print(*[format(x, ".3f") for x in point])
        