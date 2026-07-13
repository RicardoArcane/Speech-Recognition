import speech_recognition as sr
import re
import subprocess
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import keyboard
import os
import sys
import json


def get_config_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "app_mapping.json")


DEFAULT_APP_MAPPING = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "spotify": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
    "discord": os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe"),
    # "proton": r"C:\Program Files\Proton\VPN\v4.2.2\ProtonVPN.exe",
    # "opera": os.path.expandvars(r"%LOCALAPPDATA%\Programs\Opera GX\opera.exe"),
    # "auto clicker": os.path.expandvars(r"%LOCALAPPDATA%\OP Auto Clicker\AutoClicker-3.0.exe"),
    # "drivers": r"C:\Program Files\NVIDIA Corporation\NVIDIA App\CEF\NVIDIA App.exe",
    # "games folder": os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\Games"),
    "steam": r"C:\Program Files (x86)\Steam\steam.exe",
    "downloads folder": os.path.expandvars(r"%USERPROFILE%\Downloads"),
    # "citra": os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\citra-windows-msvc-20240303-0ff3440\citra-qt.exe"),
    # "switch": os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\yuzu-windows-msvc\yuzu.exe"),
    # "gba": os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\mGBA-0.10.3-win64\mGBA.exe"),
    # "melon": os.path.expandvars(r"%USERPROFILE%\OneDrive\Desktop\melonDS.exe"),
    # "tablet": r"C:\LDPlayer\LDPlayer9\dnplayer.exe",
    "epic": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe",
}


def load_app_mapping():
    config_path = get_config_path()

    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            json.dump(DEFAULT_APP_MAPPING, f, indent=4)
        print(f"Created a config file at:\n{config_path}")
        print("Open that file in Notepad to add or fix app paths for your computer, then restart this program.\n")
        return DEFAULT_APP_MAPPING

    with open(config_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("Warning: app_mapping.json is invalid/corrupted. Using default app list instead.")
            return DEFAULT_APP_MAPPING


app_mapping = load_app_mapping()

print("Use commands such as 'open' followed with a command from the list of progams in folder to open applications/folders. \nUse 'close' followed with a command from the list of progams in folder to close applications/folders. \nUse 'volume' followed with a number from 0-100 in increments of 10 to set volume. \nSay 'pause script' to pause the script, 'resume script' to resume the script or 'stop script' to end the script.")

recognizer = sr.Recognizer()


def set_volume(volume_level):
    device = AudioUtilities.GetSpeakers()
    volume = device.EndpointVolume

    volume.SetMasterVolumeLevelScalar(volume_level / 100, None)
    print(f"Volume set to {volume_level}%")


def close_application(app_name):
    app_name = app_name.lower()
    app_path = app_mapping.get(app_name)
    if app_path:
        try:
            exe_name = app_path.split()[-1]
            exe_name = os.path.basename(exe_name)
            subprocess.call(["taskkill", "/F", "/IM", exe_name])
            print(f"Closed {app_name}")
            return
        except Exception as e:
            print(f"Error closing {app_name}: {e}")
            return
    else:
        print(f"'{app_name}' not found in app_mapping.json")


def open_application(app_name):
    app_name = app_name.lower()

    app_path = app_mapping.get(app_name)
    if app_path:
        try:
            if os.path.isdir(app_path):
                print(f"Opening folder {app_name}")
                os.startfile(app_path)
            else:
                print(f"Opening {app_name}...")
                subprocess.Popen(app_path, shell=True)
            return
        except Exception as e:
            print(f"Error opening {app_name}: {e}")
            return
    else:
        print(f"'{app_name}' not found in app_mapping.json")


def paused():
    print("Script paused. Say 'resume script' to continue or 'stop script' to end the script.")
    while True:
        with sr.Microphone() as mic:
            try:
                recognizer.adjust_for_ambient_noise(mic, duration=1)
                audio = recognizer.listen(mic)
                text = recognizer.recognize_google(audio)
                text = text.lower()
                match_pause = re.search(r"resume script", text)
                if match_pause:
                    print("Resuming script...")
                    return
                if "stop script" in text:
                    print("Stopping script...")
                    exit()
                else:
                    continue
            except sr.UnknownValueError:
                continue


while True:
    with sr.Microphone() as mic:
        try:
            recognizer.adjust_for_ambient_noise(mic, duration=1)
            print("Listening...")
            audio = recognizer.listen(mic)
            text = recognizer.recognize_google(audio)
            text = text.lower()
            print("You said: " + text)

            match = re.search(r'volume (\d+)', text)
            if match:
                volume_level = int(match.group(1))
                set_volume(volume_level)

            if "open" in text:
                match_app = re.search(r'open (.+)', text)
                if match_app:
                    app_name = match_app.group(1).strip()
                    open_application(app_name)

            if "close" in text:
                match_close = re.search(r'close (.+)', text)
                if match_close:
                    app_name = match_close.group(1).strip()
                    close_application(app_name)

            if "pause script" in text:
                paused()

            if "stop script" in text:
                print("Stopping script...")
                break

            if keyboard.is_pressed('q'):
                break
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand that.")
        except sr.RequestError:
            print("Could not request results from Google Speech Recognition service.")