# Smart_Classroom_Digital_Twin

Giao diện:


<img alt="Dashboard.png" src="https://github.com/ptyants/Smart_Classroom_Digital_Twin/blob/main/DEMO/Dashboard.png?raw=true" data-hpc="true" class="Box-sc-g0xbh4-0 fzFXnm">
<img alt="terminal.png" src="https://github.com/ptyants/Smart_Classroom_Digital_Twin/blob/main/DEMO/terminal.png?raw=true" data-hpc="true" class="Box-sc-g0xbh4-0 fzFXnm">


Chuẩn bị các môi trường sau:
+ Python 3  (v3.11)
+ Docker
+ Mosquitto (v2.0)
+ Influxdb  (v2.7 stable)
+ Grafana


1. Mosquitto:
    Mosquitto là một trình môi giới (broker) MQTT – một phần mềm trung gian dùng để giao tiếp giữa các thiết bị trong hệ thống Internet of Things (IoT).
    Kiểm tra version:
    
        mosquitto -v
        
    Chạy mosquitto:
    + Cách 1: 
        
            net start mosquitto
    
    + Cách 2: Hoặc chạy trực tiếp file mosquitto.exe từ thư mục cài đặt (thường là C:\Program Files\mosquitto).
   
    Tắt chạy ngầm mosquitto:

        net stop mosquitto
        
    Kiểm tra lại có cổng 1883  nào đc sử dụng k (do mặc định mosquitto dùng cổng này)

        netstat -ano | findstr 1883


3. InfluxDB
    Cài đặt:

        docker run -d --name influxdb2 -p 8086:8086 \
        -v influxdb2-data:/var/lib/influxdb2 \
        -v influxdb2-config:/etc/influxdb2 \
        -e DOCKER_INFLUXDB_INIT_MODE=setup \
        -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
        -e DOCKER_INFLUXDB_INIT_PASSWORD=123 \
        -e DOCKER_INFLUXDB_INIT_ORG=myorg \
        -e DOCKER_INFLUXDB_INIT_BUCKET=mybucket \
        influxdb:2

    Và chạy (nếu chưa thấy bật)

        docker start influxdb2

4. Grafana:
    Lệnh này truy cập cùng lớp mạng nhưng khác vị trí local nên không thể truy cập kết nối 2 docker với nhau:
   
        docker run -d --name=grafana -p 3000:3000 grafana/grafana-enterprise

    Dùng lệnh này mới kết nối được:
    
        docker run -d --name grafana --network monitoring-network -p 3000:3000 grafana/grafana-enterprise

    Và chạy (nếu chưa thấy bật)

        docker start grafana


Chạy hệ thống:
    Chạy song song 3 file python với nhau gồm:
    + app/app.py
    + mqtt_receiver/mqtt_receiver.py
    + simulator/simulated_school_device.py


Lưu ý:
+ Dự án tôi chạy là trên window 10
+ Nếu không thể chạy hoặc cài đặt đc bất cứ thư viên hay phần mền nào có thể tìm bản gần nhất hoặc chỉnh sửa lại mã nguồn cho phù hợp với môi trường máy và phiên bản hỗ trợ
+ Chạy InfuxDB và Grafana trên git hoặc trình cli tương tự như powershell
+ Muốn kết nối đc InfuxDB và Grafana thì chạy "docker network create monitoring-network" trước khi chạy các lệnh trên
+ Username và Password thì có thể đọc và tùy chỉnh trong lệnh docker


## Kiến trúc hệ thống

```text
Smart_Classroom_Digital_Twin/
│
├── app/                        # Dashboard Flask
│   ├── app.py                  # Flask app chính
│   └── templates/
│       └── dashboard.html      # Giao diện web
│
├── mqtt_receiver/              # Bộ thu MQTT
│   └── mqtt_receiver.py        # Lắng nghe dữ liệu từ thiết bị IoT
│
├── simulator/                  # Thiết bị mô phỏng
│   └── simulated_school_device.py  # Mô phỏng thiết bị lớp học gửi dữ liệu
│
├── requirements.txt            # Danh sách thư viện Python cần thiết
├── README.md                   # Tài liệu mô tả dự án
├── .gitignore                  # Bỏ qua các file/thư mục không cần thiết
└── config.py                   # Biến môi trường (MQTT, Flask API, DB credentials)


Giải thích sơ lược:
- app/ chứa backend Flask + SocketIO kết nối với Influxdb.
- mqtt_receiver/ là client nhận dữ liệu MQTT rồi đẩy về server qua HTTP.
- simulator/ để mô phỏng quá trình hoạt động tiêu thụ năng lượng và môi trường tại các phòng học
- influxdb/ để quản lý kết nối và thao tác với cơ sở dữ liệu time-series.
- requirements.txt liệt kê thư viện.
  
