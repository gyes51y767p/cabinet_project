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
from pathlib import Path

DOOR_CONFGS={
    "user_base_dir": {"Linux": "/home/admin",
                        "Darwin": "~"},
    "sounds_dir" : "projects/cabinet_project/musicbox/sounds",

    "jwr": {
        "music_list": [
            {"music_file_path": "gentle_pantry.mp3",
             "repeat_times": 1,  # do we need this?
             "volume": "-6000",  # do we need this?
             "delay_to_play": 5},  # do we need this?
            {"music_file_path": "pantry_smooth.mp3",
             "repeat_times": 1,
             "volume": "-10000",
             "delay_to_play": 5},
            {"music_file_path": "pantry_furious.mp3",
             "repeat_times": 1,
             "volume": "-20000",
             "delay_to_play": 5}
        ]
    },

    "jwr2": {
        "music_list": [
            {"music_file_path": "gentle_sauce.mp3",
             "repeat_times": 1,
             "volume": "-6000",
             "delay_to_play": 5},
            {"music_file_path": "sauce_smooth.mp3",
             "repeat_times": 1,
             "volume": "-10000",
             "delay_to_play": 5},
            {"music_file_path": "sauce_furious.mp3",
             "repeat_times": 1,
             "volume": "-20000",
             "delay_to_play": 5}
        ]
    },

    "pantry": {
        "music_list": [
            {"music_file_path": "gentle_pantry.mp3",
                 "repeat_times": 3,#do we need this?
                 "volume": "-6000",#do we need this?
                 "delay_to_play": 20 },#do we need this?
            {"music_file_path": "pantry_smooth.mp3",
                 "repeat_times": 3,
                 "volume": "-10000",
                 "delay_to_play": 20},
            {"music_file_path": "pantry_furious.mp3",
                 "repeat_times": 1,
                 "volume": "-20000" ,
                 "delay_to_play": 20 }
        ]
    },

    "sauces": {
        "music_list": [
            {"music_file_path": "gentle_sauce.mp3",
                 "repeat_times": 3,
                 "volume": "-6000",
                 "delay_to_play": 10},
            {"music_file_path": "sauce_smooth.mp3",
                 "repeat_times": 1,
                 "volume": "-10000",
                 "delay_to_play": 10},
            {"music_file_path": "sauce_furious.mp3",
                 "repeat_times": 1,
                 "volume": "-20000",
                 "delay_to_play": 10 }
        ]
    }
}


sounds_base_dir=None
platform=platform.system()                  # linux/Darwin (support can be added for others if needed

logging.basicConfig(level=logging.DEBUG)

# user="doorman"
# password= "!@#$1Sastupidphrase"

user="jwr-test"
password= "mvy8URH9ndf0hbw_dmj"

DOOR_CLOSED="closed"
DOOR_OPEN="open"

mqtt_client=None    # the shared client object
door_dict={}        # list of doors we have in our program
music_player=None   # the shared music player

# setting callbacks for different events to see if it works, the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    logging.info("CONNECT received with code %s." % rc)

# which topic was subscribed to, only print the first time that script run
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    logging.info(f"client: {client}, userdata: {userdata}, mid: {mid}, granted_qos: {granted_qos}, properties: {properties}")
    logging.info("Subscribed: " + str(mid) + " " + str(granted_qos))

# when receiving a message, update the global variable
def on_message(client, userdata, msg):
    new_door_state = msg.payload.decode('utf-8')
    door_name=msg.topic.split("/")[-1]
    logging.info(f"Door {door_name} has a new mqtt message of {new_door_state}")

    door = door_dict.get(door_name)
    if not door:
        logging.info(f"Adding new door object {door_name}")
        door = Door(door_name)
        door_dict[door_name]=door

    door.new_mqtt_status=new_door_state

class MusicPlayer:
    """
    Class to single thread the playing of music
    The music is played in a thread and that thread creates a subprocess to actually play the music
    """
    def __init__(self):
        # set up the music player
        self.is_playing=False           # are we currently playing a song any song
        self.play_thread=None           # the thread that is playing the song; None if not playing
        self.door_playing=None          # the door that we are playing a song for; None if not playing

    def play_mp3(self, file_path):
        """
        Start playing a song; this is called as a thread
        1) Start the song as a sub-process command
        2) Loop while the song is stil playing and the door_status = Open
        :param file_path:  Song to play,
        :return:           None
        """

        play_cmd = ['afplay', file_path]
        if platform == 'Linux':
            volume = self.door_playing.play_volume
            play_cmd = ["mpg123", "-q", "-o", "alsa:hw:1,0", volume, f"{file_path}"]

        p = subprocess.Popen(play_cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            # when the music is playing, check if the door is closed
        while p.poll() is None:
            time.sleep(0.5)
            if self.door_playing.door_state == DOOR_CLOSED:
                logging.info(f"door closed; play_mp3 music stopping")
                os.kill(p.pid, signal.SIGTERM)
                break
        if p.returncode == 0:
            logging.info('Music player ended with success')
        else:
            logging.info('Music player ended with failure')
        p.wait()
        logging.info(f"ending play_mp3 thread")

    def play_song(self, door)->bool:
        """
        Play the song setup in the given door
        :param door: the door to get the song from
        :return: True if we can play, False if something is already playing
        """
        # play the queued/next song for the given door now
        self.door_playing=door
        sound_file=door.music_file
        mp3_file=f"{sounds_base_dir}/{sound_file}"
        if self.is_playing == False:
            self.play_thread = threading.Thread(target=self.play_mp3, args=(mp3_file,))
            self.play_thread.start()
            self.is_playing=True
            return(True)
        else:
            return(False)

    def is_playing_music(self)->bool:
        """
        Return true/false if any file is playing
        if we have something playing, we doublecheck to see if it is still playing
        if playing has stopped, we clean up and switch state back to not playing
        :return: True/False
        """
        # is any file playing
        if self.is_playing:
            # do a quick check to see if the music stopped
            if not self.play_thread.is_alive():
                self.play_thread.join()             # clean up the thread
                self.play_thread=None               # stop tracking this dead thread
                self.door_playing=None              # forget the door we are done playing
                self.is_playing=False               # we are no longer playing as well
        # is the music_player playing any_song
        return(self.is_playing)


    def which_door(self)->str:
        """
        Which door if any is playing
        :return: the name of the door or an empty string
        """
        if self.door_playing:
            return(self.door_playing.door_name)
        else:
            return ""


class Door:
    """
    Doors are mqtt objects that we are listening for we track their open/closed status
    When open, we set timers and play a bit of reminder audio of the door state
    """

    def __init__(self, door_name)->None:
        """
        Create a door
        :param door_name: The last part of the name passed from mqtt
        """
        self.door_name = door_name                      # The name of our door
        self.door_state = DOOR_CLOSED                   # is the door open/closed we default to closed on init
        self.last_door_state = self.door_state          # helps us track when the door has changed
        self.door_config=DOOR_CONFGS.get(door_name)     # get the configs for this door
        self.music_is_playing=False                     # have we queued a song?
        self.new_mqtt_status=self.door_state            # lastest update from mqtt, can change at any time

        # will be initialized when door is eventually opened; not used when closed
        self.next_play_time=None                        # time in the future to play the next song
        self.music_file=None                            # the next song to play
        self.plays_left=None                            # number of times left to play this song
        self.play_volume=None                           # play volume, onl used on linux
        self.play_index=None                            # index of current song in config song list

        if not self.door_config:
            raise ValueError(f"Can not find door {door_name} in DOOR_CONFIGS, exiting")

    def update(self)->None:
        """
        Check the timers to see if it is tiime to start a new song
        Queue up next song if current song has ended
        :return: None
        """

        # check for recently arrived mqtt message
        if self.door_state != self.new_mqtt_status:
            new_status = self.new_mqtt_status
            self.open_close(new_status)

        # check for time events and door_state_changes.
        if self.door_state==DOOR_OPEN:
            current_time=time.time()
            mbox_playing = music_player.is_playing_music()

            if self.music_is_playing:
                if not mbox_playing:
                    logging.info(f"Song ended for door: {self.door_name}")
                    self.song_ended()
                elif music_player.which_door() != self.door_name:
                    logging.info(f"Song is playing but for different door {music_player.which_door()}; ending song for door{self.door_name}")
                    self.song_ended()
            elif current_time > self.next_play_time:
                if music_player.is_playing_music() == False:
                    music_player.play_song(self)
                    self.music_is_playing=True
                    logging.info(f"Satarring music: {self.music_file} for door: {self.door_name}")
                else:
                    logging.info(f"Time to play next song for door: {self.door_name}; waiting for other music to stop")

    def song_ended(self):
        """
        Queue up the time to play the next itteration of this song;
        If no itterations queue up the next song by calling switch music
        :return:
        """
        self.music_is_playing=False
        self.plays_left -= 1
        if self.plays_left==0:
            self.switch_music()
        else:
            music_dict = self.door_config['music_list'][self.play_index]
            seconds_to_next_play = music_dict['delay_to_play']
            self.next_play_time = time.time() + seconds_to_next_play
            logging.info(f"Door {self.door_name} queued the next play of song {self.music_file} in {seconds_to_next_play} seconds")


    def switch_music(self)->None:
        """
        Switch to the next song in the list, at the end of the list go back to item 0
        :return: None
        """
        self.play_index += 1
        if self.play_index >= len(self.door_config['music_list']):
            self.play_index=0
        music_dict = self.door_config['music_list'][self.play_index]
        seconds_to_next_play = music_dict['delay_to_play']
        self.next_play_time = time.time() + seconds_to_next_play
        self.music_file = music_dict['music_file_path']
        self.plays_left = music_dict['repeat_times']
        self.play_volume = music_dict['volume']
        logging.info(f"Switching music file for door: {self.door_name} to {self.music_file} in {seconds_to_next_play} seconds")

    def open_close(self, new_door_state)->None:
        """
        Switch the door to OPEN or CLOSED state
        if the door state has not changed, then do nothing.
        if newly opend, queue up the next music to play
        if newly closed, set playing to false and set the status to closed
        :param new_door_state:
        :return:
        """
        # switch the door state
        self.door_state=new_door_state
        if self.door_state != self.last_door_state:
            logging.info(f"topic: {self.door_name}, message: {new_door_state}")
            if self.door_state == DOOR_CLOSED:
                self.music_is_playing=False
                logging.info(f"Door {self.door_name} is now CLOSED")

            else:
                # set up a new door state
                self.play_index=0
                music_dict=self.door_config['music_list'][self.play_index]
                self.next_play_time= time.time() + music_dict['delay_to_play']
                self.music_file=music_dict['music_file_path']
                self.plays_left=music_dict['repeat_times']
                self.play_volume=music_dict['volume']
                logging.info(f"Door {self.door_name} is now OPEN")

            self.last_door_state = self.door_state



#play the sound if the door is open for more than music_start_delay seconds


def setup_mqtt()->None:
    """
    Establish connection ot MQTT broker and subscribe to our topics /door/...
    :return: None
    """
    # using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
    # userdata is user defined data of any type, updated by user_data_set()
    # client_id is the given name of the client
    mqtt_client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
    mqtt_client.on_connect = on_connect

    # enable TLS for secure connection
    mqtt_client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    mqtt_client.username_pw_set(user, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    # $mqtt_client.connect("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", 8883)
    mqtt_client.connect("2f39d90aedd74a8ca09b710a5d6adf16.s2.eu.hivemq.cloud", 8883)

    # setting callbacks, use separate functions like above for better visibility
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_message = on_message

    mqtt_client.subscribe("/door/jwr", qos=1)
    mqtt_client.subscribe("/door/jwr2", qos=1)
    #mqtt_client.subscribe("/door/sauces", qos=1)
    # loop_forever for simplicity, here you need to stop the loop manually
    # you can also use loop_start and loop_stop
    mqtt_client.loop_start()

def main()->None:
    """
    Primary function, set up a few global environment things
    Repeatedly loop over the list of door and update their state
    causing music to play and stop as the door state changes over time.
    :return:
    """
    global music_player, home_dir, sounds_base_dir

    music_player=MusicPlayer()      # set up the single threaded music player
    setup_mqtt()                    # initialize the mqtt environ/package
    home_dir=DOOR_CONFGS['user_base_dir'][platform]
    home_dir=Path(home_dir).expanduser()
    sounds_base_dir=f"{home_dir}/{DOOR_CONFGS['sounds_dir']}"


    while True:
            time.sleep(1)
            for door in door_dict.values():
                door.update()

if __name__== '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(e)
        if mqtt_client:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
        logging.info("exit")