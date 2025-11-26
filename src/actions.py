# --- Standard Library ---
import os
import sys
import time
import json
import random
from datetime import datetime
import math

# --- Third-party Libraries ---
from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import numpy as np
from PIL import ImageGrab
import easyocr
import ast
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
walls_cords = []


#--MAIN ACTION FUNCTIONS--
def start_find():
    print(f"Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        click_randomized(x, y)
        time.sleep(0.3)

def attack():
    print(f"Function 'attack' called.")
    time.sleep(0.5)
    for x, y in CORDS_EARTHQUAKES:
        click_randomized(x, y)
        time.sleep(0.1)
    time.sleep(0.5)
    for x, y in CORDS_VALKS:
        click_randomized(x, y)
        time.sleep(0.04)
    for x, y in CORDS_HEROS:
        click_randomized(x, y)
        time.sleep(0.2)
    time.sleep(1)

def surrender(duration=0.0, defeated=True):
    print(f"Function 'surrender' called.")
    save = False
    if save:
        for i, (x, y) in enumerate(CORDS_SURRENDER):
            click_randomized(x, y)
            time.sleep(0.3)
            if i == 1:  # after the second tuple (index 1)
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
    while True:
        start_time = time.time()
        print(f"Function 'auto_attack' called.")
        start_find()
        time.sleep(1)
        while not check_end_battle():
            time.sleep(1.5)
        time.sleep(1)
        attack()
        time.sleep(5)
        count = 0
        cache = 1000
        defeated = False
        while True:   
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
            time.sleep(3)

        duration = time.time() - start_time
        surrender(duration + 5, defeated)
        print("Auto attack cycle COMPLETED.")
        time.sleep(4)               # Delay before starting the next cycle

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


def test(top, bottom):
    # example cords, best if given based on session zoom
    # top = (885, 156)
    left = (695, 303)
    # bottom = (1073, 592)
    right = (1267, 446)

    x1 = top[0]
    x2 = bottom[0]
    y1 = top[1]
    y2 = bottom[1]

    x_step = (x1 - x2)    #gonna give +
    y_step = (y2 - y1)    #gonna give +

    x_step = x_step / 12
    y_step = y_step / 12

    last_x = x1
    last_y = y1

    cords_row_1 = [(x1, y1)]

    for _ in range(12):
        new_cord = (last_x - x_step, last_y + y_step)
        new_cord_int = (int(math.ceil(new_cord[0])), int(math.ceil(new_cord[1])))
        cords_row_1.append(new_cord_int)
        last_x = new_cord[0]
        last_y = new_cord[1]

    for i, cord in enumerate(cords_row_1):
        print(f"Sequence: {i} Clicking at: {cord}")
        pyautogui.click(cord[0], cord[1])
        time.sleep(0.2)

def append_cord():
    pos = pyautogui.position()
    print(pos)
    walls_cords.append((pos.x, pos.y))

def configure_test2():
    print("Configured wall coordinates:")
    for cord in walls_cords:
        print(cord)
    test(walls_cords[0], walls_cords[1])


#--CONFIGURATION FUNCTIONS--


# --HELPER FUNCTIONS--
def safe_int(value):                                # helper
    try:
        clean = value.replace('+', '').replace(' ', '')
        return int(clean)
    except:
        return 0                # returns zero if conversion fails, so no crash occurs (only if used for saving into loot.json)

def click_randomized(x, y, offset=5):               # helper
    rand_x = x + random.randint(-offset, offset)
    rand_y = y + random.randint(-offset, offset)
    pyautogui.click(rand_x, rand_y)