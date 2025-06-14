# config.py
# test.mosquitto.org
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "school/room/+/data"

FLASK_SERVER_URL = "http://127.0.0.1:5000/api/room_state"

INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "09FUMoXqnXXaWEXZ6KKYXqAAbe6QnL3DsRC3Wx2scG6DA5HuLyjwFrczAqQzrBhrXYVYizBq4R7IB6RuzwGSLA=="
INFLUXDB_ORG = "myorg"
INFLUXDB_BUCKET = "school_data"