# IoToy 3D Render:

This is a project I made for [University of Edinburgh's IoT Group](http://iot.ed.ac.uk/) during my time as a software Engineer intern in summer 2019. This project is a beta version of IoToy. The alpha edition is now widely used in primary and secondary schools across Edinburgh to aid workshops in **data science** and **Internet of Things**.

A raspberry pi Zero is connected to an accelerometer and hosts an MQTT server. We can use the **recievePi4.py** python file on our laptop to run a real-time 3D rendering of a teddy bear.

A working demo can be found [here](https://www.youtube.com/watch?v=ObJK_eU24yU)

![Screenshot of teddy bear](screenshot-teddy.png)

## Instructions:
- Connect Raspberry Pi Zero to an accelerometer. We recommend using BNO055.
- Install requirements in Raspberry Pi Zero and run ``sendPi0.py``.
- In a laptop or a raspberry 4 install the requirements and run ``recievePi4.py``.