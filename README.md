## Environment

Ubuntu 20.04

## Run

```
python main.py
```

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
