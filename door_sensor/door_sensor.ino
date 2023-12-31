// This example uses an ESP32 Development Board
// to connect to shiftr.io.
//
// You can check on your device after a successful
// connection here: https://www.shiftr.io/try.
//
// by Joël Gähwiler
// https://github.com/256dpi/arduino-mqtt

#include <WiFi.h>
#include <MQTT.h>

const char ssid[] = "LAK-FOXSPARROW";
const char pass[] = "4793263208";

WiFiClient net;
MQTTClient client;

unsigned long lastMillis = 0;

void connect() {
  Serial.print("checking wifi...");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.print("\nconnecting...");
  while (!client.connect("arduino", "public", "public")) {
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

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, pass);

  // Note: Local domain names (e.g. "Computer.local" on OSX) are not supported
  // by Arduino. You need to set the IP address directly.
  client.begin("public.cloud.shiftr.io", net);
  client.onMessage(messageReceived);

  connect();
}

void loop() {
  client.loop();
  delay(10);  // <- fixes some issues with WiFi stability

  if (!client.connected()) {
    connect();
  }

  // publish a message roughly every second.
  if (millis() - lastMillis > 1000) {
    lastMillis = millis();
    client.publish("/hello", "world");
  }
}





#define DOOR_SENSOR 15

#define DOOR_OPEN 1
#define DOOR_CLOSED 0
int open_close;

#define READ_DELAY_MS 500
int next_read=0;

void print_door_state(int door_state) {
    if (door_state == DOOR_OPEN) {
      Serial.println("Door is open!");
    } else {
      Serial.println("Door is closed");
    }
}

void setup() {
  // put your setup code here, to run once:

  Serial.begin(115200);
  while (!Serial) {}

  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  open_close=digitalRead(DOOR_SENSOR);
  Serial.print("Initial Door State is: ");
  print_door_state(open_close);

  Serial.println("Setup Done");

}

void loop() {
  // put your main code here, to run repeatedly:

  if (millis() > next_read) {
    int pin_mode = digitalRead(DOOR_SENSOR); 
  
    if (pin_mode != open_close) {
      print_door_state(pin_mode);
      open_close=pin_mode;
      next_read = millis() + READ_DELAY_MS;
    }
  }
}



