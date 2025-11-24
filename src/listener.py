from pynput import keyboard
from pynput.keyboard import Controller
import time
import sys
import os
from actions import *
from concurrent.futures import ThreadPoolExecutor


controller = Controller()

executor = ThreadPoolExecutor(max_workers=2)


config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config"))
sys.path.append(config_path)

from hotkeys import *

globals().update({
    f"KEY_{name}": data["key"]
    for name, data in HOTKEYS.items()
})

def DrawPoint(pos, size=6, color="red"):
    dot = Toaster(
        width=size,
        height=size,
        x=pos[0],
        y=pos[1],
        border_radius=size // 2,
        background_color=color,
        click_through=True,
        always_on_top=True
    )
    dot.show()
    return dot


def on_press(key):
    try:
        mapping = {
            KEY_START_FIND: start_find,
            KEY_ATTACK: attack,
            KEY_SURRENDER: surrender,
            KEY_RECORD: record_position,
            KEY_AUTO_ATTACK: auto_attack
        }

        if hasattr(key, "char") and key.char == KEY_KILL:
            kill_programm(executor)
            return False
        
        if hasattr(key, "char") and key.char == KEY_DRAW_POINT:
            DrawPoint((300, 200), size=4, color="red")

        if hasattr(key, "char"):
            func = mapping.get(key.char)
            print(f"Pressed key: {key.char}")
            if func:
                executor.submit(func)
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
