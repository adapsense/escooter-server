# escooter_server

The escooter server has two parts:
1. MQTT broker
2. Python Program

# MQTT Broker
The MQTT broker is the software that manages MQTT communication of the system. The MQTT broker software to be used is Mosquitto.

To ensure that the broker is accessible to the firmware of all escooters, Mosquitto should be installed and ran on a platform that is available 24/7.

Requirements:
- Domain name
- Email address for security updates

Steps:
1. Prepare your server instance
2. In your server instance, install and run Mosquitto
```
sudo apt-get install mosquitto mosquitto-clients
```
3. Test your now running MQTT broker

Open a new terminal and access the server instance. In the new terminal, key in the following
```
mosquitto_sub -h localhost -t test
```
This command subscribes to the broker on the hostname "localhost" with the topic "test". In the old terminal, key in the following
```
mosquitto_pub -h localhost -t test -m "hello world"
```
This command publishes the message "hello world" to the topic "test". Now check the new terminal if the message was received there.

4. Prepare to install certbot

In the old terminal, key in the following
```
sudo add-apt-repository ppa:certbot/certbot
```
Press the enter key to accept. Afterwards, key in the following
```
sudo apt-get update
```
5. Install certbot
```
sudo apt-get install certbot
```
6. Prepare to run certbot
```
sudo ufw allow http
```
7. Run certbot

Start running certbot by keying in the following replacing "mqtt.example.com" with your domain name
```
sudo certbot certonly --standalone --standalone-supported-challenges http-01 -d mqtt.example.com
```
Go through the prompts and provide an email address where LetsEncrypt can contact you and give you updates on the status of certbot. Accept the terms and service and it should inform you where certificates are stored.

8. Setup automatic certificate renewal
```
sudo crontab -e
```
Choose a text editor then add the following line at the end of the file that opens
```
15 3 * * * certbot renew --noninteractive --post-hook "systemctl restart mosquitto"
```
Save and close the file.

9. Choose a username and password to be used to restrict MQTT communications

Key in the following replacing "username" with your chosen username
```
sudo mosquitto_passwd -c /etc/mosquitto/passwd username
```
This will then prompt you for a password. Key it in and press the enter key.

10. Implement chosen username and password restriction, and enable SSL encryption and websockets
```
sudo nano /etc/mosquitto/conf.d/default.conf
```
In the file that opens, add these lines, replacing the paths for the certfile, cafile and keyfile with the paths for your setup
```
allow_anonymous false
password_file /etc/mosquitto/passwd
listener 1883 localhost

listener 8883
certfile /etc/letsencrypt/live/mqtt.example.com/cert.pem
cafile /etc/letsencrypt/live/mqtt.example.com/chain.pem
keyfile /etc/letsencrypt/live/mqtt.example.com/privkey.pem

listener 8083
protocol websockets
certfile /etc/letsencrypt/live/mqtt.example.com/cert.pem
cafile /etc/letsencrypt/live/mqtt.example.com/chain.pem
keyfile /etc/letsencrypt/live/mqtt.example.com/privkey.pem
```
Save and close the file. Then key in the following to restart mosquitto with the new restriction
```
sudo systemctl restart mosquitto
```
Then open up the relevant ports by keying in
```
sudo ufw allow 8883
```
and
```
sudo ufw allow 8083
```

# Python Program
The python program performs two functions:
- Link the backend database to the MQTT communication network
- Implement geofencing

Requirement:
- Python3 installed in the server instance

Steps:
1. Install the needed python packages
```
pip3 install dash
pip3 install dash-core-components
pip3 install dash-html-components
pip3 install plotly
pip3 install pyorbital
pip3 install pymongo
pip3 install bson
pip3 install paho-mqtt
pip3 install Shapely
pip3 install numpy
```
2. Clone this repository
```
git clone https://github.com/adapsense/escooter-server.git
```
3. Open the config.py file and update the configuration based on your backend's details as well as those of your domain that hosts the MQTT broker.
- backend_dbclient : connection string for your MongoDB database
- backend_query : Object ID for "Active" in geofenceStatus collection
- mqtt_ip : Domain name
- mqtt_port : Available port, preferrably websockets
- mqtt_path : MQTT path  on the broker
- mqtt_username : Chosen username
- mqtt_password : Chosen password
4. Run the python program
```
python3 live_monitor_v3.py
```
