# --- Standard Library ---
import os
import sys
import time
import random
import threading
import math
import json

# --- Third-party Libraries ---
from pynput import keyboard, mouse
from pynput.keyboard import Controller
import pyautogui
import pydirectinput
import numpy as np
from PIL import ImageGrab
import easyocr
# --- Project Imports ---
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config")
)
sys.path.append(config_path)
from coordinates import *
from hotkeys import *

# --- Initialization ---
controller = Controller()
reader = easyocr.Reader(['en'])

# Set by the GUI's stop button to break out of auto_attack between steps.
STOP_EVENT = threading.Event()

def stop_sleep(seconds):
    """Sleep, but wake up early if a stop was requested. Returns True if stopping."""
    return STOP_EVENT.wait(seconds)

SEQUENCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sequences"))

def load_sequence(name):
    filename = name if name.endswith(".json") else f"{name}.json"
    with open(os.path.join(SEQUENCES_DIR, filename)) as f:
        return json.load(f)["events"]

def list_sequences():
    """Names (without .json) of every recorded sequence, for populating the GUI dropdown."""
    if not os.path.isdir(SEQUENCES_DIR):
        return []
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(SEQUENCES_DIR)
        if f.endswith(".json")
    )

def play_sequence(name):
    """Replays a recorded sequence: press/click events fire immediately, delay
    events wait (interruptible by STOP_EVENT, same as the rest of auto_attack)."""
    events = load_sequence(name)
    print(f"Playing sequence '{name}' ({len(events)} events).")
    for event in events:
        etype = event["type"]
        if etype == "delay":
            if stop_sleep(event["duration"] / 5000):
                return
        elif etype == "press":
            pydirectinput.press(event["key"])
        elif etype == "click":
            click_randomized(event["coords_x"], event["coords_y"])
        else:
            print(f"Unknown sequence event type '{etype}' - skipping.")


#--MAIN ACTION FUNCTIONS--
def start_find():
    print(f"Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        click_randomized(x, y)
        time.sleep(0.3)

def attack(sequence_name=None):
    print(f"Function 'attack' called.")
    play_sequence(sequence_name or list_sequences()[0])

def surrender():
    print(f"Function 'surrender' called.")
    for x, y in CORDS_SURRENDER:
        click_randomized(x, y)
        time.sleep(0.3)

def record_position():
    pos = pyautogui.position()
    print(f"Recorded position: {pos}")

#--SEQUENCE RECORDING--
# Toggled by the Home hotkey. While active, a mouse listener captures real
# left-clicks and gui.py's own keyboard listener feeds key presses in via
# record_key_event().
#
# The mouse listener below is created once, at import time, and left running
# for the process lifetime - it just no-ops while _recording is False. Do NOT
# start/stop a Listener from inside start_recording()/stop_recording(): those
# run on the keyboard hook's own callback thread, and spinning up a brand-new
# OS-level hook from inside another hook's callback can take long enough that
# Windows silently unhooks the low-level keyboard hook (no exception, it just
# stops receiving events afterward).
_recording = False
_record_events = []
_record_last_time = None

# Set while the GUI's "name this sequence" dialog is open, so the hotkey
# listener can ignore keystrokes typed there instead of firing bot actions
# like attack() when a hotkey letter happens to be typed.
_input_locked = False

def is_recording():
    return _recording

def set_input_locked(locked):
    global _input_locked
    _input_locked = locked

def is_input_locked():
    return _input_locked

def start_recording():
    global _recording, _record_events, _record_last_time
    if _recording:
        return
    _recording = True
    _record_events = []
    _record_last_time = time.time()
    print("Recording started - press Home again to stop.")

def stop_recording():
    """Stops capturing and returns the events recorded so far (caller decides what to name/save)."""
    global _recording
    if not _recording:
        return []
    _recording = False
    print(f"Recording stopped - {len(_record_events)} events captured.")
    return _record_events

def record_key_event(key_name):
    """Call this from a keyboard listener's on_press while is_recording() is True."""
    if not _recording:
        return
    _log_event({"type": "press", "key": key_name})

def _on_record_click(x, y, button, pressed):
    if pressed and _recording and button == mouse.Button.left:
        _log_event({"type": "click", "coords_x": x, "coords_y": y})

# Started once here, at import time - see the note above on why this must
# not be started/stopped from start_recording()/stop_recording() instead.
_record_mouse_listener = mouse.Listener(on_click=_on_record_click)
_record_mouse_listener.start()

def _log_event(event):
    global _record_last_time
    now = time.time()
    delay_ms = round((now - _record_last_time) * 1000)
    _record_events.append({"type": "delay", "duration": delay_ms})
    _record_events.append(event)
    _record_last_time = now
    print(f"Recorded: {event}")

def save_recording(name, events):
    """Writes events out to sequences/<name>.json. Returns the path, or None if skipped."""
    if not events:
        print("Nothing recorded - skipping save.")
        return None
    name = name.strip()
    if not name:
        print("No name given - skipping save.")
        return None
    os.makedirs(SEQUENCES_DIR, exist_ok=True)
    safe_name = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "sequence"
    path = os.path.join(SEQUENCES_DIR, f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump({"name": name, "events": events}, f, indent=4)
    print(f"Saved recording '{name}' to {path}")
    return path

def kill_programm(executor):
    print("Exiting program.")
    executor.shutdown(wait=False)
    os._exit(0)

def check_end_battle():
        out = read_area(CORDS_END_BATTLE)
        if out == []:
            return False
        elif out[0] == "End Battle":
            return True
        else:
            return False

def auto_attack(sequence_name=None):
    sequence_name = sequence_name or list_sequences()[0]
    STOP_EVENT.clear()
    while True:
        if STOP_EVENT.is_set():
            print("Auto attack stopped.")
            return
        print(f"Function 'auto_attack' called.")

        start_find()
        time.sleep(1)
        false_count = 0
        while True:
            if STOP_EVENT.is_set():
                print("Auto attack stopped.")
                return
            if check_end_battle():
                false_count = 0
                break      # reset if True is returned
            else:
                false_count += 1     # count consecutive False results

                if false_count == 10:
                    print("check_end_battle() returned False 10 times in a row, trying start find again.")
                    false_count = 0
                    start_find()

            stop_sleep(1.5)
        time.sleep(1)
        attack(sequence_name)
        time.sleep(5)
        count = 0
        cache = 1000
        while True:
            if STOP_EVENT.is_set():
                print("Auto attack stopped.")
                return
            percentage = read_area(CORDS_PERCENTAGE)
            percentage = safe_int(percentage[0]) if percentage else 0
            if cache == percentage:
                count += 1
            cache = percentage
            if percentage >= 50:
                break
            if count >= 5:
                break
            stop_sleep(3)

        surrender()
        print("Auto attack cycle COMPLETED.")
        stop_sleep(4)               # Delay before starting the next cycle

def read_area(region):
    try:
        screenshot = ImageGrab.grab(bbox=region)
        img = np.array(screenshot)
        raw = reader.readtext(img)

        result = [item[1] for item in raw]  # Format like: ['28 829', '186 360', '724']
        print(f"Read area {region}: {result}")
        return result
    
    except Exception as e:
        print(f"ERROR reading area of: {region}")
        return []

# --HELPER FUNCTIONS--
def safe_int(value):
    try:
        clean = value.replace('+', '').replace(' ', '')
        return int(clean)
    except:
        return 0                # returns zero if conversion fails, so no crash occurs

def click_randomized(x, y, offset=5):
    rand_x = x + random.randint(-offset, offset)
    rand_y = y + random.randint(-offset, offset)
    pyautogui.click(rand_x, rand_y)

