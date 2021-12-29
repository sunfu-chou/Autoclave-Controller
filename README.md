## Environment

Ubuntu 20.04
Username: ubuntu
Password: raspberry

## Run

```
python main.py
```

## Wifi
SSID: 66666
Password: 6666666666
## Preparation
1. install virtualenv and create a virtual environment

install virtualenv
```
pip install virtualenv
```

create virtual environment
```
virtualenv venv
```

2. install pigpio
[pigpio](https://abyz.me.uk/rpi/pigpio/download.html)

3. install Adafruit
[Adafruit](https://github.com/adafruit/Adafruit_CircuitPython_ADS1x15)

```
sudo chmod 666 /dev/i2c-1
```
4. install [influxdb client](https://docs.influxdata.com/influxdb/v2.0/install/?t=Linux)

```
pip install influxdb_client
```
5. install numpy
```
pip install numpy
```
6. install scikit-fuzzy matplotlib
```
pip install scikit_fuzzy matplotlib
```
7. set pigpiod daemon

touch file names `pigpiod.dervice` adn contains below in `/lib/systemd/system`
```
[Unit]
Description=Pigpio daemon

[Service]
Type=forking
PIDFile=pigpio.pid
ExecStart=/usr/local/bin/pigpiod
ExecStop=/bin/systemctl kill -s SIGKILL pigpiod

[Install]
WantedBy=multi-user.target
```

and run 

```
sudo systemctl enable pigpiod.service
```

## Grafana
### Install
[Install on Debian_Ubuntu _ Grafana Labs](https://grafana.com/docs/grafana/latest/installation/debian/)
### settings
1. [Home dashboard](https://grafana.com/docs/grafana/latest/administration/preferences/change-home-dashboard/)
2. [Data source](https://grafana.com/docs/grafana/latest/datasources/influxdb/)
### Connect
```
ubuntu.local:3000
```

### Username and Password
Username: admin

Password: admin

## InfluxDB
### Install
[Install InfluxDB _ InfluxDB OSS 2.1 Documentation](https://docs.influxdata.com/influxdb/v2.1/install/?t=Linux)
### settings
1. Org, Bucket
### Connect
```
ubuntu.local:8086
```
### Username and Password
Username: admin

Password: adminadmin
