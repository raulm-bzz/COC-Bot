from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import time
import sys
import os
from actions import *

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from coordinates import *
from hotkeys import *

controller = Controller()




def on_press(key):
    try:
        if key.char == KEY_START_FIND:
            start_find(key)

        elif key.char == KEY_ATTACK:
            attack(key)


        elif key.char == KEY_SURRENDER:
            surrender(key)

        elif key.char == KEY_RECORD:
            record_position(key)

        elif key.char == KEY_KILL:
            return kill_programm(key)
        
    except AttributeError:
        pass


print("---> Listening <--- \nAvailable hotkeys:")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
