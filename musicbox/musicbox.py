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
import argparse
import configparser

logging.basicConfig(level=logging.DEBUG)

DOOR_CLOSED="closed"
DOOR_OPEN="open"
music_start_delay=5
doors_object_dict = {}
screaming_is_on=False
client=None

door_configs={
    "pantry": {
        "door_state": DOOR_CLOSED,
        "music_list": [
            {"music_file_path": "gentle_pantry.mp3",
                 "repeat_times": 2,
                 "volume": "-10000",
                 "delay_to_next": 60 },
            {"music_file_path": "pantry_smooth.mp3",
                 "repeat_times": 2,
                 "volume": "-20000",
                 "delay_to_next": 45},
            {"music_file_path": "pantry_furious.mp3",
                 "repeat_times": 2,
                 "volume": "-30000" ,
                 "delay_to_next": 30 }
        ]
    },

    "sauces": {
        "door_state": DOOR_CLOSED,
        "music_list": [
            {"music_file_path": "gentle_sauce.mp3",
                 "repeat_times": 2,
                 "volume": "-6000",
                 "delay_to_next": 60},
            {"music_file_path": "sauce_smooth.mp3",
                 "repeat_times": 2,
                 "volume": "-10000",
                 "delay_to_next": 45},
            {"music_file_path": "sauce_furious.mp3",
                 "repeat_times": 2,
                 "volume": "-20000",
                 "delay_to_next": 30 }
        ]
    }
}


class Door:
    """
        Doors are mqtt objects that we are listening for we track their open/closed status
        When open, we set timers and play a bit of reminder audio of the door state
        """
    def __init__(self, door_name, new_door_state,door_info_from_config):
        self.door_name = door_name
        self.door_state = new_door_state
        self.door_last_door_state = "close"
        self.door_music_is_playing = False

        # Music stuff
        self.door_music_files = door_info_from_config["music_list"]
        self.music_index = 0  # what is the current song
        self.music_plays =self.door_music_files[0]["repeat_times"]  # how many times have we played the current song
        self.next_play_time = self.door_music_files[0]["delay_to_next"]  # how long to wait before playing the next song
        self.volume = self.door_music_files[0]["volume"]
        self.music_file_path= self.door_music_files[0]["music_file_path"]
        # door state stuff
        self.door_music_thread = None
        self.door_is_open_that_moment=time.time()
        self.door_is_open_total_time=time.time()

    def update(self):
        if self.door_state != self.door_last_door_state:
            logging.info(f"in update function ")
            if self.door_music_is_playing and self.door_state == DOOR_CLOSED:
                logging.info(f"{self.door_name} closed")
                if self.door_music_is_playing:
                    self.door_music_thread.join()
                    self.door_music_is_playing = False
            elif self.door_state == DOOR_OPEN:
                logging.info(f"{self.door_name} is opening")
                self.door_is_open_that_moment = time.time()                     # update it when the door is open so the time can reset
                self.music_index = 0                                            # start over from 0
                self.music_plays = self.door_music_files[0]["repeat_times"]
                self.next_play_time = self.door_music_files[0]["delay_to_next"]  # how long to wait before playing the next song
                self.volume = self.door_music_files[0]["volume"]
                self.music_file_path = self.door_music_files[0]["music_file_path"]
                if not self.door_music_is_playing:
                    self.door_music_thread = threading.Thread(target=self.play_mp3) #start the thread so it doesnt block the main thread
                    self.door_music_thread.start()
                    logging.info(f"play_mp3 thread started")
                    self.door_music_is_playing = True
            else:
                logging.info(f"invalid door state")
            self.door_last_door_state = self.door_state

    def which_song_to_play(self):
        play_cmd=None
        if not screaming_is_on:
            play_cmd = ['afplay',  f"{os.path.abspath('sounds')}/{self.music_file_path}"]
            if platform.system() == 'Linux':
                play_cmd = ["mpg123", "-q", "-f",self.volume, "-o", "alsa:hw:1,0",
                            f"{os.path.abspath('sounds')}/{self.music_file_path}"]
            self.music_plays -= 1
            if self.music_plays <= 0:
                self.music_index += 1
                if self.music_index >= len(self.door_music_files):
                    self.music_index = 0
                self.music_plays = self.door_music_files[self.music_index]["repeat_times"]
                self.next_play_time = self.door_music_files[self.music_index]["delay_to_next"]
                self.volume = self.door_music_files[self.music_index]["volume"]
                self.music_file_path = self.door_music_files[self.music_index]["music_file_path"]
        return play_cmd

    def play_mp3(self):
        global screaming_is_on
        while True and self.door_state == DOOR_OPEN:
            cur_time = time.time()
            if cur_time > self.door_is_open_that_moment + self.next_play_time:
                play_cmd = self.which_song_to_play()
                if not screaming_is_on:
                    p = subprocess.Popen(play_cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    screaming_is_on=True
                    while p.poll() is None:                         #while the music is playing at background
                        time.sleep(0.5)
                        if self.door_state == DOOR_CLOSED:
                            logging.info(f"play_mp3 music stopping")
                            os.kill(p.pid, signal.SIGTERM)
                            break
                    if p.returncode == 0:                            #if the music is played successfully
                        logging.info('Music player ended with success')
                    else:
                        logging.info('Music player ended with failure')
                    p.wait()
                    screaming_is_on = False
                    time.sleep(self.next_play_time)                 #wait for the next song to play
        logging.info(f"exit play_mp3")

    def update_door_state(self, new_door_state):
            self.door_state = new_door_state


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
    if door_name not in doors_object_dict:
        doors_object_dict[door_name]=Door(door_name, new_door_state, door_configs[door_name])
        logging.info(f"door_name: {door_name} appended to doors_Object_List")
    else:
        doors_object_dict[door_name].update_door_state(new_door_state)
        logging.info(f"door_name: {door_name} updated to {new_door_state}")


def setup_mqtt(config):
    """
    Establish connection ot MQTT broker and subscribe to our topics /door/...
    :return: None
    """
    client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect

    # enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(config["default"]["mqtt_host_user"], config["default"]["mqtt_host_pswd"])
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(config["default"]["mqtt_host"], 8883)

    # setting callbacks, use separate functions like above for better visibility
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    client.subscribe("/door/pantry", qos=1)
    client.subscribe("/door/sauces", qos=1)

    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    client.loop_start()


def get_args():
    parser = argparse.ArgumentParser(prog='cache.py')
    parser.add_argument("-i", "--ini", required=True)
    args = parser.parse_args()
    return args


def main()->None:
    """
        Primary function, set up a few global environment things
        Repeatedly loop over the list of door and update their state
        causing music to play and stop as the door state changes over time.
        :return:
        """
    args=get_args()
    ini_file=args.ini

    config = configparser.ConfigParser()
    config.read(ini_file)

    setup_mqtt(config)         # initialize the mqtt environ/package

    while True:
        time.sleep(1)
        for each_door in doors_object_dict:
            cur_door=doors_object_dict[each_door] #extract the door object
            cur_door.update()


if __name__== '__main__':
    try:
        main()
    except Exception as e:
        client.loop_stop()
        client.disconnect()
        logging.info("exit")
