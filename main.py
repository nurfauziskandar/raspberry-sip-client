#!/usr/bin/env python3

import os
import re
from dotenv import load_dotenv
from baresipy import BareSIP
from time import sleep
import RPi.GPIO as GPIO
import sounddevice as sd
from pathlib import Path


# Konfigurasi GPIO
BUTTON_CALL = 17  # GPIO 17 untuk tombol call
BUTTON_HANGUP = 27  # GPIO 27 untuk tombol hangup

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_CALL, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_HANGUP, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def update_audio_source(file_path, new_device):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Ganti baris yang dimulai dengan "audio_source"
        updated_content = re.sub(
            r'^(audio_source\s+alsa,).*$',
            rf'\1{new_device}',
            content,
            flags=re.MULTILINE
        )

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

        print(f"audio_source berhasil diganti menjadi: alsa,{new_device}")

    except FileNotFoundError:
        print(f"File tidak ditemukan: {file_path}")
    except Exception as e:
        print(f"Terjadi error: {e}")

def update_config(file_path, new_config):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    new_lines = []
    config_found = False

    for line in lines:
        stripped = line.strip()

        if stripped and not stripped.startswith('#'):
            config_found = True
            continue 
        elif stripped.startswith('#' + new_config):
            continue
        else:
            new_lines.append(line)

    new_lines.append(f"{new_config}\n")

    with open(file_path, 'w') as file:
        file.writelines(new_lines)

    print(f"Account berhasil ditambahkan menjadi: {new_config}")

class voIP(BareSIP):
    def __init__(self, user, password, gateway):
        super().__init__(user, password, gateway)
        self.incoming_call = 0
        self.flag = 0

    # events
    def handle_incoming_call(self, number):
        print("Incoming call: " + number)
        self.incoming_call = 1
        if self.call_established:
            print("already in a call, rejecting")
            sleep(0.1)
            self.do_command("b")

    def handle_call_rejected(self, number):
        print("Rejected incoming call: " + number)

    def handle_call_timestamp(self, timestr):
        print("Call time: " + timestr)

    def handle_call_status(self, status):
        if status != self._call_status:
            print("Call Status: " + status)
            if status == "DISCONNECTED":
                self.incoming_call = 0
                self.flag = 0

    def handle_call_start(self):
        number = self.current_call
        print("Calling: " + number)

    def handle_call_ringing(self):
        number = self.current_call
        print(number + " is Ringing")

    def handle_call_established(self):
        print("Call established")

    def handle_call_ended(self, reason, number=None):
        self.incoming_call = 0
        self.flag = 0
        print("Call ended")
        print(f"Number: {number} , Reason: {reason}")

    def _handle_no_accounts(self):
        print("No accounts setup")
        self.login()

    def handle_login_success(self):
        print("Logged in!")

    def handle_login_failure(self):
        print("Log in failed!")
        self.quit()

    def handle_ready(self):
        print("Ready for instructions")

    def handle_mic_muted(self):
        print("Microphone muted")

    def handle_mic_unmuted(self):
        print("Microphone unmuted")

    def handle_audio_stream_failure(self):
        self.incoming_call = 0
        print("Aborting call, maybe we reached voicemail?")
        self.hang()

    def handle_dtmf_received(self, char, duration):
        print("Received DTMF symbol '{0}' duration={1}".format(char, duration))

    def handle_error(self, error):
        print(error)
        if error == "failed to set audio-source (No such device)":
            self.handle_audio_stream_failure()

    def handle_unhandled_output(self, output):
        print("Received unhandled output: '{0}'".format(output))

sounddev = None
devices = sd.query_devices()
homeDir = Path.home()
print("Checking Sound card ...")
for i, device in enumerate(devices):
    dvs = device['name']
    listing = dvs.find("USB")
    if listing == 0:
        sounddev = dvs.split(" - ")[1].replace("(", "").replace(")", "")
        break
    else:
        sounddev = None
if sounddev == None:
    print("Sound card not detected, please attach!")
    exit()
else:
    config_file = f"{homeDir}/.baresip/config"
    update_audio_source(config_file, f"plug{sounddev}")

load_dotenv(".env")
    
dialCall = os.getenv("DIAL_CALL")
user = os.getenv("USER_DIAL")
password = os.getenv("PASSWORD")
server = os.getenv("FREEPBX_SERVER")

if dialCall == None or user == None or password == None or server == None:
    exit()

update_config(f"{homeDir}/.baresip/accounts", f"<sip:{user}@{server}>;auth_pass={password}")

sip = voIP(user, password, server)

try:
    # Loop utama
    while True:
        if GPIO.input(BUTTON_CALL) == GPIO.LOW:
            print('You pushed call')
            if sip.incoming_call == 1 and sip.flag == 0:
                print("Menerima panggilan masuk...")
                sip.accept_call()
                sip.flag = 1
            if sip.incoming_call == 0 and sip.flag == 0:
                print('Memulai panggilan...')
                sip.call(f"{dialCall}@{server}")
                sip.flag = 1

        if GPIO.input(BUTTON_HANGUP) == GPIO.LOW:
            print('You pushed Hang')
            sip.flag = 0
            sip.incoming_call = 0
            sip.hang()

        sleep(0.5)

except KeyboardInterrupt:
    print("\nMenghentikan program...")

finally:
    sip.quit()
    GPIO.cleanup()
    print("Program berhenti.")