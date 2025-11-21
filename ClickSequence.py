from pynput import keyboard
from pynput.keyboard import Controller
import pyautogui
import time

keyboard = Controller()

# --- EDIT THESE POSITIONS FOR YOUR CLICK SEQUENCE ---
CORDS_START_FIND = [
    (197, 928),
    (352, 732),
    (1614, 881)
]

CORDS_SURRENDER = [
    (211, 877),
    (1157, 652),
    (993, 888)
]

CORDS_VALKS = [
    (290, 490),
    (348, 452),
    (359, 413),
    (393, 392),
    (427, 370),
    (447, 355),
    (503, 319),
    (533, 300),
    (573, 268),
    (603, 249),
    (632, 230),
    (663, 211),
    (704, 180),
    (759, 131),
    (790, 108),
    (826, 77),
    (872, 57),
    (1077, 48),
    (1124, 74),
    (1170, 96),
    (1216, 117),
    (1246, 146),
    (1294, 182),
    (1336, 220),
    (1367, 242),
    (1434, 291),
    (1485, 324),
    (1560, 375),
    (1623, 429),
    (1670, 465),
    (1684, 513),
    (1646, 560),
    (1587, 611),
    (1521, 657),
    (1456, 696),
    (1416, 724),
    (1378, 755),
    (1331, 803),
    (1280, 844),
    (1219, 889)
]

CORDS_HEROS = [
    (639, 790)
    ]

CORDS_EARTHQUAKES = [
    (758, 311),
    (758, 311),
    (758, 311),
    (758, 311),
    (1234, 311),
    (1234, 311),
    (1234, 311),
    (1234, 311)
]


# in order
KEY_START_FIND = 'a'
KEY_ATTACK = 's'
KEY_SURRENDER = 'd'

KEY_RECORD = '0'
KEY_KILL = '$'


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
                keyboard.press(key)    # press key
                keyboard.release(key)  # release key
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
