# --- Standard Library ---
import os
import sys
import time
import json
import random
import threading
from datetime import datetime
import math

# --- Third-party Libraries ---
from pynput import keyboard
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


#--MAIN ACTION FUNCTIONS--
def start_find():
    print(f"Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        click_randomized(x, y)
        time.sleep(0.3)

def attack():
    rndm_CORDS_VALKS = CORDS_VALKS[:]
    random.shuffle(rndm_CORDS_VALKS)
    print(f"Function 'attack' called.")
    time.sleep(0.5)
    pydirectinput.press('a')
    for x, y in CORDS_EARTHQUAKES:
        click_randomized(x, y)
        time.sleep(0.05)
    time.sleep(0.3)
    pydirectinput.press('1')
    for x, y in rndm_CORDS_VALKS:
        click_randomized(x, y)
        time.sleep(0.01)
    time.sleep(0.1)
    for key, (x, y) in zip("qwer", CORDS_HEROS):
        pydirectinput.press(key)
        time.sleep(0.05)
        click_randomized(x, y)
        time.sleep(0.07)
    for key in "qwer":
        pydirectinput.press(key)
        time.sleep(0.07)
    time.sleep(1)

def surrender(duration=0.0, defeated=True):
    print(f"Function 'surrender' called.")
    save = False
    if save:
        for i, (x, y) in enumerate(CORDS_SURRENDER):
            click_randomized(x, y)
            time.sleep(0.3)
            if i == 1:
                    time.sleep(1.5)
                    results = get_all_loot(defeated)
                    save_loot_data(results, duration)
                    time.sleep(1)
    elif not save:
        for x, y in CORDS_SURRENDER:
            click_randomized(x, y)
            time.sleep(0.3)

def record_position():
    pos = pyautogui.position()
    print(f"Recorded position: {pos}")

def kill_programm(executor):
    print("Exiting program.")
    executor.shutdown(wait=False)
    os._exit(0)

def save_loot_data(loot_data, duration, filepath="data/loot_data.json"):
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    loot_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "duration": duration,
        **loot_data
    }
    data.append(loot_entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("Loot data saved.")

def check_end_battle():
        out = read_area(CORDS_END_BATTLE)
        if out == []:
            return False
        elif out[0] == "End Battle":
            return True
        else:
            return False

def auto_attack():
    STOP_EVENT.clear()
    while True:
        if STOP_EVENT.is_set():
            print("Auto attack stopped.")
            return
        start_time = time.time()
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
        attack()
        time.sleep(5)
        count = 0
        cache = 1000
        defeated = False
        while True:
            if STOP_EVENT.is_set():
                print("Auto attack stopped.")
                return
            percentage = read_area(CORDS_PERCENTAGE)
            percentage = safe_int(percentage[0])
            if cache == percentage:
                count += 1
            cache = percentage
            if percentage >= 50:
                break
            if count >= 5:
                defeated = True
                break
            stop_sleep(3)

        duration = time.time() - start_time
        surrender(duration + 5, defeated)
        print("Auto attack cycle COMPLETED.")
        stop_sleep(4)               # Delay before starting the next cycle

def check_loot():
    raw = read_area(CORDS_MAIN_LOOT)
    if raw == []:
        return 0, 0, 0
    
    gold_raw   = raw[0] if len(raw) > 0 else 0
    elixir_raw = raw[1] if len(raw) > 1 else 0
    dark_raw   = raw[2] if len(raw) > 2 else 0

    gold   = safe_int(gold_raw)
    elixir = safe_int(elixir_raw)
    dark   = safe_int(dark_raw)

    return gold, elixir, dark

def check_loot_bonus():

    raw = read_area(CORDS_BONUS_LOOT)
    if raw == []:
        return 0, 0, 0

    gold_raw   = raw[0] if len(raw) > 0 else 0
    elixir_raw = raw[1] if len(raw) > 1 else 0
    dark_raw   = raw[2] if len(raw) > 2 else 0

    gold   = safe_int(gold_raw)
    elixir = safe_int(elixir_raw)
    dark   = safe_int(dark_raw)

    return gold, elixir, dark

def get_all_loot(defeated):
    gold_main, elixir_main, dark_main = check_loot()
    time.sleep(1)
    if defeated == False:
       # bonus exists
        gold_bonus, elixir_bonus, dark_bonus = check_loot_bonus()
        total_gold = gold_main + gold_bonus
        total_elixir = elixir_main + elixir_bonus
        total_dark = dark_main + dark_bonus
    else:
        total_gold = gold_main
        total_elixir = elixir_main
        total_dark = dark_main
        gold_bonus = 0
        elixir_bonus = 0
        dark_bonus = 0
    return {
        "gold_main": gold_main,
        "elixir_main": elixir_main,
        "dark_main": dark_main,
        "gold_bonus": gold_bonus,
        "elixir_bonus": elixir_bonus,
        "dark_bonus": dark_bonus,
        "total_gold": total_gold,
        "total_elixir": total_elixir,
        "total_dark": total_dark
    }

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
        return 0                # returns zero if conversion fails, so no crash occurs (only if used for saving into loot.json)

def click_randomized(x, y, offset=5):
    rand_x = x + random.randint(-offset, offset)
    rand_y = y + random.randint(-offset, offset)
    pyautogui.click(rand_x, rand_y)

