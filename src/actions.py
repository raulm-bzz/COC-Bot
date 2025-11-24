from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import time
import sys
import os
import json
from datetime import datetime
from PIL import ImageGrab
import easyocr
import numpy as np

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from coordinates import *
from hotkeys import *

controller = Controller()
reader = easyocr.Reader(['en'])

def start_find():
    print(f"Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        pyautogui.click(x, y)
        time.sleep(0.3)

def attack():
    print(f"Function 'attack' called.")
    pyautogui.click(1079, 981)
    time.sleep(0.5)
    for x, y in CORDS_EARTHQUAKES:
        pyautogui.click(x, y)
        time.sleep(0.1)
    time.sleep(0.5)
    for x, y in CORDS_VALKS:
        pyautogui.click(x, y)
        time.sleep(0.04)
    for x, y in CORDS_HEROS:
        pyautogui.click(x, y)
        time.sleep(0.25)
    for x, y in CORDS_HEROS:
        pyautogui.click(x, y)
        time.sleep(0.2)

    time.sleep(1)

    

def surrender(duration=0.0, defeated=True):
    print(f"Function 'surrender' called.")
    for i, (x, y) in enumerate(CORDS_SURRENDER):
        pyautogui.click(x, y)
        time.sleep(0.3)
        if i == 1:  # after the second tuple (index 1)
                time.sleep(1.5)
                results = get_all_loot(defeated)
                save_loot_data(results, duration)
                time.sleep(1)


# Record cursor position
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

    # Load existing data
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if not isinstance(data, list):
                data = []  # Safety fallback
        except json.JSONDecodeError:
            data = []  # If file is corrupt, reset it

    # Add timestamp automatically
    loot_entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "duration": duration,
        **loot_data
    }
    data.append(loot_entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("Loot data saved.")

def analyse():
    print(f"Function 'analyse' called.")
    start_time = time.time()
    region = (1780, 866, 1834, 900)
    screenshot = ImageGrab.grab(bbox=region)

    img = np.array(screenshot)

    result = reader.readtext(img)

    detected_text = result[0][1]

    elapsed = time.time() - start_time
    print(f"{detected_text} in {elapsed:.4f}s")
    return int(detected_text)

def check_end_battle():
        out = read_area((147, 861, 287, 888))
        if out == []:
            return False
        elif out[0] == "End Battle":
            return True
        else:
            return False

    
def auto_attack():
    while True:
        start_time = time.time()
        print(f"Function 'auto_attack' called.")
        start_find()
        time.sleep(1)
        while not check_end_battle():
            time.sleep(1.5)
        time.sleep(1)       
        attack()
        time.sleep(7)
        count = 0
        cache = 1000
        defeated = False
        while True:   
            percentage = analyse()
            if cache == percentage:
                count += 1
            cache = percentage
            if percentage >= 50:
                break
            if count >= 5:
                defeated = True
                break
            time.sleep(3)

        duration = time.time() - start_time
        surrender(duration + 5, defeated)
        print("Auto attack cycle COMPLETED.")
        time.sleep(4)               # Delay before starting the next cycle



def check_loot():
    region = (799, 442, 1018, 627)
    raw = read_area(region)
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
    region = (1254, 523, 1405, 671)

    raw = read_area(region)
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
        

def safe_int(value):            # helper
    try:
        # remove garbage characters
        clean = value.replace('+', '').replace(' ', '')
        return int(clean)
    except:
        return 0                # returns zero if conversion fails, so no crash occurs (only if used for saving into loot.json)

