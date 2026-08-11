"""Tkinter front-end for the COC bot.

Run this instead of listener.py to get a window with buttons, a live log and
loot stats. The global hotkeys keep working exactly as before.
"""

# --- Standard Library ---
import os
import sys
import json
import queue
import threading
import traceback
import tkinter as tk
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor

# --- Third-party Libraries ---
from pynput import keyboard

# --- Project Imports ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "config")
)
sys.path.append(config_path)

import actions
from hotkeys import HOTKEYS

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOOT_FILE = os.path.join(PROJECT_ROOT, "data", "loot_data.json")

# --- Colors ---
BG      = "#1b1d24"
PANEL   = "#242731"
BTN     = "#323647"
BTN_HL  = "#3d4256"
BORDER  = "#333747"
FG      = "#e7e9ef"
MUTED   = "#8b90a3"
ACCENT  = "#4f8cff"
GREEN   = "#3ddc84"
ORANGE  = "#ffb020"
RED     = "#ff5f56"


class LogStream:
    """Redirects print() output into a queue the GUI drains on the main thread."""

    def __init__(self, log_queue, mirror):
        self.log_queue = log_queue
        self.mirror = mirror

    def write(self, text):
        self.log_queue.put(text)
        if self.mirror:
            try:
                self.mirror.write(text)
            except Exception:
                pass

    def flush(self):
        if self.mirror:
            try:
                self.mirror.flush()
            except Exception:
                pass


class BotGUI:
    def __init__(self, root):
        self.root = root
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.log_queue = queue.Queue()
        self.busy_lock = threading.Lock()
        self.current_action = None

        root.title("COC Attack Bot")
        root.geometry("940x660")
        root.minsize(760, 520)
        root.configure(bg=BG)

        self._build_styles()
        self._build_header()
        self._build_body()
        self._build_log()

        # Everything printed by actions.py from here on lands in the log panel.
        sys.stdout = LogStream(self.log_queue, sys.__stdout__)
        sys.stderr = LogStream(self.log_queue, sys.__stderr__)

        self._start_hotkey_listener()
        self.refresh_stats()
        self._tick()

        print("GUI ready. Hotkeys are active globally.")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=FG, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI Semibold", 16))
        style.configure("Heading.TLabel", background=PANEL, foreground=MUTED,
                        font=("Segoe UI Semibold", 9))
        style.configure("Value.TLabel", background=PANEL, foreground=FG,
                        font=("Consolas", 11))
        style.configure("Vertical.TScrollbar", background=BTN, troughcolor="#15171d",
                        bordercolor="#15171d", arrowcolor=MUTED, relief="flat")
        style.map("Vertical.TScrollbar", background=[("active", BTN_HL)])

    def _button(self, parent, text, command, color=BTN, fg=FG, hover=BTN_HL):
        btn = tk.Button(
            parent, text=text, command=command,
            bg=color, fg=fg, activebackground=hover, activeforeground=fg,
            relief="flat", bd=0, padx=12, pady=9, cursor="hand2",
            font=("Segoe UI Semibold", 10), highlightthickness=0,
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=color))
        return btn

    def _build_header(self):
        header = ttk.Frame(self.root, style="TFrame")
        header.pack(fill="x", padx=16, pady=(14, 8))

        ttk.Label(header, text="COC Attack Bot", style="Title.TLabel").pack(side="left")

        self.status_dot = tk.Label(header, text="●", bg=BG, fg=MUTED,
                                   font=("Segoe UI", 14))
        self.status_dot.pack(side="right", padx=(8, 0))
        self.status_label = tk.Label(header, text="Idle", bg=BG, fg=MUTED,
                                     font=("Segoe UI Semibold", 11))
        self.status_label.pack(side="right")

    def _build_body(self):
        body = ttk.Frame(self.root, style="TFrame")
        body.pack(fill="x", padx=16)
        body.columnconfigure(0, weight=1, uniform="col")
        body.columnconfigure(1, weight=1, uniform="col")

        # --- Actions panel ---
        actions_panel = tk.Frame(body, bg=PANEL, highlightthickness=1,
                                 highlightbackground=BORDER)
        actions_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(actions_panel, text="ACTIONS", style="Heading.TLabel").pack(
            anchor="w", padx=14, pady=(12, 8))

        grid = tk.Frame(actions_panel, bg=PANEL)
        grid.pack(fill="x", padx=14, pady=(0, 8))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        buttons = [
            ("Start Find", lambda: self.run_action("start_find", actions.start_find)),
            ("Attack", lambda: self.run_action("attack", actions.attack)),
            ("Surrender", lambda: self.run_action("surrender", actions.surrender)),
            ("Record Position", lambda: self.run_action("record_position", actions.record_position)),
        ]
        for i, (text, cmd) in enumerate(buttons):
            btn = self._button(grid, text, cmd)
            btn.grid(row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)

        run_row = tk.Frame(actions_panel, bg=PANEL)
        run_row.pack(fill="x", padx=14, pady=(4, 14))
        run_row.columnconfigure(0, weight=1)
        run_row.columnconfigure(1, weight=1)

        self._button(run_row, "▶  Auto Attack", self.start_auto_attack,
                     color=ACCENT, fg="#0d1117", hover="#6ea1ff").grid(
                         row=0, column=0, sticky="ew", padx=3)
        self._button(run_row, "■  Stop", self.stop_auto_attack,
                     color=RED, fg="#0d1117", hover="#ff7b73").grid(
                         row=0, column=1, sticky="ew", padx=3)

        # --- Stats panel ---
        stats_panel = tk.Frame(body, bg=PANEL, highlightthickness=1,
                               highlightbackground=BORDER)
        stats_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        head = tk.Frame(stats_panel, bg=PANEL)
        head.pack(fill="x", padx=14, pady=(12, 8))
        ttk.Label(head, text="LOOT STATS", style="Heading.TLabel").pack(side="left")
        tk.Button(head, text="Refresh", command=self.refresh_stats, bg=PANEL, fg=MUTED,
                  activebackground=PANEL, activeforeground=FG, relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI", 9)).pack(side="right")

        self.stat_vars = {}
        for label in ("Recorded battles", "Total gold", "Total elixir",
                      "Total dark", "Last battle"):
            row = tk.Frame(stats_panel, bg=PANEL)
            row.pack(fill="x", padx=14, pady=2)
            ttk.Label(row, text=label, style="Muted.TLabel").pack(side="left")
            var = tk.StringVar(value="-")
            ttk.Label(row, textvariable=var, style="Value.TLabel").pack(side="right")
            self.stat_vars[label] = var

        # --- Hotkey reference ---
        hk = tk.Frame(stats_panel, bg=PANEL)
        hk.pack(fill="x", padx=14, pady=(12, 14))
        ttk.Label(hk, text="HOTKEYS", style="Heading.TLabel").pack(anchor="w", pady=(0, 4))
        hint = "   ".join(f"{d['key']} = {d['description']}" for d in HOTKEYS.values())
        tk.Label(hk, text=hint, bg=PANEL, fg=MUTED, font=("Consolas", 8),
                 justify="left", wraplength=380).pack(anchor="w")

    def _build_log(self):
        wrapper = tk.Frame(self.root, bg=PANEL, highlightthickness=1,
                           highlightbackground=BORDER)
        wrapper.pack(fill="both", expand=True, padx=16, pady=16)

        head = tk.Frame(wrapper, bg=PANEL)
        head.pack(fill="x", padx=14, pady=(10, 4))
        ttk.Label(head, text="LOG", style="Heading.TLabel").pack(side="left")
        tk.Button(head, text="Clear", command=self.clear_log, bg=PANEL, fg=MUTED,
                  activebackground=PANEL, activeforeground=FG, relief="flat", bd=0,
                  cursor="hand2", font=("Segoe UI", 9)).pack(side="right")

        self.log = tk.Text(wrapper, bg="#15171d", fg="#c8ccd8", bd=0,
                           font=("Consolas", 9), wrap="word", insertbackground=FG,
                           padx=10, pady=8, state="disabled")
        scroll = tk.Scrollbar(wrapper, command=self.log.yview, bg=BTN,
                              troughcolor="#15171d", activebackground=BTN_HL,
                              highlightthickness=0, bd=0, relief="flat",
                              elementborderwidth=0, width=12)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y", padx=(0, 4), pady=(0, 10))
        self.log.pack(fill="both", expand=True, padx=(10, 0), pady=(0, 10))

    # ------------------------------------------------------------------
    # Action plumbing
    # ------------------------------------------------------------------
    def run_action(self, name, func):
        """Run a bot action on the worker pool, one at a time, logging any crash."""
        if not self.busy_lock.acquire(blocking=False):
            print(f"Busy with '{self.current_action}' - '{name}' ignored.")
            return
        self.current_action = name

        def wrapped():
            try:
                func()
            except Exception:
                print(f"ERROR in '{name}':\n{traceback.format_exc()}")
            finally:
                self.current_action = None
                self.busy_lock.release()

        self.executor.submit(wrapped)

    def start_auto_attack(self):
        actions.STOP_EVENT.clear()
        self.run_action("auto_attack", actions.auto_attack)

    def stop_auto_attack(self):
        if self.current_action is None:
            print("Nothing running.")
            return
        print("Stop requested - finishing current step...")
        actions.STOP_EVENT.set()

    def quit_app(self):
        actions.STOP_EVENT.set()
        self.executor.shutdown(wait=False)
        os._exit(0)

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------
    def _start_hotkey_listener(self):
        mapping = {
            HOTKEYS["START_FIND"]["key"]: ("start_find", actions.start_find),
            HOTKEYS["ATTACK"]["key"]: ("attack", actions.attack),
            HOTKEYS["SURRENDER"]["key"]: ("surrender", actions.surrender),
            HOTKEYS["RECORD"]["key"]: ("record_position", actions.record_position),
        }
        auto_key = HOTKEYS["AUTO_ATTACK"]["key"]
        kill_key = HOTKEYS["KILL"]["key"]
        stop_key = HOTKEYS["STOP"]["key"]

        def on_press(key):
            char = getattr(key, "char", None)
            if char is None:
                return
            if char == kill_key:
                self.quit_app()
            elif char == auto_key:
                self.start_auto_attack()
            elif char == stop_key:
                self.stop_auto_attack()
            elif char in mapping:
                name, func = mapping[char]
                self.run_action(name, func)

        self.listener = keyboard.Listener(on_press=on_press, daemon=True)
        self.listener.start()

    # ------------------------------------------------------------------
    # Periodic updates (main thread)
    # ------------------------------------------------------------------
    def _tick(self):
        self._drain_log()
        self._update_status()
        self.root.after(120, self._tick)

    def _drain_log(self):
        chunks = []
        while True:
            try:
                chunks.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return
        self.log.configure(state="normal")
        self.log.insert("end", "".join(chunks))
        # Keep the log from growing without bound during long auto-attack runs.
        if int(self.log.index("end-1c").split(".")[0]) > 2000:
            self.log.delete("1.0", "500.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _update_status(self):
        action = self.current_action
        if action is None:
            text, color = "Idle", MUTED
        elif actions.STOP_EVENT.is_set():
            text, color = "Stopping...", ORANGE
        else:
            text, color = f"Running: {action}", GREEN
        if self.status_label.cget("text") != text:
            self.status_label.configure(text=text, fg=color)
            self.status_dot.configure(fg=color)

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def refresh_stats(self):
        try:
            with open(LOOT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
        except (OSError, json.JSONDecodeError):
            data = []

        self.stat_vars["Recorded battles"].set(str(len(data)))
        for label, key in (("Total gold", "total_gold"),
                           ("Total elixir", "total_elixir"),
                           ("Total dark", "total_dark")):
            total = sum(entry.get(key, 0) or 0 for entry in data)
            self.stat_vars[label].set(f"{total:,}".replace(",", " "))

        if data:
            last = data[-1]
            self.stat_vars["Last battle"].set(last.get("timestamp", "-")[-8:])
        else:
            self.stat_vars["Last battle"].set("-")


def main():
    root = tk.Tk()
    app = BotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
