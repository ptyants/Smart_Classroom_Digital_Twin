# ./mqtt_receiver/mqtt_receiver.py
import sys
import os
import paho.mqtt.client as mqtt
import requests
import json


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import MQTT_BROKER, MQTT_TOPIC, MQTT_PORT, FLASK_SERVER_URL


def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        print(f"[MQTT] Received message: {data}")

        # Gửi dữ liệu đến Flask server qua HTTP POST
        response = requests.post(FLASK_SERVER_URL, json=data)
        print(f"[HTTP] Sent to Flask. Status: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Failed to process message: {e}")


def main():
    client = mqtt.Client()
    try:
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print(f"[INFO] MQTT Receiver started. Subscribing to {MQTT_TOPIC}")
        client.loop_forever()
    except KeyboardInterrupt:
        print("Stopped MQTT Receiver.")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
