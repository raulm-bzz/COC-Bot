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

def start_find(key):
    print(f"Hotkey {key} pressed. Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        pyautogui.click(x, y)
        time.sleep(0.3)

def attack(key):
    print(f"Hotkey {key} pressed. Function 'attack' called.")
    pyautogui.click(1079, 981)
    time.sleep(0.5)
    for x, y in CORDS_EARTHQUAKES:
        pyautogui.click(x, y)
        time.sleep(0.08)
    pyautogui.click(640, 975)
    time.sleep(0.5)
    for x, y in CORDS_VALKS:
        pyautogui.click(x, y)
        time.sleep(0.04)
    pyautogui.click(793, 972)
    time.sleep(1)
    pyautogui.click(639, 790)
    pyautogui.click(872, 974)
    pyautogui.click(639, 790)
    pyautogui.click(933, 973)
    pyautogui.click(639, 790)
    pyautogui.click(1003, 976)
    pyautogui.click(639, 790)
    time.sleep(1)
    keys_to_press = ['q', 'w', 'e', 'r']
    for key in keys_to_press:
        controller.press(key)    # press key via controller 
        controller.release(key)  # release key via controller
        time.sleep(0.2)

def surrender(key, duration=0.0, defeated=True):
    print(f"Hotkey {key} pressed. Function 'surrender' called.")
    for i, (x, y) in enumerate(CORDS_SURRENDER):
        pyautogui.click(x, y)
        time.sleep(0.3)
        if i == 1:  # after the second tuple (index 1)
                print("Second click done, getting loot data...")
                time.sleep(3)
                results = get_all_loot(key, defeated)
                save_loot_data(results, duration)
                print(results)
                time.sleep(1)


# Record cursor position
def record_position(key):
    pos = pyautogui.position()
    print(f"Recorded position: {pos}")
          
def kill_programm(key, executor):
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

def analyse(key):
    print(f"Hotkey {key} pressed. Function 'analyse' called.")
    start_time = time.time()
    region = (1776, 863, 1828, 894)
    screenshot = ImageGrab.grab(bbox=region)

    img = np.array(screenshot)

    result = reader.readtext(img)

    detected_text = result[0][1]

    elapsed = time.time() - start_time
    print(f"{detected_text} in {elapsed:.4f}s")
    return int(detected_text)

def check_for_end_battle():
    region = (147, 861, 287, 888)           # Coordinates of the "End Battle" text/button
    screenshot = ImageGrab.grab(bbox=region)

    img = np.array(screenshot)

    result = reader.readtext(img)

    try:
        detected_text = result[0][1]
        print(detected_text)
    except Exception as e:
        detected_text = None
        print(f"No text detected or an error occurred")

    return detected_text
    
def auto_attack(key):
    while True:
        start_time = time.time()
        print(f"Hotkey {key} pressed. Function 'auto_attack' called.")
        start_find(key)

        while check_for_end_battle() != "End Battle":   # Wait until Cloud search is over
            time.sleep(1.5)
        time.sleep(1)               # Additional delay to ensure everything is loaded
        attack(key)
        time.sleep(10)              # Delay for % analysation to start
        count = 0
        cache = 1000
        defeated = False
        while True:   
            percentage = analyse(key)
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
        surrender(key, duration + 5, defeated)
        print("Auto attack cycle COMPLETED.")
        time.sleep(5)               # Delay before starting the next cycle



def check_loot(key):
    print(f"Hotkey {key} pressed. Function 'test' called.")
    region = (799, 442, 1018, 627)
    screenshot = ImageGrab.grab(bbox=region)

    img = np.array(screenshot)

    result = reader.readtext(img)

    try:
        gold = result[0][1]
        elixir = result[1][1]
        dark = result[2][1]

        gold = int(gold.replace(' ', ''))
        elixir = int(elixir.replace(' ', ''))
        dark = int(dark.replace(' ', ''))
    except Exception as e:
        print(f"No text detected or an error occurred")

    return gold, elixir, dark
    
def check_loot_bonus(key):
    print(f"Hotkey {key} pressed. Function 'test' called.")
    region = (1254, 523, 1405, 671)
    screenshot = ImageGrab.grab(bbox=region)

    img = np.array(screenshot)

    result = reader.readtext(img)

    try:
        gold = result[0][1]
        elixir = result[1][1]
        dark = result[2][1]

        gold = int(gold.replace('+', ''))
        elixir = int(elixir.replace('+', ''))
        dark = int(dark.replace('+', ''))
    except Exception as e:
        print(f"No text detected or an error occurred")
    return gold, elixir, dark

def get_all_loot(key, defeated):
    gold_main, elixir_main, dark_main = check_loot(key)
    time.sleep(2)
    if defeated == False:
        gold_bonus, elixir_bonus, dark_bonus = check_loot_bonus(key)
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