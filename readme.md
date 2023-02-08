

## Run instruction
To test sensor with robot configure in params.yaml:
 - robot ip
 - sensor corners in robot system
 - power_meter usb address (find it by running
  ```
import pyvisa

rm = pyvisa.ResourceManager()
for addr in rm.list_resources():
    print(addr, '-->', rm.open_resource(addr).query('*IDN?').strip())
 ```
 - arduino address (find it by "ls /dev/ttyACM*" command)

Then run grid_toucher.py file. The result of touching will be send to log_database if there is **.env** file with passwords in root folder(it also requires crt sertificate "mkdir /usr/local/share/ca-certificates/Yandex &&
wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O /usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt").

To read data from Thorlab PowerMeter you have to install python PyVisa library through pip.

For pyvisa I also installed pyvisa-py backend with pip, libusb (or PyUSB) for usb access and allowed listening usb ports like here https://stackoverflow.com/questions/66480203/pyvisa-not-listing-usb-instrument-on-linux

To log to database

![](https://storage.yandexcloud.net/monthly-reports/September%202022/Amir/photo1666609449.jpeg)

(Пояснение к смыслу параметров протыкивания)


### Update 8.02.2023:
В новой системе используется задание положения через номер дырки в столе, в которую вкручен сенсор. 
Появилась промежуточная программа для автоматического определения высоты сенсора.
Появилась возможность указывать при запуске кастомный файл конфига для предварительной подготовки нужных параметров для нескольких сенсоров.


1. В скрипте `print_params.yaml` производится перевод из более удобных человеку координат в номере дырки в столбце и в строке в строку, которую нужно вставить в .yaml файл с параметрами.
2. Программа для определения высоты сенсора `find_sensor_hight.py`.\
Можно настроить в программе:
 - `config['safe_hight']` высоту начиная с которой робот быдет опускаться 
 - `config['minimal_possible_hight']` высоту, ниже которой он ни в коем случае не должен опуститься
 - `depth_step` шаг, с которым робот будет опускаться (не бошьше 0.1 мм, а финальную настройку лучше на 0.02 мм проводить)
 Lkz pfgecrf ghjuhfvvsghjnsrbdfybz
 3.  Для запуска протыкивания и теста высоты сейчас нужно использовать такие команды
 ```
 sudo /home/robot/anaconda3/envs/amir/bin/python /home/robot/Amir/UR5-Control2/find_sensor_hight.py -c 804hight.yaml
 ```
 Будет выбран файл параметров 804hight.yaml.    

Памятка для натройки конфиг файла:
 - скопировать файл p_main.yaml в файл с нужным названием.
 - указать id сенсора
 - указать определенную через программу высоту сенсора.