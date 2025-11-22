from pynput import keyboard
from pynput.keyboard import Controller
import time
import sys
import os
from actions import *
from concurrent.futures import ThreadPoolExecutor
import threading
controller = Controller()

executor = ThreadPoolExecutor(max_workers=2)


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from hotkeys import *

globals().update({
    f"KEY_{name}": data["key"]
    for name, data in HOTKEYS.items()
})


def on_press(key):
    try:
        # hotkey → function mapping
        mapping = {
            KEY_START_FIND: start_find,
            KEY_ATTACK: attack,
            KEY_SURRENDER: surrender,
            KEY_RECORD: record_position,
            KEY_ANALYSE: analyse,
            KEY_AUTO_ATTACK: auto_attack
        }

        # handle special kill key first
        if hasattr(key, "char") and key.char == KEY_KILL:
            kill_programm(key, executor)
            return False

        # process normal mapped hotkeys
        if hasattr(key, "char"):
            func = mapping.get(key.char)
            if func:
                executor.submit(func, key)  # run ONCE via executor

    except AttributeError:
        pass


def print_banner():
    print("""


*******************************
*        COC Attack Bot       *
*******************************

Hotkeys:""")
    
    # auto-generate each hotkey line with nice spacing
    for name, data in HOTKEYS.items():
        print(f"    {data['key']:<12} : {data['description']}")
    
    print("""
Now listening...
      
""")

print_banner()

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
