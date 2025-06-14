# ./simulator/simulated_school_device.py
import sys
import os
import paho.mqtt.client as mqtt
import json
import random
import time
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import MQTT_BROKER, MQTT_PORT


# === Cấu Hình MQTT ===
# test.mosquitto.org
MQTT_BROKER = MQTT_BROKER
MQTT_PORT =  MQTT_PORT
ROOM_IDS = [f"ROOM-{i}" for i in range(1,6)]  # Phòng từ 1 -> 6

# === Trạng Thái Ban Đầu ===
room_state = {
    room_id: {
        "people_count": random.randint(0, 30),
        "temperature": random.uniform(25, 30),
        "humidity": random.uniform(40, 60),
        "electric_energy": 0.0,
        "ac_status": "OFF",
        "timestamp": time.time()
    } for room_id in ROOM_IDS
}

# Cập nhật điện năng ban đầu theo số người (sau khi people_count đã có)
for room_id in ROOM_IDS:
    ppl = room_state[room_id]["people_count"]
    room_state[room_id]["electric_energy"] = round(ppl * 0.3 + random.uniform(0.1, 0.3), 2)


# Ví dụ thay đổi ac_lock thành dict lưu cả trạng thái ON/OFF
ac_lock_state = {room_id: {"lock_until": 0, "forced_status": None} for room_id in ROOM_IDS}


# === Hảm Cập Nhập Giá Trị Giả Lập Mỗi Phòng ===
def update_room_data(room_id, state):
    now = time.time()

    # Nhiệt độ dao động nhẹ
    delta_temp = random.uniform(-0.5, 0.5)
    delta_humidity = random.uniform(-1, 1)

    state["temperature"] = max(18, min(35, state["temperature"] + delta_temp))
    state["humidity"] = max(30, min(70, state["humidity"] + delta_humidity))
    state["people_count"] = random.randint(0, 40)


    lock_info = ac_lock_state.get(room_id, {"lock_until": 0, "forced_status": None})

    if now < lock_info["lock_until"]:
        state["ac_status"] = lock_info["forced_status"]
        print(f"Đang lock - Phòng {room_id}")
    else:
        # Nếu AC bật thì giảm nhiệt độ
        if state["ac_status"] == "ON":
            delta_temp -= 0.3

        # Logic bật/tắt AC trong TH có người sử dụng phòng
        if state["temperature"]  > 30 or state["people_count"] > 25:
            state["ac_status"] = "ON"
        elif state["temperature"] < 24 and state["people_count"] < 10:
            state["ac_status"] = "OFF"
        else:
            # Giữ nguyên hoặc chuyển sang IDLE với xác suất thấp
            state["ac_status"] = random.choices(
                ["ON", "OFF", "IDLE"], weights=[3, 2, 1]
            )[0]

    # === Giả lập tiêu thụ điện ===
    if state["ac_status"] == "ON":
        energy_increase = random.uniform(0.2, 0.5) + (state["people_count"] * 0.01)
    elif state["ac_status"] == "IDLE":
        energy_increase = random.uniform(0.05, 0.1)
    else:
        energy_increase = random.uniform(0.01, 0.05)

    # Cộng dồn điện năng tiêu thụ
    state["electric_energy"] = round(state["electric_energy"] + energy_increase, 2)
    state["timestamp"] = time.time()

    return state


# === MQTT Client ===
client = mqtt.Client()

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc==0:
            if userdata and "device_id" in userdata:
                print("Userdata device_id:", userdata["device_id"])
            else:
                print("No device_id found in userdata.")
            client.subscribe("school/room/+/control")
        else:
            print("Failed to connect, return code %d\n", rc)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()


# === Gửi dữ liệu ===
def publish_data():
    for room_id in ROOM_IDS:
        room_state[room_id] = update_room_data(room_id, room_state[room_id])
        topic = f"school/room/{room_id}/data"
        payload = json.dumps({**room_state[room_id], "room_id": room_id})
        client.publish(topic, payload)
        print(f"Published to {topic}: {payload}")


# === Xử lý tin nhắn điều khiển ===
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"Received message on {topic}: {payload}")


    # Ví dụ topic: school/room/ROOM-1/control
    try:
        data = json.loads(msg.payload.decode())
        room_id = data.get("room_id")
        command = data.get("command")
        duration = data.get("duration", 60)  # seconds

        if room_id in ROOM_IDS:
            if command == "TURN_OFF":
                ac_lock_state[room_id] = {"lock_until": time.time() + duration, "forced_status": "OFF"}
            elif command == "TURN_ON":
                ac_lock_state[room_id] = {"lock_until": time.time() + duration, "forced_status": "ON"}

    except Exception as e:
        print(f"Error processing control message: {e}")


# === Chạy Mô Phỏng ===
if __name__ == "__main__":
    connect_mqtt()
    try:
        while True:
            publish_data()
            time.sleep(3)
    except KeyboardInterrupt:
        print("Stopped Simulation.")
        client.loop_stop()
        client.disconnect()