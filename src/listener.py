from pynput import keyboard
from pynput.keyboard import Controller
import time
import sys
import os
from actions import *
from concurrent.futures import ThreadPoolExecutor


controller = Controller()

executor = ThreadPoolExecutor(max_workers=2)
CONFIG_MODE = False



config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from hotkeys import *

globals().update({
    f"KEY_{name}": data["key"]
    for name, data in HOTKEYS.items()
})

wall_cords = []

def on_press(key):
    global CONFIG_MODE
    try:

        # ----------------------------
        # NORMAL MODE MAPPINGS
        # ----------------------------
        normal_mapping = {
            KEY_START_FIND: start_find,
            KEY_ATTACK: attack,
            KEY_SURRENDER: surrender,
            KEY_RECORD: record_position,
            KEY_AUTO_ATTACK: auto_attack
        }

        # ----------------------------
        # CONFIG MODE MAPPINGS
        # (example actions)
        # ----------------------------
        config_mapping = {
        }

        # --- KILL ALWAYS WORKS ---
        if hasattr(key, "char") and key.char == KEY_KILL:
            kill_programm(executor)
            return False
        

        # ==========================================================
        # ENTER CONFIG MODE (press `c`)
        # ==========================================================
        if hasattr(key, "char") and key.char == KEY_CONFIGURE and not CONFIG_MODE:
            CONFIG_MODE = True
            print("\n>>> ENTERED CONFIG MODE <<<")
            print("Press ESC or 'c' again to return to normal mode.\n")
            return

        # ==========================================================
        # EXIT CONFIG MODE (ESC or `c` again)
        # ==========================================================
        if CONFIG_MODE:
            if hasattr(key, "char") and key.char == KEY_CONFIGURE:
                CONFIG_MODE = False
                print("\n>>> EXITED CONFIG MODE <<<\n")
                return

            if key == keyboard.Key.esc:
                CONFIG_MODE = False
                print("\n>>> EXITED CONFIG MODE <<<\n")
                return

            if hasattr(key, "char"):
                func = config_mapping.get(key.char)
                if func:
                    print(f"[CONFIG] Pressed: {key.char}")
                    executor.submit(func)
                else:
                    print(f"[CONFIG] Unknown key: {key.char}")
            return  # IMPORTANT — prevents normal hotkeys running

        # ==========================================================
        # NORMAL MODE LOGIC
        # ==========================================================
        if hasattr(key, "char"):
            func = normal_mapping.get(key.char)
            print(f"[NORMAL] Pressed key: {key.char}")
            if func:
                executor.submit(func)
        if hasattr(key, "char") and key.char == KEY_TEST:
            print(f"Test key {key} pressed!")
            test()

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
