## Environment

Ubuntu 20.04

## Run

just run controller
```
python main.py
```
run and debug
```
python -m debugpy --listen 0.0.0.0:64825 --wait-for-client ./main.py
```

then open debug client on local computer

## Preparation
1. install pigpio
2. install Adafruit
3. set pigpiod daemon

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

### Connect
```
ubuntu.local:3000
```

## InfluxDB
### Connect
```
ubuntu.local:8086
```
