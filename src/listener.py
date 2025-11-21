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




def on_press(key):
    try:
        # Trigger the sequence
        if key.char == KEY_START_FIND:
            print(f"Hotkey '{KEY_START_FIND}' pressed. Performing clicks...")
            for x, y in CORDS_START_FIND:
                pyautogui.click(x, y)
                time.sleep(0.3)

        if key.char == KEY_ATTACK:
            print(f"Hotkey '{KEY_ATTACK}' pressed. Performing clicks...")

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


        if key.char == KEY_SURRENDER:
            print(f"Hotkey '{KEY_SURRENDER}' pressed. Performing clicks...")
            for x, y in CORDS_SURRENDER:
                pyautogui.click(x, y)
                time.sleep(0.3)

        # Record cursor position
        elif key.char == KEY_RECORD:
            pos = pyautogui.position()
            print(f"Recorded position: {pos}")

        elif key.char == KEY_KILL:
            print("Exiting program.")
            return False  # Stop listener
        
    except AttributeError:
        # ignore special keys
        pass


print("Listening... Press L to trigger clicks, 0 to record cursor position. Ctrl+C to exit.")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
