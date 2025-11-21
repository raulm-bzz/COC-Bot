from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import time
import sys
import os

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from coordinates import *
from hotkeys import *

controller = Controller()

def start_find(key):
    print(f"Hotkey '{key}' pressed. Function 'start_find' called.")
    for x, y in CORDS_START_FIND:
        pyautogui.click(x, y)
        time.sleep(0.3)

def attack(key):
    print(f"Hotkey '{key}' pressed. Function 'attack' called.")
    pyautogui.click(1079, 981)
    time.sleep(0.5)
    for x, y in CORDS_EARTHQUAKES:
        pyautogui.click(x, y)
        time.sleep(0.03)
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
    print(f"Hotkey '{key}' pressed. Function 'surrender' called.")
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

