# myodbus

myodbus is a simple class to connect to and use the Myo armband via the GATT protocol standard on Linux using bluez and dbus. The main class is implemented in myodbus.py, and some sample code to demonstrate its use can be found in sample.py.


## Usage:
```
python sample.py -h                                                                           
usage: sample.py [-h] [--sleep] --myopath MYOPATH                                                                             
                                                                                                                              
Sample program for connecting to, configuring and reading sensor values from a                                               
Myo IMU sensor.                                                                                                              
                                                                                                                             
optional arguments:                                                                                                          
  -h, --help         show this help message and exit                                                                         
  --sleep                                                                                                                    
  --myopath MYOPATH  dbus path to Myo device. Example:                                                                       
                     /org/bluez/hci1/dev_XX_XX_XX_XX_XX_XX
```


## Requirements/Known to work with:
- Bluez 5.43
- DBus 1.10.18
- Python 2.7.13 / Python 3.5.3
- python-dbus 1.2.4-1 / python3-dbus  1.2.4-1
