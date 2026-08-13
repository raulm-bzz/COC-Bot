"""Tkinter front-end for the COC bot - window with buttons, a live log, and
global hotkeys."""

# --- Standard Library ---
import os
import sys
import queue
import threading
import traceback
import tkinter as tk
import tkinter.font as tkfont
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

# --- Colors: purple theme ---
BG           = "#150f24"   # window background
PANEL        = "#1f1736"   # card fill
BTN          = "#2c2249"   # button idle
BTN_HL       = "#3b2e5e"   # button hover
BORDER       = "#372c54"   # subtle card outline
FG           = "#f2eefb"   # primary text
MUTED        = "#9c8fc0"   # secondary text
HEADING      = "#b9a6e8"   # section labels
ACCENT       = "#a855f7"   # primary purple accent
ACCENT_HOVER = "#bd7bfa"
ON_ACCENT    = "#1c1030"   # text on accent/red buttons
RED          = "#fb7185"
RED_HOVER    = "#fda1ac"
GREEN        = "#34d399"
ORANGE       = "#fbbf24"
LOG_BG       = "#130d20"
LOG_FG       = "#d7cdee"


def _rounded_points(x1, y1, x2, y2, r):
    """Point list for a rounded rectangle, meant for create_polygon(smooth=True)."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


def _parent_bg(parent, fallback=BG):
    try:
        return parent.cget("bg")
    except tk.TclError:
        return fallback


class RoundedCard(tk.Canvas):
    """A Canvas with a rounded-rect background and a same-colored `.body`
    Frame inset inside it, so normal widgets can be packed/gridded as usual."""

    def __init__(self, parent, fill, radius=18, border=None, bg_out=None, **kw):
        super().__init__(parent, bg=bg_out or _parent_bg(parent), highlightthickness=0,
                          bd=0, **kw)
        self.fill = fill
        self.radius = radius
        self.border = border
        self.inset = max(radius - 6, 6)
        self.body = tk.Frame(self, bg=fill)
        self._win = self.create_window(self.inset, self.inset, anchor="nw", window=self.body)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        w, h = self.winfo_width(), self.winfo_height()
        self.delete("bg")
        if w > 2 and h > 2:
            pts = _rounded_points(1, 1, w - 1, h - 1, self.radius)
            self.create_polygon(pts, smooth=True, fill=self.fill,
                                 outline=self.border or self.fill, tags="bg")
            self.tag_lower("bg")
        self.coords(self._win, self.inset, self.inset)
        self.itemconfigure(self._win, width=max(0, w - 2 * self.inset),
                           height=max(0, h - 2 * self.inset))

    def fit_height(self):
        """Size the card to its body's natural content height (call after packing)."""
        self.body.update_idletasks()
        self.configure(height=self.body.winfo_reqheight() + 2 * self.inset)


class RoundedButton(tk.Canvas):
    """A clickable rounded-rect button drawn on a Canvas, since ttk/tk widgets
    can't do border-radius."""

    def __init__(self, parent, text, command, fill, hover, fg=FG,
                 radius=10, font=("Segoe UI Semibold", 10), height=38,
                 width=None, padx=16, **kw):
        self._font = tkfont.Font(family=font[0], size=font[1],
                                  weight=font[2] if len(font) > 2 else "normal")
        if width is None:
            width = self._font.measure(text) + padx * 2
        super().__init__(parent, bg=_parent_bg(parent), highlightthickness=0, bd=0,
                         width=width, height=height, cursor="hand2", **kw)
        self.command = command
        self.text = text
        self.fill = fill
        self.hover = hover
        self.fg = fg
        self.radius = radius
        self.font = font
        self._hovering = False

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _redraw(self, event=None):
        w, h = max(self.winfo_width(), 2), max(self.winfo_height(), 2)
        self.delete("all")
        color = self.hover if self._hovering else self.fill
        pts = _rounded_points(1, 1, w - 1, h - 1, min(self.radius, h / 2 - 1))
        self.create_polygon(pts, smooth=True, fill=color, outline=color)
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=self.font)

    def _on_enter(self, _e):
        self._hovering = True
        self._redraw()

    def _on_leave(self, _e):
        self._hovering = False
        self._redraw()

    def _on_click(self, _e):
        if self.command:
            self.command()


class StatusPill(tk.Canvas):
    """A small rounded 'chip' showing a colored dot + status text."""

    def __init__(self, parent, fill, font=("Segoe UI Semibold", 10), **kw):
        super().__init__(parent, bg=_parent_bg(parent), highlightthickness=0, bd=0, **kw)
        self.fill = fill
        self.font_spec = font
        self._font = tkfont.Font(family=font[0], size=font[1],
                                  weight=font[2] if len(font) > 2 else "normal")
        self.text = "Idle"
        self.color = MUTED
        self.set(self.text, self.color)

    def set(self, text, color):
        self.text, self.color = text, color
        pad_x, dot_r, gap = 14, 4, 8
        w = pad_x * 2 + dot_r * 2 + gap + self._font.measure(text)
        h = 30
        self.configure(width=w, height=h)
        self.delete("all")
        pts = _rounded_points(0, 0, w, h, h / 2)
        self.create_polygon(pts, smooth=True, fill=self.fill, outline=self.fill)
        cx, cy = pad_x + dot_r, h / 2
        self.create_oval(cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r,
                         fill=color, outline=color)
        self.create_text(cx + dot_r + gap, cy, text=text, fill=FG,
                         font=self.font_spec, anchor="w")


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
        root.geometry("940x680")
        root.minsize(760, 540)
        root.configure(bg=BG)

        self._build_header()
        self._build_body()
        self._build_log()

        # Everything printed by actions.py from here on lands in the log panel.
        sys.stdout = LogStream(self.log_queue, sys.__stdout__)
        sys.stderr = LogStream(self.log_queue, sys.__stderr__)

        self._start_hotkey_listener()
        self._tick()

        print("GUI ready. Hotkeys are active globally.")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=18, pady=(18, 10))

        tk.Label(header, text="COC Attack Bot", bg=BG, fg=FG,
                font=("Segoe UI Semibold", 17)).pack(side="left")

        self.status_pill = StatusPill(header, fill=PANEL)
        self.status_pill.pack(side="right")

    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="x", padx=18)
        body.columnconfigure(0, weight=1, uniform="col")
        body.columnconfigure(1, weight=1, uniform="col")

        # --- Actions card ---
        actions_card = RoundedCard(body, fill=PANEL, radius=18, border=BORDER, bg_out=BG)
        actions_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        a = actions_card.body

        tk.Label(a, text="ACTIONS", bg=PANEL, fg=HEADING,
                font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=4, pady=(2, 10))

        grid = tk.Frame(a, bg=PANEL)
        grid.pack(fill="x", padx=4)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        buttons = [
            ("Start Find", lambda: self.run_action("start_find", actions.start_find)),
            ("Attack", lambda: self.run_action("attack", lambda: actions.attack(self.sequence_var.get()))),
            ("Surrender", lambda: self.run_action("surrender", actions.surrender)),
            ("Record Position", lambda: self.run_action("record_position", actions.record_position)),
        ]
        for i, (text, cmd) in enumerate(buttons):
            btn = RoundedButton(grid, text, cmd, fill=BTN, hover=BTN_HL, radius=10, height=40)
            btn.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4)

        seq_row = tk.Frame(a, bg=PANEL)
        seq_row.pack(fill="x", padx=4, pady=(10, 4))
        tk.Label(seq_row, text="Sequence:", bg=PANEL, fg=MUTED,
                font=("Segoe UI", 9)).pack(side="left")

        seq_names = actions.list_sequences() or ["(no sequences found)"]
        self.sequence_var = tk.StringVar(value=seq_names[0])

        self.sequence_menu = tk.OptionMenu(seq_row, self.sequence_var, *seq_names)
        self.sequence_menu.configure(bg=BTN, fg=FG, activebackground=BTN_HL,
                                     activeforeground=FG, highlightthickness=0,
                                     bd=0, font=("Segoe UI", 9), width=14, anchor="w")
        self.sequence_menu["menu"].configure(bg=PANEL, fg=FG,
                                             activebackground=BTN_HL, activeforeground=FG)
        self.sequence_menu.pack(side="left", padx=(8, 0))

        run_row = tk.Frame(a, bg=PANEL)
        run_row.pack(fill="x", padx=4, pady=(6, 4))
        run_row.columnconfigure(0, weight=1)
        run_row.columnconfigure(1, weight=1)

        RoundedButton(run_row, "▶  Auto Attack", self.start_auto_attack,
                     fill=ACCENT, hover=ACCENT_HOVER, fg=ON_ACCENT, radius=10,
                     height=42).grid(row=0, column=0, sticky="ew", padx=4)
        RoundedButton(run_row, "■  Stop", self.stop_auto_attack,
                     fill=RED, hover=RED_HOVER, fg=ON_ACCENT, radius=10,
                     height=42).grid(row=0, column=1, sticky="ew", padx=4)

        actions_card.fit_height()

        # --- Hotkeys card ---
        hotkeys_card = RoundedCard(body, fill=PANEL, radius=18, border=BORDER, bg_out=BG)
        hotkeys_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        h = hotkeys_card.body

        tk.Label(h, text="HOTKEYS", bg=PANEL, fg=HEADING,
                font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=4, pady=(2, 10))

        for d in HOTKEYS.values():
            row = tk.Frame(h, bg=PANEL)
            row.pack(fill="x", padx=4, pady=5)
            tk.Label(row, text=d["key"].upper(), bg=BTN, fg=ACCENT,
                    font=("Consolas", 11, "bold"), width=3,
                    relief="solid", bd=1, highlightbackground=BORDER
                    ).pack(side="left", ipady=3)
            tk.Label(row, text=d["description"], bg=PANEL, fg=FG,
                    font=("Segoe UI", 10)).pack(side="left", padx=(10, 0))

        hotkeys_card.fit_height()

    def _build_log(self):
        card = RoundedCard(self.root, fill=PANEL, radius=18, border=BORDER, bg_out=BG)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        wrap = card.body

        head = tk.Frame(wrap, bg=PANEL)
        head.pack(fill="x", pady=(0, 6))
        tk.Label(head, text="LOG", bg=PANEL, fg=HEADING,
                font=("Segoe UI Semibold", 9)).pack(side="left")
        RoundedButton(head, "Clear", self.clear_log, fill=PANEL, hover=BTN,
                     fg=MUTED, radius=8, height=24, font=("Segoe UI", 9),
                     padx=10).pack(side="right")

        text_frame = tk.Frame(wrap, bg=LOG_BG)
        text_frame.pack(fill="both", expand=True)

        self.log = tk.Text(text_frame, bg=LOG_BG, fg=LOG_FG, bd=0,
                           font=("Consolas", 9), wrap="word", insertbackground=FG,
                           padx=10, pady=8, state="disabled")
        scroll = tk.Scrollbar(text_frame, command=self.log.yview, bg=BTN,
                              troughcolor=LOG_BG, activebackground=BTN_HL,
                              highlightthickness=0, bd=0, relief="flat",
                              elementborderwidth=0, width=12)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

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
        sequence_name = self.sequence_var.get()
        self.run_action("auto_attack", lambda: actions.auto_attack(sequence_name))

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
    # Sequence recording
    # ------------------------------------------------------------------
    def _toggle_recording(self):
        """Called from the hotkey listener thread - only touches Tk via root.after."""
        if actions.is_recording():
            events = actions.stop_recording()
            self.root.after(0, lambda: self._prompt_recording_name(events))
        else:
            actions.start_recording()

    def _prompt_recording_name(self, events):
        if not events:
            print("Recording had no events - nothing to save.")
            return

        actions.set_input_locked(True)

        dialog = tk.Toplevel(self.root)
        dialog.title("Save Recording")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        # Covers Save, Discard, Esc, and the window's own close button alike.
        dialog.bind("<Destroy>", lambda _e: actions.set_input_locked(False))

        tk.Label(dialog, text="Name this sequence:", bg=BG, fg=FG,
                font=("Segoe UI Semibold", 10)).pack(padx=18, pady=(18, 8), anchor="w")

        entry = tk.Entry(dialog, bg=PANEL, fg=FG, insertbackground=FG,
                         relief="flat", font=("Segoe UI", 10), width=30)
        entry.pack(padx=18, pady=(0, 14), fill="x", ipady=4)
        entry.focus_set()

        def do_save(_e=None):
            name = entry.get().strip()
            if not name:
                return
            actions.save_recording(name, events)
            self._refresh_sequence_menu()
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.pack(padx=18, pady=(0, 18), fill="x")
        RoundedButton(btn_row, "Save", do_save, fill=ACCENT, hover=ACCENT_HOVER,
                     fg=ON_ACCENT, radius=10, height=34).pack(side="right")
        RoundedButton(btn_row, "Discard", dialog.destroy, fill=BTN, hover=BTN_HL,
                     fg=FG, radius=10, height=34).pack(side="right", padx=(0, 8))

        entry.bind("<Return>", do_save)
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

    def _refresh_sequence_menu(self):
        """Repopulates the sequence dropdown, e.g. after a new recording is saved."""
        names = actions.list_sequences() or ["(no sequences found)"]
        menu = self.sequence_menu["menu"]
        menu.delete(0, "end")
        for name in names:
            menu.add_command(label=name, command=lambda n=name: self.sequence_var.set(n))
        if self.sequence_var.get() not in names:
            self.sequence_var.set(names[0])

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------
    def _start_hotkey_listener(self):
        mapping = {
            HOTKEYS["START_FIND"]["key"]: ("start_find", actions.start_find),
            HOTKEYS["ATTACK"]["key"]: ("attack", lambda: actions.attack(self.sequence_var.get())),
            HOTKEYS["SURRENDER"]["key"]: ("surrender", actions.surrender),
            HOTKEYS["RECORD"]["key"]: ("record_position", actions.record_position),
        }
        auto_key = HOTKEYS["AUTO_ATTACK"]["key"]
        kill_key = HOTKEYS["KILL"]["key"]
        stop_key = HOTKEYS["STOP"]["key"]

        def on_press(key):
            char = getattr(key, "char", None)

            # --- KILL ALWAYS WORKS, even mid-recording / while naming ---
            if char == kill_key:
                self.quit_app()
                return

            # --- While the "name this sequence" dialog is up, ignore every
            # other hotkey so typing e.g. "s" doesn't also trigger attack() ---
            if actions.is_input_locked():
                return

            if key == keyboard.Key.home:
                self._toggle_recording()
                return

            if char == stop_key:
                self.stop_auto_attack()
                return

            if actions.is_recording():
                key_name = char if char is not None else str(key).replace("Key.", "")
                actions.record_key_event(key_name)
                return

            if char is None:
                return
            if char == auto_key:
                self.start_auto_attack()
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
        if text != self.status_pill.text:
            self.status_pill.set(text, color)

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main():
    root = tk.Tk()
    app = BotGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app)
    root.mainloop()


if __name__ == "__main__":
    main()
