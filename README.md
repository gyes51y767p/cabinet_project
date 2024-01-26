# IoT Cabinet Doors Monitor
This project uses [Raspberry Pi](https://www.raspberrypi.com/) and [IoT](https://en.wikipedia.org/wiki/Internet_of_things) to monitor cabinet doors
in real-time. A magnetic switch signals an ESP32 to send 
status changes to an [MQTT server](https://mqtt.org/). The [ESP32](https://www.espressif.com/en/products/socs/esp32) conserves power
in idle times, and the Raspberry Pi plays custom sounds
upon receiving MQTT notifications.


# Motivation
This project came to life because of our quirky roommate
habits. The mission? Cook up a clever notification system 
to remind the last person to close those pesky cabinet doors.
Let them become a better <span style="font-family:Papyrus; font-size:30px; color:green;">PERSON!</span> again!


# Table of contents
1. [Getting Started](#getting-started)
2. [Final product](#project-images)
3. [Project images](#project-images)
4. [Quick Start](#quick_start)
5. [Future work](#future-work)
6. [Contributing](#contributing)


# Getting Started <a name="getting-started"></a>

To clone the repository, run the following command:

```bash
git clone git@github.com:gyes51y767p/cabinet_project.git
```
# Quick Start <a name="quick_start"></a>
Recommend Python 3.9 or higher here. 
There is no expectation that it won't work with future versions. 
We need a version of Python that is compatible with the paho.mqtt library.

For ESP32:
* In this project, we use [HiveMQ](https://www.hivemq.com/) for MQTT server
* Use the scirpt for esp32 form [here](door_sensor/door_sensor.ino)
* Open the script in Arduino IDE and edit the personal password and subscribe/publish topic
* Upload the script to ESP32
* Connect the ESP32 to the magnetic switch and power supply
* Done!

For Raspberry Pi:
* Use the script for Raspberry Pi from [here](musicbox/musicbox.py)
* Open terminal to musicbox folder
* Create a python 3.9 virtual environment
```bash
python3.9 -m venv env
source env/bin/activate
./setup.sh              # install dependencies including supervisord to run in background when the machine boot
pip install -r requirements.txt
``` 
* Open musicbox.py and edit the MQTT server address, username, password, and subscribe/publish topic
* Customize your notification sound to <span style="font-family:Papyrus; font-size:30px;">REMIND ROOMMATES!</span>


# Project images <a name="project-images"></a>
![final view.jpg](musicbox%2Fworking_process_images%2Ffinal%20view.jpg)
[more images](musicbox/working_process_images/)

# Future work<a name="future-work"></a>
Apply to other applications such as: garage door, fridge door, etc.

# 👏 Contributing<a name="contributing"></a>


Would love your help! Contribute or advises by raising issue and opening pull requests. 
