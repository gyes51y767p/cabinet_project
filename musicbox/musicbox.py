#This script is running on RPI Bookworm and Bullseye 64-bit OS, python 3.9
#The command to play sound "mpg123" is not compatible with Python 3.11 which causes a "jack"-related error
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

user="doorman"
pswd="!@#$1Sastupidphrase"
DOOR_CLOSED="closed"
DOOR_OPEN="open"
door_state = DOOR_CLOSED
last_door_state = DOOR_CLOSED
music_is_playing = False
music_start_delay=5
music_sources_path="sounds"
doors_Object_List = {}

door_configs={
    "pantry": {
        "door_state": DOOR_CLOSED, #do we need this?
        "initial_delay": 30,#do we need this?
        "music_list": [
            {"music_file_path": "gentle_pantry.mp3",
                 "repeat_times": 3,#do we need this?
                 "volume": "-6000",#do we need this?
                 "delay_to_next": 20 },#do we need this?
            {"music_file_path": "pantry_smooth.mp3",
                 "repeat_times": 1,
                 "volume": "-10000",
                 "delay_to_next": 20},
            {"music_file_path": "pantry_furious.mp3",
                 "repeat_times": 0,
                 "volume": "-20000" ,
                 "delay_to_next": 20 }
        ]
    },

    "sauces": {
        "door_state": DOOR_CLOSED,#no need
        "initial_delay": 30,
        "music_list": [
            {"music_file_path": "gentle_sauce.mp3",
                 "repeat_times": 3,
                 "volume": "-6000",
                 "delay_to_next": 20},
            {"music_file_path": "sauce_smooth.mp3",
                 "repeat_times": 1,
                 "volume": "-10000",
                 "delay_to_next": 20},
            {"music_file_path": "sauce_furious.mp3",
                 "repeat_times": 0,
                 "volume": "-20000",
                 "delay_to_next": 20 }
        ]
    }
}

class Door:
    def __init__(self, door_name, new_door_state,door_info_from_config):
        self.door_name = door_name
        self.door_state = new_door_state
        self.door_last_door_state = "close"
        self.door_music_is_playing = False
        # self.door_music_start_delay = door_music_start_delay
        self.door_music_files = door_info_from_config["music_list"]
        self.door_music_thread = None
        self.door_is_open_that_moment=time.time()
        self.door_is_open_total_time=time.time()
# class Door:
#    def open_door:(self):
#         self.door_open=True
#         self.times_played=0
#
#
# for door_name in [ door_configs ]
def update_door_state(door_Object,new_door_state):
    if new_door_state in [DOOR_CLOSED, DOOR_OPEN]:
        door_Object.door_state = new_door_state
        # door_Object.door_is_open_that_moment=time.time()
        # door_Object.door_last_door_state = new_door_state
    else:
        logging.info("invalid new_door_state received")


# setting callbacks for different events to see if it works, the message etc.

def on_connect(client, userdata, flags, rc, properties=None):
    logging.info("CONNACK received with code %s." % rc)

# which topic was subscribed to, only print the first time that script run
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logging.info(f"client: {client}, userdata: {userdata}, mid: {mid}, granted_qos: {granted_qos}, properties: {properties}")
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

# when receiving a message, update the global variable
def on_message(client, userdata, msg):
    # global door_state
    new_door_state = msg.payload.decode('utf-8')
    door_name=msg.topic.split("/")[-1]
    if door_name not in doors_Object_List:
        doors_Object_List[door_name]=Door(door_name,new_door_state,door_configs[door_name])
        logging.info(f"door_name: {door_name} appended to doors_Object_List")

    else:
        update_door_state(doors_Object_List[door_name],new_door_state)


#play the sound if the door is open for more than music_start_delay seconds
def play_mp3(cur_door):
    play_cmd = ['afplay']
    # play_cmd.append(f"{os.path.abspath('sounds')}/{cur_door.door_music_files[0]['music_file']}")
    # test_cmd1=['afplay',f"{os.path.abspath('sounds')}/{cur_door.door_music_files[0]['music_file']}"]
    # test_cmd2=['afplay',f"{os.path.abspath('sounds')}/{cur_door.door_music_files[1]['music_file']}"]
    if platform.system() == 'Linux':
        play_cmd = ["mpg123", "-q", "-f", "-2000", "-o", "alsa:hw:1,0"]
    for i in range(music_start_delay):
        time.sleep(1)
        if cur_door.door_state == DOOR_CLOSED:
            break
    while True and cur_door.door_state == DOOR_OPEN:
        cur_door.door_is_open_total_time=time.time()
        total_time=cur_door.door_is_open_total_time-cur_door.door_is_open_that_moment
        logging.info(f"total time: {total_time}")
        time.sleep(1)
        #there are three if statement  may create the function for it to handle the total time and have diffenct output and music
        if total_time >6 and total_time<20 : #play gentle sound
            logging.info(f"playing sound now and the time is {total_time}")
            if f"{os.path.abspath('sounds')}/{cur_door.door_music_files[0]['music_file_path']}" not in play_cmd:
                play_cmd.append(f"{os.path.abspath('sounds')}/{cur_door.door_music_files[0]['music_file_path']}")
            logging.info(f"play_cmd: {play_cmd}")
            p = subprocess.Popen(play_cmd,# remvoeber change to play_cmd for rpi
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            # when the music is playing, check if the door is closed
            while p.poll() is None:
                logging.info(f"playing sound now the door is open for more than 6 less than 20")
                time.sleep(2)# was 0.5 in old code
                if cur_door.door_state == DOOR_CLOSED:
                    logging.info(f"play_mp3 music stopping")
                    os.kill(p.pid, signal.SIGTERM)
                    break
            if p.returncode == 0:
                logging.info('Music player ended with success')
            else:
                logging.info('Music player ended with failure')
            p.wait()
        if total_time >=20 and total_time <40 :
            play_cmd=play_cmd[:-1]#any better way?
            play_cmd.append(f"{os.path.abspath('sounds')}/{cur_door.door_music_files[1]['music_file_path']}")
            logging.info(f"playing sound now  and the time is {total_time}")
            p = subprocess.Popen(play_cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            # when the music is playing, check if the door is closed
            while p.poll() is None:
                logging.info(f"playing sound now the door is open for more than 20 less than 100")
                time.sleep(2)#change back to 0.5 from old code
                if cur_door.door_state == DOOR_CLOSED:
                    logging.info(f"play_mp3 music stopping")
                    os.kill(p.pid, signal.SIGTERM)
                    break
            if p.returncode == 0:
                logging.info('Music player ended with success')
            else:
                logging.info('Music player ended with failure')
            p.wait()

    logging.info(f"exit play_mp3")




    # old code
    # global door_state
    #
    # play_cmd=['afplay']
    # play_cmd.append(file_path)
    # if platform.system()=='Linux':
    #     play_cmd=["mpg123","-q",f"{file_path}"]
    # for _ in range(music_start_delay):
    #     time.sleep(1)
    #     if door_state==DOOR_CLOSED:
    #         break
    # while True and door_state==DOOR_OPEN:
    #     p=subprocess.Popen(play_cmd,
	# 	    stdout=subprocess.PIPE,
	# 	    stderr=subprocess.PIPE)
    #     #when the music is playing, check if the door is closed
    #     while p.poll() is None:
    #         time.sleep(0.5)
    #         if door_state==DOOR_CLOSED:
    #             logging.info(f"play_mp3 music stopping")
    #             os.kill(p.pid, signal.SIGTERM)
    #             break
    #     if p.returncode == 0:
    #         logging.info('Music player ended with success')
    #     else:
    #         logging.info('Music player ended with failure')
    #     p.wait()
    # logging.info(f"exit play_mp3")

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(user, pswd)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", 8883)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message

client.subscribe("/door/pantry", qos=1)
client.subscribe("/door/sauces", qos=1)

# loop_forever for simplicity, here you need to stop the loop manually
# you can also use loop_start and loop_stop
client.loop_start()
mp3_file = "sound1.mp3"
try:
    while True:
        if doors_Object_List:
            time.sleep(1)
            for each_door in doors_Object_List:
                cur_door=doors_Object_List[each_door] #extract the door object

                if cur_door.door_state!=cur_door.door_last_door_state:
                    if cur_door.door_music_is_playing and cur_door.door_state==DOOR_CLOSED:
                        logging.info(f"{cur_door.door_name} closed")
                        if cur_door.door_music_is_playing:
                            cur_door.door_music_thread.join()
                            cur_door.door_music_is_playing=False
                    elif cur_door.door_state==DOOR_OPEN:
                        cur_door.door_is_open_that_moment = time.time()# update it when the door is open so the time can reset
                        logging.info(f"{cur_door.door_name} open")
                        if not cur_door.door_music_is_playing:
                            cur_door.door_music_thread = threading.Thread(target=play_mp3, args=(cur_door,))
                            cur_door.door_music_thread.start()
                            cur_door.door_music_is_playing=True
                    else:
                        logging.info(f"invalid door state")
                    cur_door.door_last_door_state=cur_door.door_state

except Exception as e:
    client.loop_stop()
    client.disconnect()
    logging.info("exit")


# old code
#             if door_state != last_door_state:
#                 if music_is_playing and door_state == DOOR_CLOSED:
#                     logging.info("door closed")
#                     if music_is_playing:
#                         play_thread.join() # to kill the music if it is playing
#                         music_is_playing=False
#                 elif door_state == DOOR_OPEN:
#                     logging.info("door open")
#                     if not music_is_playing:
#                         play_thread = threading.Thread(target=play_mp3, args=(mp3_file,))
#                         play_thread.start()
#                         music_is_playing=True
#                 else:
#                     logging.info("invalid door state")
#                 last_door_state = door_state
# except Exception as e:
#     client.loop_stop()
#     client.disconnect()
#     logging.info("exit")
