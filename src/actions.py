from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import time
import sys
import os
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
def surrender(key):
    print(f"Hotkey {key} pressed. Function 'surrender' called.")
    for x, y in CORDS_SURRENDER:
        pyautogui.click(x, y)
        time.sleep(0.3)
# Record cursor position
def record_position(key):
    pos = pyautogui.position()
    print(f"Recorded position: {pos}")
          
def kill_programm(key):
    print("Exiting program.")
    return False

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
    
def auto_attack(key):
    print(f"Hotkey {key} pressed. Function 'auto_attack' called.")
    start_find(key)
    time.sleep(5)               # Delay for time in Clouds
    attack(key)
    time.sleep(10)              # Delay for % analysation to start
    while analyse(key) <= 50:   
        time.sleep(3)           # Delay between analysations (to avoid spamming)
    surrender(key)
    print("Auto attack cycle COMPLETED.")
