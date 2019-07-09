import logging
import sys
import time
import paho.mqtt.publish as publish
from Adafruit_BNO055 import BNO055

bno = BNO055.BNO055(serial_port='/dev/serial0', rst=18)

if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
    logging.basicConfig(level=logging.DEBUG)

# Initialize the BNO055 and stop if something went wrong.
if not bno.begin():
    raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

# Print system status and self test result.
status, self_test, error = bno.get_system_status()
print('System status: {0}'.format(status))
print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
# Print out an error if system status is in error mode.
if status == 0x01:
    print('System error: {0}'.format(error))
    print('See datasheet section 4.3.59 for the meaning.')

# Print BNO055 software revision and other diagnostic data.
sw, bl, accel, mag, gyro = bno.get_revision()

print('Reading BNO055 data, press Ctrl-C to quit...')

while True:
    heading, roll, pitch = bno.read_euler()

    # Read the calibration status, 0=uncalibrated and 3=fully calibrated.
    sys, gyro, accel, mag = bno.get_calibration_status()
    x, y, z, w = bno.read_quaternion()
    # Heading, Roll, Pitch, sys_cal, gyro_cal, accel_cal, mag_cal.
    accel = bno.read_linear_acceleration()
    magnitude = (accel[0]**2 +  accel[1]**2 + accel[2]**2)**(1/2)

    publish.single("test/accdata",'{0} {1} {2} {3:.2f} {4:.2f} {5} {6} {7} {8} {9} {10}'.format(heading, roll, pitch, sys, gyro, accel, mag, x, y, z, w),hostname="192.168.5.1" )
    time.sleep(1)
