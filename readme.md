

## Run instruction
To test sensor with robot configure in params.yaml:
 - robot ip
 - sensor corners in robot system
 - power_meter usb address (find it by running
  ```
import pyvisa

rm = pyvisa.ResourceManager()
for addr in rm.list_resources()
    print(addr, '-->', rm.open_resource(addr).query('*IDN?').strip())
 ```
 - arduino address (find it by lsusb command)

Then run grid_toucher.py file. The result of touching will be send to log_database if there is **.env** file with passwords in root folder.

To read data from Thorlab PowerMeter you have to install python PyVisa library through pip.

For pyvisa I also installed pyvisa-py backend with pip, usblib for usb access and allowed listening usb ports like here https://stackoverflow.com/questions/66480203/pyvisa-not-listing-usb-instrument-on-linux