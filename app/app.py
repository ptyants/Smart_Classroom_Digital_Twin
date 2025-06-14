# app.py
import sys
import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import threading
import paho.mqtt.client as mqtt
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# MQTT client for control commands
mqtt_client = mqtt.Client()

current_states = {}  # lưu trạng thái hiện tại


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Flask MQTT client connected with code {rc}")
    else:
        print(f"[MQTT] Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    print(f"[MQTT] Disconnected with return code {rc}")

def on_publish(client, userdata, mid):
    print(f"[MQTT] Message published with mid: {mid}")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_publish

mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/room_state", methods=["POST"])
def receive_room_state():
    global current_states

    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # Lưu trạng thái hiện tại để gửi về dashboard
    room_id = data.get("room_id")
    if not room_id:
        return jsonify({"error": "'room_id' is missing"}), 400
    current_states[room_id] = data

    # Gửi dữ liệu vào InfluxDB
    try:
        point = (
            Point("ac_state")
            .tag("room_id", room_id)  # thêm tag để phân biệt phòng
            .field("temperature", float(data.get("temperature", 0)))
            .field("humidity", float(data.get("humidity", 0)))
            .field("electric_energy", float(data.get("electric_energy", 0)))
            .field("ac_status", 1 if data.get("ac_status", "OFF") == "ON" else 0)
            .time(int(data.get("timestamp", time.time()) * 1e9), WritePrecision.NS)
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)
        print(f"[InfluxDB] Data written: {data}")
    except Exception as e:
        print(f"[InfluxDB] Write error: {e}")

    # Điều khiển AC dựa trên logic:
    temp = data.get("temperature", 0)
    command = None
    
    # Điều kiến AC bật tắt tự động
    # if temp > 30:
    #     command = "TURN_ON"
    # elif temp < 25:
    #     command = "TURN_OFF"

    # Nếu có lệnh điều khiển thì gửi qua MQTT
    if command:
        topic = f"school/room/{room_id}/control"
        try:
            mqtt_client.publish(topic, json.dumps({"room_id": room_id, "command": command}))
            print(f"[MQTT] Published control command: {command} to {topic}")
        except Exception as e:
            print(f"[MQTT] Publish error: {e}")

    # Gửi trạng thái cập nhật realtime cho dashboard qua SocketIO
    socketio.emit("update_state", { "room_id": room_id, **data })

    return jsonify({"status": "ok"})

@socketio.on('manual_control')
def manual_control(data):
    # Nhận lệnh thủ công từ dashboard (ON/OFF)
    room_id = data.get("room_id")
    command = data.get("command")
    if room_id and command in ["TURN_ON", "TURN_OFF"]:
        topic = f"school/room/{room_id}/control"  # publish đúng topic tương tự
        try:
            mqtt_client.publish(topic, json.dumps({"room_id": room_id, "command": command}))
            print(f"[MQTT] Manual control sent: {command} to {topic}")
            socketio.emit("manual_ack", {"room_id": room_id, "command": command, "status": "sent"})
        except Exception as e:
            print(f"[MQTT] Manual control publish error: {e}")
            socketio.emit("manual_ack", {"room_id": room_id, "command": command, "status": "failed", "error": str(e)})


if __name__ == "__main__":
    socketio.run(app, port=5000, debug=True)
