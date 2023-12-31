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

WiFiClientSecure net;
MQTTClient client;


#define DOOR_SENSOR 15
#define DOOR_OPEN 1
#define DOOR_CLOSED 0
#define READ_DELAY_MS 500

int next_read=0;
int open_close;

unsigned long lastMillis = 0;



void connect() {
  Serial.print("checking wifi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.print("\nconnecting MQTT");
  net.setInsecure();
  while (!client.connect("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", "gyes51y767p", "@Mm5648970")) {
    Serial.print(".");
    delay(1000);
  }

  Serial.println("\nconnected!");

  // client.subscribe("/hello");
  // client.unsubscribe("/hello");
}

void messageReceived(String &topic, String &payload) {
  Serial.println("incoming: " + topic + " - " + payload);

  // Note: Do not use the client in the callback to publish, subscribe or
  // unsubscribe as it may cause deadlocks when other things arrive while
  // sending and receiving acknowledgments. Instead, change a global variable,
  // or push to a queue and handle it in the loop after calling `client.loop()`.
}

void print_door_state(int door_state) {
    if (door_state == DOOR_OPEN) {
      Serial.println("Door is open!");
    } else {
      Serial.println("Door is closed");
    }
}
void send_door_state(int door_state) {
    if (door_state == DOOR_OPEN) {
      client.publish("/door1", "1");
    } else {
      client.publish("/door1", "0");
    }
}



void setup() {
  Serial.begin(115200);
  while (!Serial) {}

  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  open_close=digitalRead(DOOR_SENSOR);
  Serial.print("Initial Door State is: ");
  print_door_state(open_close);

  WiFi.begin(ssid, pass);

  // Note: Local domain names (e.g. "Computer.local" on OSX) are not supported
  // by Arduino. You need to set the IP address directly.
  client.begin("61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud", 8883, net);
  client.onMessage(messageReceived);

  connect();
  Serial.println("Setup Done");
}

void loop() {
  client.loop();
  delay(10);  // <- fixes some issues with WiFi stability

  if (!client.connected()) {
    connect();
  }
  if (millis() > next_read) {
    int pin_mode = digitalRead(DOOR_SENSOR); 
  
    if (pin_mode != open_close) {
        print_door_state(pin_mode);
        send_door_state(pin_mode);
        open_close=pin_mode;
        next_read = millis() + READ_DELAY_MS;
    }
  }
}






