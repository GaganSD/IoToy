import json
import logging
import threading
import time
import keyboard
from flask import *
import paho.mqtt.client as mqtt
from Adafruit_BNO055 import BNO055

# bno = BNO055.BNO055(serial_port='/dev/serial0', rst=18)

BNO_UPDATE_FREQUENCY_HZ = 10
CALIBRATION_FILE = 'calibration.json'
BNO_AXIS_REMAP = { 'x': BNO055.AXIS_REMAP_X,
                   'y': BNO055.AXIS_REMAP_Z,
                   'z': BNO055.AXIS_REMAP_Y,
                   'x_sign': BNO055.AXIS_REMAP_POSITIVE,
                   'y_sign': BNO055.AXIS_REMAP_POSITIVE,
                   'z_sign': BNO055.AXIS_REMAP_NEGATIVE }

app = Flask(__name__)


bno_data = {}
bno_changed = threading.Condition()

# Background thread to read BNO sensor data.  Will be created right before
# the first request is served (see start_bno_thread below).
bno_thread = None


def read_bno():
    """Function to read the BNO sensor and update the bno_data object with the
    latest BNO orientation, etc. state.  Must be run in its own thread because
    it will never return!
    """
    def on_message(client, user_data, message):
        dataSTR = str(message.payload.decode())
        datalst = dataSTR.split(' ')
        #print("datalst check")
        heading = float(data[0])
        print("heading")
        print(heading)
        roll = float(data[1])
        pitch = float(data[2])
        sys = float(data[3])
        gyro = float(data[4])
        accel = float(data[5])
        mag = float(data[6])
        #temp = float(data[7])
        print("about to go in bno_changed")
        x, y, z, w= float(data[7]), float(data[8]), float(data[9]), float(data[10])
        print("X, y, z, w")
        print(x, y, z, w)
        if keyboard.is_pressed('q'):
            print("'q' is pressed")
            client.disconnect()
            client.loop_stop()
            bno_data.clear()
            
        with bno_changed:
            print("inside bno_changed")
            bno_data['euler'] = (heading, roll, pitch)
            bno_data['temp'] = temp
            bno_data['quaternion'] = (x, y, z, w)
            bno_data['calibration'] = (sys, gyro, accel, mag)
            bno_data['temp'] = 20.0
            print(bno_data)
            print("bno_data should have printed")
            bno_changed.notifyAll()
            print("Notified")
        time.sleep(1.0/BNO_UPDATE_FREQUENCY_HZ)
    print("Inside client" )
    client = mqtt.Client('ReadAccData')
    client.connect('192.168.5.1', 1883, 120)
    client.subscribe('test/accdata')
    client.on_message = on_message
    client.loop_forever()
    print("This should not be printed")

        
    # while True:
    #     # Grab new BNO sensor readings.
    #     temp = bno.read_temp()
    #     heading, roll, pitch = bno.read_euler()
    #     x, y, z, w = bno.read_quaternion()
    #     sys, gyro, accel, mag = bno.get_calibration_status()
    #     status, self_test, error = bno.get_system_status(run_self_test=False)
    #     if error != 0:
    #         print 'Error! Value: {0}'.format(error)
    #     # Capture the lock on the bno_changed condition so the bno_data shared
    #     # state can be updated.
    #     with bno_changed:
    #         bno_data['euler'] = (heading, roll, pitch)
    #         bno_data['temp'] = temp
    #         bno_data['quaternion'] = (x, y, z, w)
    #         bno_data['calibration'] = (sys, gyro, accel, mag)
    #         # Notify any waiting threads that the BNO state has been updated.
    #         bno_changed.notifyAll()
    #     # Sleep until the next reading.
    #     time.sleep(1.0/BNO_UPDATE_FREQUENCY_HZ)

def bno_sse():
    """Function to handle sending BNO055 sensor data to the client web browser
    using HTML5 server sent events (aka server push).  This is a generator function
    that flask will run in a thread and call to get new data that is pushed to
    the client web page.
    """
    # Loop forever waiting for a new BNO055 sensor reading and sending it to
    # the client.  Since this is a generator function the yield statement is
    # used to return a new result.
    print("inside bno_sse")
    while True:
        # Capture the bno_changed condition lock and then wait for it to notify
        # a new reading is available.
        with bno_changed:
            print("inside while loop")
            bno_changed.wait()
            print("inside bno_changed")
            # A new reading is available!  Grab the reading value and then give
            # up the lock.
            bno_data['euler']
            heading, roll, pitch = bno_data['euler']
            temp = bno_data['temp']
            x, y, z, w = bno_data['quaternion']
            sys, gyro, accel, mag = bno_data['calibration']
            print(bno_data)
            print("sending bno_data")
        # Send the data to the connected client in HTML5 server sent event format.
        data = {'heading': heading, 'roll': roll, 'pitch': pitch, 'temp': temp,
                'quatX': x, 'quatY': y, 'quatZ': z, 'quatW': w,
                'calSys': sys, 'calGyro': gyro, 'calAccel': accel, 'calMag': mag }
        yield 'data: {0}\n\n'.format(json.dumps(data))


@app.before_first_request
def start_bno_thread():
    # Start the BNO thread right before the first request is served.  This is
    # necessary because in debug mode flask will start multiple main threads so
    # this is the only spot to put code that can only run once after starting.
    # See this SO question for more context:
    #   http://stackoverflow.com/questions/24617795/starting-thread-while-running-flask-with-debug
    global bno_thread
    # Initialize BNO055 sensor.
#    if not bno.begin():
#        raise RuntimeError('Failed to initialize BNO055!')
#    bno.set_axis_remap(**BNO_AXIS_REMAP)
    # Kick off BNO055 reading thread.
    bno_thread = threading.Thread(target=read_bno)
    bno_thread.daemon = True  # Don't let the BNO reading thread block exiting.
    bno_thread.start()

@app.route('/bno')
def bno_path():
    # Return SSE response and call bno_sse function to stream sensor data to
    # the webpage.
    return Response(bno_sse(), mimetype='text/event-stream')

@app.route('/')
def root():
    return render_template('index.html')


if __name__ == '__main__':
    # Create a server listening for external connections on the default
    # port 5000.  Enable debug mode for better error messages and live
    # reloading of the server on changes.  Also make the server threaded
    # so multiple connections can be processed at once (very important
    # for using server sent events).
    app.run(host='0.0.0.0', debug=True, threaded=True)
