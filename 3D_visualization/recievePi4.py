######
## IoToy made by Gagan Devagiri for University of Edinburgh's
## IoT Research and Innovation Service
## v1.0 - 10/07/19
######


import json
import logging
import threading
import time
from flask import *
import paho.mqtt.client as mqtt
from Adafruit_BNO055 import BNO055


global datalst, recievedCheck

BNO_UPDATE_FREQUENCY_HZ = 10
app = Flask(__name__)

bno_data = {}
bno_changed = threading.Condition()
bno_thread = None
recieved_check = False


def send_bno():
    time.sleep(3)
    global datalst
    while True:
        heading = float(datalst[0])
        roll = float(datalst[1])
        pitch = float(datalst[2])
        sys = float(datalst[3])
        gyro = float(datalst[4])
        accel = float(datalst[5])
        mag = float(datalst[6])
        x, y, z, w= float(datalst[7]), float(datalst[8]), float(datalst[9]), float(datalst[10])
        with bno_changed:
            bno_data['euler'] = (heading, roll, pitch)
            bno_data['quaternion'] = (x, y, z, w)
            bno_data['calibration'] = (sys, gyro, accel, mag)
            bno_data['temp'] = 20.0
            bno_changed.notifyAll()
        time.sleep(1.0/BNO_UPDATE_FREQUENCY_HZ)
        


    

def read_bno():
    """
    Connects to the mqtt client & calls on_message
    updates dataSTR variable
    """
    def on_message(client, user_data, message):
        dataSTR = str(message.payload.decode())
        global datalst
        datalst = dataSTR.split(' ')
    client = mqtt.Client('ReadAccData')
    client.connect('192.168.5.1', 1883, 120)
    client.subscribe('test/accdata')
    client.on_message = on_message
    client.loop_forever()
    print("This should not be printed")


def bno_sse():
    """
    Generator Function. Sends sensor data to client web browser using
    server push.
    """
    while True:
        with bno_changed:
            bno_changed.wait()
            bno_data['euler']
            heading, roll, pitch = bno_data['euler']
            temp = bno_data['temp']
            x, y, z, w = bno_data['quaternion']
            sys, gyro, accel, mag = bno_data['calibration']
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
    bno_thread = threading.Thread(target=read_bno)
    sending_thread = threading.Thread(target=send_bno)

    sending_thread.daemon = True
    bno_thread.daemon = True

    sending_thread.start()
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
    app.run(host='0.0.0.0', debug=True, threaded=True)
