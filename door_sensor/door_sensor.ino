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

const char ssid[] = "LAK-FOXSPARROW";
const char pass[] = "4793263208";

// the keys to send to MQTT server
const char mqtt_key[]="/door/pantry";
const char mqtt_open[]="open";
const char mqtt_closed[]="closed";

WiFiClientSecure net;
MQTTClient client;

const gpio_num_t DOOR_SENSOR=GPIO_NUM_15;
const boolean DOOR_OPEN=true;

boolean door_is_open;															// currently read door state
RTC_DATA_ATTR boolean last_door_is_open=false;		// what was the last known state of the door, retained during deep sleep mode

void connect() {
	// connect to the wifi
  Serial.print("checking wifi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

	// connect to the MQTT
  Serial.print("\nconnecting MQTT");
  net.setInsecure();
  while (!client.connect("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", "gyes51y767p", "@Mm5648970")) {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("\nconnected!");
}

void print_door_state(boolean door_is_open) {
    if (door_is_open == true) {
      Serial.println("Door is open!");
    } else {
      Serial.println("Door is closed");
    }
}

void send_door_state(int door_is_open) {
    if (door_is_open == true) {
      client.publish(mqtt_key, mqtt_open);
    } else {
      client.publish(mqtt_key, mqtt_closed);
    }
}

void mqtt_connect_and_send(boolean door_is_open) {

	WiFi.begin(ssid, pass);
  client.begin("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", 8883, net);
  connect();
	client.loop();
  delay(10);  // <- fixes some issues with WiFi stability
	Serial.println("Sending new door state.");
  send_door_state(door_is_open);
	Serial.println("Send complete.");
	client.loop();									// not sure if this is needed after the publish, but better safe then sorry

}

void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  door_is_open=digitalRead(DOOR_SENSOR)==DOOR_OPEN;
	Serial.println("\n~~~~~~~~~~~~~~~~~~~~~~~~\n");
	print_door_state(door_is_open);

	if (last_door_is_open != door_is_open) {
		Serial.println("Door status changed, sending new state");
		mqtt_connect_and_send(door_is_open);
		last_door_is_open=door_is_open;
	}

	Serial.println("Going To Sleep");
	esp_sleep_enable_ext0_wakeup(DOOR_SENSOR, !door_is_open);
	esp_deep_sleep_start();

}

void loop() {

}






