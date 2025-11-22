from pynput import keyboard
from pynput.keyboard import Controller
import time
import sys
import os
from actions import *
controller = Controller()


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from coordinates import *
from hotkeys import *

globals().update({
    f"KEY_{name}": data["key"]
    for name, data in HOTKEYS.items()
})




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

        elif key.char == KEY_ANALYSE:
            analyse(key)

        elif key.char == KEY_KILL:
            return kill_programm(key)
        

        
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
