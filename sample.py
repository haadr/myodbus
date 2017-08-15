

from myodbus import MyoDbus

import numpy
import argparse
import struct
import dbus 

from dbus.mainloop.glib import DBusGMainLoop, threads_init
from gi.repository import GLib

################################################################################
#### Args
################################################################################
parser = argparse.ArgumentParser(description='Sample program for connecting to, configuring and reading sensor values from a Myo IMU sensor.')
parser.add_argument('--sleep', dest='sleep', action='store_true')
parser.add_argument('--myopath', dest='myopath', required=True, help="dbus path to Myo device. Example: /org/bluez/hci1/dev_XX_XX_XX_XX_XX_XX")
parser.set_defaults(sleep=False)
args = parser.parse_args()

################################################################################
#### Callback function
################################################################################

def handleIMU( interfaceName, payload, arrayOfString, myo_basepath=None):
    
    print("\n################################################################################") 
    print("From Myo with path: {}".format(myo_basepath[:37]))
    print("handleIMU arguments: \n\tInterface name: {}\n\tData: {}\n\t{}".format(interfaceName, payload,  arrayOfString))
    # Unpack sensor values
    rb = payload['Value']
    
    MYOHW_ORIENTATION_SCALE = 16384.0
    MYOHW_ACCELEROMETER_SCALE = 2048.0
    MYOHW_GYROSCOPE_SCALE = 16.0
    
    vals = struct.unpack('10h', rb)
    
    quat = vals[:4]
    acc = vals[4:7]
    gyr = vals[7:10]

    acc = [ a * MYOHW_ACCELEROMETER_SCALE for a in acc ]
    gyr = [ g * MYOHW_GYROSCOPE_SCALE for g in gyr ]
    
    quat = [ q * MYOHW_ORIENTATION_SCALE for q in quat ]
    magnitude = numpy.sqrt( sum( [quat[i]*quat[i] for i in range(len(quat))] ) )

    for i,q in enumerate(quat):
        quat[i] = q/magnitude

    print("quat: {}\nacc: {}\ngyro: {}".format( quat, acc, gyr) )
    print("################################################################################") 

################################################################################
#### Event loop
################################################################################
DBusGMainLoop(set_as_default=True)
loop = GLib.MainLoop()
# Get system bus
bus = dbus.SystemBus()

if __name__ == '__main__':
    # New Myo
    myo = MyoDbus(bus, args.myopath)

    # Connect and configure
    myo.connect(wait=True, verbose=True)
    myo.lock()
    myo.setNeverSleep() 
    
    myo.subscribeToIMU()
    myo.attachIMUHandler( handleIMU )
    myo.enableIMU()
    
    print("Battery: {}%".format( myo.getBatterLevel() ) )

    # Start main loop
    try:
        print("Running event loop! Press Ctrl+C to exit...")
        loop.run()
        
    except KeyboardInterrupt:
        print("Shutting down...")
        loop.quit()

        print("Disconnecting...")
        myo.unsubscribeFromIMU()
        myo.disableIMU_EMG_CLF()
        myo.vibrate(duration='short')
        if args.sleep:
            print("Setting Myo to deep sleep...")
            myo.setDeepSleep()
