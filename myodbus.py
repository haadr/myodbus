from __future__ import print_function

import dbus
import sys
import time

""" Constants
See https://github.com/thalmiclabs/myo-bluetooth/blob/master/myohw.h for
explanations.
"""

# Commands
VIBRATE_CMD_S = [ dbus.Byte(3),dbus.Byte(1),dbus.Byte(1)  ]
VIBRATE_CMD_M = [ dbus.Byte(3),dbus.Byte(1),dbus.Byte(2)  ]
VIBRATE_CMD_L = [ dbus.Byte(3),dbus.Byte(1),dbus.Byte(3)  ]


ENABLE_IMU_CLF_CMD = dbus.ByteArray(b'\x01\x03\x00\x01\x01')
ENABLE_IMU_CMD     = [ dbus.Byte(1), dbus.Byte(3),  dbus.Byte(0),  dbus.Byte(1), dbus.Byte(0) ]
DISABLE_IMU_CMD    = dbus.ByteArray( b' \x01\x03\x00\x00\x00'  )


NEVER_SLEEP_CMD  = dbus.ByteArray( b'\x09\x01\x01' )
NORMAL_SLEEP_CMD = dbus.ByteArray( b'\x09\x01\x00' )
DEEP_SLEEP_CMD   = dbus.ByteArray( b'\x04\x00' )

# Related to pose classification
UNLOCK_CMD = dbus.ByteArray(b'\x0a\x01\x02')
LOCK_CMD = dbus.ByteArray(b'\x0a\x01\x00')
BLANK_CMD = dbus.ByteArray( b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' )

# Paths
# Bluez and Gatt protocol dbus services and paths
DBUS_PROP_IFACE         = "org.freedesktop.DBus.Properties"
BLUEZ_DEV_IFACE         = 'org.bluez.Device1'
BLUEZ_GATT_CHAR_IFACE   = 'org.bluez.GattCharacteristic1'
BLUEZ_NAME              = 'org.bluez'

BATTERY_LEVEL_CHAR_PATH = '/service000f/char0010'
COMMAND_CHAR_PATH       = "/service0013/char0018"
IMU_VAL_CHAR_PATH       = "/service001a/char001b"


class MyoDbus(object):
    """ Implements the dbus interface to a Myo """
    def __init__(self, system_bus, myo_path):
        self.system_bus = system_bus
        self.myo_basepath = myo_path
        self.myo_name = None

        # Try to init
        self.myo_obj      = self.system_bus.get_object(BLUEZ_NAME, myo_path)
        self.myo_cmd_char = self.system_bus.get_object(BLUEZ_NAME, myo_path + COMMAND_CHAR_PATH )
        self.imu_val_char = self.system_bus.get_object(BLUEZ_NAME, myo_path + IMU_VAL_CHAR_PATH )
        self.bat_val_char = self.system_bus.get_object(BLUEZ_NAME, myo_path + BATTERY_LEVEL_CHAR_PATH )

    # TODO check proper error handling
    def connect(self, wait=None):
        print("Connecting...")
        try:
            self.myo_obj.Connect(dbus_interface=BLUEZ_DEV_IFACE)
        except Exception as instance:
            print("Connection failed: {}".format( instance.args[0]  ) )
            if "org.freedesktop.DBus.Error.UnknownObject" in "{}".format( instance ):
                print("Error: Device not found at the specified path: {}".format( self.myo_basepath ))
                sys.exit(-1)

        else:
            # Check if it's actually up and populated in dbus/bluez
            if(wait):
                print("Connected, waiting to make sure the dbus objects are ready ")

                while(True):
                    if(self.isConnected):
                        break
                    else:
                        print(".", end='')
                        time.sleep(.1)

            self.myo_name = self.getName()
            self.vibrate(duration="short")
            print("Done waiting, sensor {} is ready".format(self.myo_name))

    def disconnect(self):
        try:
            self.myo_obj.Disconnect(dbus_interface=BLUEZ_DEV_IFACE)
            print("Disconnected: {}".format( self.myo_basepath))
        except:
            print("Disconnect failed: {}".format( sys.exc_info()[0] ) )
            raise

    def isConnected(self):
        try:
            if self.myo_obj.GetAll(BLUEZ_DEV_IFACE,dbus_interface=DBUS_PROP_IFACE )['Connected'] == 0:
                return False
            else:
                return True
        except Exception as e:
            print("Exception in isConnected: {}".format(e))
            return False

    """ Command functions """
    def vibrate(self, duration=None):
        global VIBRATE_CMD_S
        global VIBRATE_CMD_M
        global VIBRATE_CMD_L

        if(duration is None):
            cmd = VIBRATE_CMD_S
        elif (duration == "short"):
            cmd = VIBRATE_CMD_S
        elif (duration == "medium"):
            cmd = VIBRATE_CMD_M
        elif (duration == "long"):
            cmd = VIBRATE_CMD_L

        try:
            self.myo_cmd_char.WriteValue( cmd , {}, dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Failed to vibrate: {}".format( sys.exc_info()[0] ) )
            raise

    def unlock(self):
        global UNLOCK_CMD

        try:
            self.myo_cmd_char.WriteValue( UNLOCK_CMD , {}, dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Unlock failed: {}".format( sys.exc_info()[0] ) )

    def lock(self):
        global LOCK_CMD
        try:
            self.myo_cmd_char.WriteValue( LOCK_CMD , {}, dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Lock failed: {}".format( sys.exc_info()[0] ) )

    def subscribeToIMU(self):
        try:
            self.imu_val_char.StartNotify(dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Failed to subscribe to IMU: {}".format( sys.exc_info()[0] ) )

    def unsubscribeFromIMU(self):
        try:
            self.imu_val_char.StopNotify(dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Failed to unsubscribe from IMU: {}".format( sys.exc_info()[0] ) )

    def attachIMUHandler(self, func ):
        try:
            self.imu_val_char.connect_to_signal( "PropertiesChanged", func, byte_arrays=True, path_keyword='myo_basepath' )
        except:
            print("Failed to connect function to IMU signal. {}".format( sys.exc_info()[0] ) )

    def enableIMU(self):
        global ENABLE_IMU_CMD
        try:
            self.myo_cmd_char.WriteValue(ENABLE_IMU_CMD, {}, dbus_interface=BLUEZ_GATT_CHAR_IFACE)
        except:
            print("Failed to enable IMU: {}".format( sys.exc_info()[0] ) )

    def disableIMU_EMG_CLF(self):
        global DISABLE_IMU_CMD
        self.sendCommand( DISABLE_IMU_CMD )

    def sendCommand(self, cmd, reply_hnd=None, error_hnd=None):
        try:
            self.myo_cmd_char.WriteValue( cmd , {}, dbus_interface=BLUEZ_GATT_CHAR_IFACE, reply_handler=reply_hnd, error_handler=error_hnd)
        except dbus.exceptions.DBusException as instance:
            if "Did not receive a reply." in instance.args[0]:
                return
            print("Command {} failed: {}".format( ''.join( [str(ord(c)) for c in cmd] ) , instance.args[0] ) )

    def getBatterLevel(self):
        try:
            return ord(self.bat_val_char.ReadValue({}, dbus_interface=BLUEZ_GATT_CHAR_IFACE, byte_arrays=True ) )
        except:
            raise

    def getName(self):
        try:
            return self.myo_obj.GetAll(BLUEZ_DEV_IFACE,dbus_interface=DBUS_PROP_IFACE )['Name']
        except:
            raise

    def getSensorValue(self):
        try:
            return self.imu_val_char.ReadValue({}, dbus_interface=BLUEZ_GATT_CHAR_IFACE,byte_arrays=True)
        except:
            raise

    def setNormalSleep(self):
        global NORMAL_SLEEP_CMD
        self.sendCommand(NORMAL_SLEEP_CMD)

    def setNeverSleep(self):
        global NEVER_SLEEP_CMD
        self.sendCommand(NEVER_SLEEP_CMD)

    def setDeepSleep(self):
        global DEEP_SLEEP_CMD
        self.sendCommand(DEEP_SLEEP_CMD, reply_hnd=self.do_nothing, error_hnd=self.do_nothing)

    def do_nothing(self):
        pass
