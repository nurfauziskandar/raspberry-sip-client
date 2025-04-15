# SIP Client for Rasperry Pi
Repositori ini digunakan untuk impementasi SIP client menggunakan modul baresip dan python wrapper baresipy, kamu dapat menggunakan freepbx sebagai SIP servernya atau apapun yang sejenis.

Untuk instalasi freepbx server pada debian os dapat mengikuti cara di official dokumnetasinya atau repositori githubnya [FreePBX](https://github.com/FreePBX/sng_freepbx_debian_install "freepbx debian install")

### Hardware configuration


### Install dependencies
```
sudo apt update
sudo apt install python3-pip
sudo apt install baresip
sudo apt install virtualenv
sudo apt install ffmpeg
sudo apt install git
```

### Clone this repo and create venv
```
git clone https://github.com/nurfauziskandar/raspberry-sip-client.git
cd raspberry-sip-client
virtualenv sipclient
source sipclient/bin/activate
ln -s /usr/bin/ffmpeg sipclient/bin/ffmpeg
```

### Install python lib
```
pip3 install -r requirement.txt
```

### Dont forget to set default output on raspi-config.
```
sudo raspi-config
Choose, System Options -> Audio -> bcm2835 Headphones or headphone only
```

### You can run this SIP Client as a service/systemd (optional)
```
[Unit]
Description=SIP Client Script as a Service
After=network-online.target sound.target local-fs.target
Wants=network-online.target sound.target

[Service]
User=pi
WorkingDirectory=/home/pi/raspberry-sip-client
ExecStart=/home/pi/raspberry-sip-client/sipclient/bin/python /home/pi/raspberry-sip-client/main.py
Environment="PATH=/home/pi/raspberry-sip-client/sipclient/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Restart=always

[Install]
WantedBy=multi-user.target
```