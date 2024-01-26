// This example uses an ESP32 Development Board
// to connect to shiftr.io.
//
// You can check on your device after a successful
// connection here: https://www.shiftr.io/try.
//
// by Joël Gähwiler
// https://github.com/256dpi/arduino-mqtt
#include <WiFiClientSecure.h>
#include <WiFi.h>
#include <MQTT.h>

// wifi config
const char ssid[] = "";		// wifi ssid
const char pass[] = "";				// wifi password

// mqt config
const char mqtt_broker_address[] = "61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud";
const int mqtt_port = 8883;
const char mqtt-broker-user[] = "doorman";
const char mqtt_password[] = "";

const char mqtt_key[]="/door/sauces";		// mtqq topic to publis
const char mqtt_open[]="open";					// mqtt payload when door is open
const char mqtt_closed[]="closed";			// mqtt payload when door is closed

WiFiClientSecure net;										// wifi object
MQTTClient client;											// mqtt object

const gpio_num_t DOOR_SENSOR=GPIO_NUM_2;	// door sensor pin
const int DOOR_OPEN=0;										// door pin state when door is OPEN 

boolean door_is_open;															// currently read door state true=open, false=closed
RTC_DATA_ATTR boolean last_door_is_open=false;		// what was the last known state of the door, retained during deep sleep mode

/*
** connect to wifi and mqtt
*/
void connect() {
	// connect to the wifi
  Serial.print("checking wifi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(100);
  }

	// connect to the MQTT
  Serial.print("\nconnecting MQTT");
  net.setInsecure();
  while (!client.connect(mqtt_broker_address, mqtt-broker-user, mqtt_password)) {
    Serial.print(".");
    delay(100);
  }
  Serial.println("\nconnected!");
}

/*
** Log the door state to the console
*/
void print_door_state(boolean door_is_open) {
    if (door_is_open == true) {
      Serial.println("Door is open");
    } else {
      Serial.println("Door is closed");
    }
}

/*
** publish the door state to MQTT
*/
void send_door_state(int door_is_open) {
    if (door_is_open == true) {
      client.publish(mqtt_key, mqtt_open);
    } else {
      client.publish(mqtt_key, mqtt_closed);
    }
}

/*
** 	1) setup wifi and mqtt connections 
**	2) connect to them both
**	3) publish our new door state topic
*/
void mqtt_connect_and_send(boolean door_is_open) {

	WiFi.begin(ssid, pass);
  client.begin(mqtt_broker_address, mqtt_port, net);
  connect();
	Serial.println("Queuing new door state");
  send_door_state(door_is_open);
	Serial.println("Starting send");
	while (!client.loop()) {}		// this statemsn, gets new messages, sends queued messages and re-connects if necessary
	Serial.println("Send complete");
  delay(10);  			// <- fixes some issues with WiFi stability

}

/*
** 1) Read the state of the door 
** 2) if and only if the state changed, publish the new state
** 3) go back to sleep until the door state changes again
**
**	This routine relies on the wakup by a RTC (real time clock related pin) chaning state
**	When this happens the esp32 wakes backup up and reads the pin and sends the state if changed
*/

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  Serial.print("src: door_sensor.ino; Updated Jan 2024; door_id: ");
  Serial.println(mqtt_key);
 

	// setup and read the door sensor
  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  door_is_open=digitalRead(DOOR_SENSOR)==DOOR_OPEN;
	Serial.println("\n~~~~~~~~~~~~~~~~~~~~~~~~\n");
	print_door_state(door_is_open);

	// if the pin state changed publish the new state
	if (last_door_is_open != door_is_open) {
		Serial.println("Door status changed");
		mqtt_connect_and_send(door_is_open);
		last_door_is_open=door_is_open;
	}

	Serial.println("Going To Sleep");
	esp_sleep_enable_ext0_wakeup(DOOR_SENSOR, door_is_open);
	esp_deep_sleep_start();

}

/*
** This code is never reached as machine is put in deep sleep at the end of the startup function
*/
void loop() {
}






