#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>

const char *ssid = "YOUR_WIFI_NAME";
const char *password = "YOUR_WIFI_PASSWORD";
const char *mqtt_server = "YOUR_VPS_IP";

WiFiClient espClient;
PubSubClient client(espClient);
Servo servo;

int angle = 90;

void callback(char *topic, byte *payload, unsigned int length)
{
    String message = "";

    for (int i = 0; i < length; i++)
    {
        message += (char)payload[i];
    }

    if (message == "MOVE_LEFT")
        angle -= 10;
    if (message == "MOVE_RIGHT")
        angle += 10;
    if (message == "CENTERED")
        angle = 90;

    angle = constrain(angle, 0, 180);
    servo.write(angle);
}

void reconnect()
{
    while (!client.connected())
    {
        if (client.connect("esp8266_mchiir01"))
        {
            client.subscribe("vision/mchiir01/movement");
        }
        else
        {
            delay(5000);
        }
    }
}

void setup()
{
    servo.attach(D1);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED)
        delay(500);

    client.setServer(mqtt_server, 1883);
    client.setCallback(callback);
}

void loop()
{
    if (!client.connected())
        reconnect();
    client.loop();
}