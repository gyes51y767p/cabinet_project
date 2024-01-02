import threading
import time
import paho.mqtt.client as paho
from paho import mqtt
import subprocess
import os
import signal
import platform
import logging

logging.basicConfig(level=logging.DEBUG)


DOOR_CLOSED="closed"
DOOR_OPEN="open"
door_state = DOOR_CLOSED
last_door_state = DOOR_CLOSED
music_is_playing = False
music_start_delay=5


# setting callbacks for different events to see if it works, the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    logging.info("CONNACK received with code %s." % rc)

# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    logging.info("mid: " + str(mid))

# which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logging.info(f"client: {client}, userdata: {userdata}, mid: {mid}, granted_qos: {granted_qos}, properties: {properties}")
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

# when receiving a message, update the global variable
def on_message(client, userdata, msg):
    global door_state
    new_door_state = msg.payload.decode('utf-8')

    if msg.topic == "/door1":
        if new_door_state in [DOOR_CLOSED, DOOR_OPEN]:
            door_state = new_door_state
        else:
            logging.info("invalid payload")
    logging.info(f"topic: {msg.topic}, message: {new_door_state}")

#play the sound if the door is open for more than music_start_delay seconds
def play_mp3(file_path):
    global door_state


    play_cmd=['afplay']
    play_cmd.append(file_path)
    if platform.system()=='Linux':
	#play_cmd=["mpg123","-q"]
        play_cmd=f"mpg123 -q {file_path}"
    for _ in range(music_start_delay):
        time.sleep(1)
        if door_state==DOOR_CLOSED:
            break
    while True and door_state==DOOR_OPEN:
    	#p=subprocess.Popen(play_cmd,stdout=subprocess.PIPE)
        #p=subprocess.Popen(play_cmd)
        #p=subprocess.Popen(play_cmd,stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        p=subprocess.Popen(play_cmd,
		    shell=True, 
		    stdout=subprocess.PIPE, 
		    stderr=subprocess.PIPE)
        #when the music is playing, check if the door is closed
        while p.poll() is None:
            time.sleep(0.5)
            if door_state==DOOR_CLOSED:
                logging.info(f"play_mp3 music stopping")
                os.kill(p.pid, signal.SIGTERM)
                break
        if p.returncode == 0:
            logging.info('Music player ended with success')
        else:
            logging.info('Music player ended with failure')
        p.wait()
    logging.info(f"exit play_mp3")

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set("gyes51y767p", "@Mm5648970")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message
#client.on_publish = on_publish

client.subscribe("/door1", qos=1)

# a single publish, this can also be done in loops, etc.
# client.publish("encyclopedia/temperature", payload="hot", qos=1)

# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop

client.loop_start()
mp3_file = "sound1.mp3"
try:
    while True:
            time.sleep(1)
            if door_state != last_door_state:
                if music_is_playing and door_state == DOOR_CLOSED:
                    logging.info("door closed")
                    if music_is_playing:
                        play_thread.join()
                        music_is_playing=False
                elif door_state == DOOR_OPEN:
                    logging.info("door open")
                    if not music_is_playing:
                        play_thread = threading.Thread(target=play_mp3, args=(mp3_file,))
                        play_thread.start()
                        music_is_playing=True
                else:
                    logging.info("invalid door state")
                last_door_state = door_state
except Exception as e:
    client.loop_stop()
    client.disconnect()
    logging.info("exit")
