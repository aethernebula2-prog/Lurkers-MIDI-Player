
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
from pathlib import Path

import mido
from pynput.mouse import Controller, Button
from pynput.keyboard import GlobalHotKeys


# =========================
# Configuration
# =========================

CONFIG_FILE = Path(__file__).with_name("config.json")

LOW_NOTE = 60       # C4
HIGH_NOTE = 84      # C6

BLACK_KEYS = {1, 3, 6, 8, 10}

NOTE_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B"
]

DEFAULT_CONFIG = {
    "x": 500,
    "y": 150,
    "width": 343,
    "height": 500,
    "white_ratio": 0.78,
    "black_ratio": 0.29,
    "minus_x": None,
    "minus_y": None,
    "plus_x": None,
    "plus_y": None
}

mouse = Controller()


def note_name(note):
    octave = note // 12 - 1
    return f"{NOTE_NAMES[note % 12]}{octave}"


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass

    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)


# =========================
# Main application
# =========================

class PianoPlayer:

    def __init__(self, root):
        self.root = root
        self.root.tk.call("tk", "scaling", 1.0)
        self.root.title("MIDI Piano Player")
        self.root.geometry("350x360")
        self.root.resizable(False, False)

        self.cfg = load_config()

        self.midi_events = []
        self.midi_duration = 0
        self.midi_name = "No MIDI selected"

        self.stop_event = threading.Event()
        self.playing = False
        self.current_low_note = 60  # 游戏初始音域 C4-C6
        self.pending_capture = None

        self.build_ui()
        self.build_overlay()

        # Global emergency-stop shortcuts (work even when this window is in the background)
        self.hotkey_listener = GlobalHotKeys({
            '<f8>': self.emergency_stop,
            '<esc>': self.emergency_stop,
            '<f6>': self.capture_minus_position,
            '<f7>': self.capture_plus_position,
        })
        self.hotkey_listener.start()

    # =====================
    # Main UI
    # =====================

    def build_ui(self):

        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="MIDI Piano Player",
            font=("Arial", 15, "bold")
        ).pack(pady=(0, 10))

        self.file_label = ttk.Label(
            main,
            text=self.midi_name
        )
        self.file_label.pack(pady=4)

        ttk.Button(
            main,
            text="Import MIDI",
            command=self.load_midi
        ).pack(fill="x", pady=4)

        speed_frame = ttk.Frame(main)
        speed_frame.pack(pady=6)

        ttk.Label(
            speed_frame,
            text="Speed:"
        ).pack(side="left", padx=5)

        self.speed = tk.StringVar(value="1.0")

        ttk.Combobox(
            speed_frame,
            textvariable=self.speed,
            values=["0.5", "0.75", "1.0", "1.25", "1.5", "2.0"],
            width=8,
            state="readonly"
        ).pack(side="left")

        ttk.Button(
            main,
            text="Show / Calibrate Piano",
            command=self.toggle_overlay
        ).pack(fill="x", pady=5)

        range_cal_frame = ttk.Frame(main)
        range_cal_frame.pack(fill="x", pady=3)

        ttk.Button(
            range_cal_frame,
            text="Set − position",
            command=lambda: self.arm_position_capture("minus")
        ).pack(side="left", expand=True, fill="x", padx=2)

        ttk.Button(
            range_cal_frame,
            text="Set + position",
            command=lambda: self.arm_position_capture("plus")
        ).pack(side="left", expand=True, fill="x", padx=2)

        ttk.Label(
            main,
            text="Hover over game − / +, then press F6 / F7",
            font=("Arial", 8)
        ).pack(pady=(0, 3))

        test_frame = ttk.Frame(main)
        test_frame.pack(pady=5)

        for note in [60, 61, 62]:
            ttk.Button(
                test_frame,
                text=note_name(note),
                command=lambda n=note: self.test_note(n)
            ).pack(side="left", padx=3)

        self.progress = ttk.Progressbar(
            main,
            maximum=100,
            mode="determinate"
        )
        self.progress.pack(fill="x", pady=8)

        control_frame = ttk.Frame(main)
        control_frame.pack(fill="x", pady=4)

        ttk.Button(
            control_frame,
            text="PLAY",
            command=self.play
        ).pack(side="left", expand=True, fill="x", padx=3)

        ttk.Button(
            control_frame,
            text="STOP",
            command=self.stop
        ).pack(side="left", expand=True, fill="x", padx=3)

        self.status = ttk.Label(
            main,
            text="Ready"
        )
        self.status.pack(pady=5)

    # =====================
    # Calibration overlay
    # =====================

    def build_overlay(self):

        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.88)

        self.overlay.configure(bg="#333333")

        self.overlay.geometry(
            f"{self.cfg['width']}x{self.cfg['height']}"
            f"+{self.cfg['x']}+{self.cfg['y']}"
        )

        self.canvas = tk.Canvas(
            self.overlay,
            bg="#333333",
            highlightthickness=0,
            bd=0
        )

        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>", self.handle_press)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.save_frame)

        self.overlay.withdraw()

        # Draw after Tk has calculated the Canvas size
        self.overlay.after(100, self.draw_keys)

    
    def draw_keys(self):
        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return

        white_offsets = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]
        white_notes = [self.current_low_note + offset for offset in white_offsets]
        white_h = h / 15
        black_w = w * 0.58
        black_h = white_h * 0.62

        for i, note in enumerate(white_notes):
            y1 = h - (i + 1) * white_h
            y2 = h - i * white_h
            self.canvas.create_rectangle(
                0, y1, w, y2,
                fill="#eeeeee", outline="#777777", width=1
            )
            self.canvas.create_text(
                w * 0.78, (y1 + y2) / 2,
                text=note_name(note), fill="#222222", font=("Arial", 8)
            )

        for offset in range(1, 24):
            note = self.current_low_note + offset
            if note % 12 not in BLACK_KEYS:
                continue
            previous_white_offset = max(v for v in white_offsets if v < offset)
            white_index = white_offsets.index(previous_white_offset)
            center_y = h - (white_index + 1) * white_h
            y1 = center_y - black_h / 2
            y2 = center_y + black_h / 2
            self.canvas.create_rectangle(
                0, y1, black_w, y2,
                fill="#20232b", outline="#555b66", width=1
            )
            self.canvas.create_text(
                black_w * 0.5, center_y,
                text=note_name(note), fill="#ffffff", font=("Arial", 8)
            )

        self.canvas.create_rectangle(
            1, 1, w - 1, h - 1,
            outline="#999999", width=2
        )
        self.canvas.create_rectangle(
            w - 20, h - 20, w, h,
            fill="#8b7cff", outline="white", width=1
        )

    # =====================
    # Move overlay
    # =====================

    def drag_start(self, event):
        self.drag_x = event.x_root
        self.drag_y = event.y_root
        self.start_x = self.cfg["x"]
        self.start_y = self.cfg["y"]

    def drag_move(self, event):

        dx = event.x_root - self.drag_x
        dy = event.y_root - self.drag_y

        x = self.start_x + dx
        y = self.start_y + dy

        self.cfg["x"] = x
        self.cfg["y"] = y

        self.overlay.geometry(
            f"+{x}+{y}"
        )

    # =====================
    # Resize overlay
    # =====================

    def resize_start(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root

        self.start_width = self.cfg["width"]
        self.start_height = self.cfg["height"]

    def resize_move(self, event):
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y

        self.cfg["width"] = max(100, self.start_width + dx)
        self.cfg["height"] = max(150, self.start_height + dy)

        self.overlay.geometry(
            f"{self.cfg['width']}x{self.cfg['height']}"
            f"+{self.cfg['x']}+{self.cfg['y']}"
        )

        self.draw_keys()

    def handle_press(self, event):
        margin = 30

        if (
            event.x >= self.canvas.winfo_width() - margin
            and event.y >= self.canvas.winfo_height() - margin
        ):
            self.resize_start(event)
            self.resizing = True
        else:
            self.resizing = False
            self.drag_start(event)

    def handle_drag(self, event):
        if self.resizing:
            self.resize_move(event)
        else:
            self.drag_move(event)

    def save_frame(self, event=None):

        self.cfg["x"] = self.overlay.winfo_x()
        self.cfg["y"] = self.overlay.winfo_y()
        self.cfg["width"] = self.overlay.winfo_width()
        self.cfg["height"] = self.overlay.winfo_height()

        save_config(self.cfg)

    def toggle_overlay(self):

        if self.overlay.state() == "withdrawn":
            self.overlay.deiconify()
            self.overlay.lift()
            self.overlay.after(100, self.draw_keys)
        else:
            self.save_frame()
            self.overlay.withdraw()

    def arm_position_capture(self, target):
        if self.playing:
            return
        self.pending_capture = target
        symbol = "−" if target == "minus" else "+"
        hotkey = "F6" if target == "minus" else "F7"
        self.status.config(text=f"Hover over game {symbol}, then press {hotkey}")

    def capture_minus_position(self):
        self._capture_range_position("minus")

    def capture_plus_position(self):
        self._capture_range_position("plus")

    def _capture_range_position(self, target):
        if self.pending_capture != target:
            return
        x, y = mouse.position
        self.cfg[f"{target}_x"] = int(x)
        self.cfg[f"{target}_y"] = int(y)
        self.pending_capture = None
        save_config(self.cfg)
        symbol = "−" if target == "minus" else "+"
        self.root.after(0, lambda: self.status.config(
            text=f"Saved {symbol} position: {int(x)}, {int(y)}"
        ))

    def click_range_button(self, target):
        x = self.cfg.get(f"{target}_x")
        y = self.cfg.get(f"{target}_y")
        if x is None or y is None:
            symbol = "−" if target == "minus" else "+"
            raise RuntimeError(f"请先校准游戏的 {symbol} 按钮位置")
        if self.stop_event.is_set():
            return False
        mouse.position = (int(x), int(y))
        mouse.click(Button.left, 1)
        if target == "minus":
            self.current_low_note -= 12
        else:
            self.current_low_note += 12
        # 等待游戏完成音域切换，再点击琴键
        if self.stop_event.wait(0.15):
            return False
        return True

    def ensure_note_in_range(self, note):
        while note < self.current_low_note:
            if not self.click_range_button("minus"):
                return False
        while note > self.current_low_note + 24:
            if not self.click_range_button("plus"):
                return False
        return not self.stop_event.is_set()

    # =====================
    # Note coordinates
    # =====================

    
    def note_position(self, note):
        white_offsets = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24]
        relative = note - self.current_low_note

        w = self.cfg["width"]
        h = self.cfg["height"]
        white_h = h / 15

        if relative in white_offsets:
            index = white_offsets.index(relative)
            x = self.cfg["x"] + w * self.cfg["white_ratio"]
            y = self.cfg["y"] + h - (index + 0.5) * white_h
        elif 1 <= relative <= 23 and note % 12 in BLACK_KEYS:
            previous_white_offset = max(v for v in white_offsets if v < relative)
            index = white_offsets.index(previous_white_offset)
            x = self.cfg["x"] + w * self.cfg["black_ratio"]
            y = self.cfg["y"] + h - (index + 1) * white_h
        else:
            return None

        return int(x), int(y)

    def click_note(self, note):

        pos = self.note_position(note)

        if pos is None:
            return

        x, y = pos

        mouse.position = (x, y)
        mouse.click(Button.left, 1)

    def test_note(self, note):

        if self.playing:
            return

        self.overlay.withdraw()

        self.status.config(
            text=f"Testing {note_name(note)}..."
        )

        def do_test():
            time.sleep(0.3)
            self.click_note(note)
            self.root.after(
                0,
                lambda: self.status.config(
                    text=f"Tested {note_name(note)}"
                )
            )

        threading.Thread(
            target=do_test,
            daemon=True
        ).start()

    # =====================
    # MIDI loading
    # =====================

    def load_midi(self):

        path = filedialog.askopenfilename(
            filetypes=[
                ("MIDI files", "*.mid *.midi"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:

            midi = mido.MidiFile(path)

            events = []
            current_time = 0.0

            # MidiFile iteration converts delta ticks to seconds
            for msg in midi:

                current_time += msg.time

                if (
                    msg.type == "note_on"
                    and msg.velocity > 0
                ):
                    if 0 <= msg.note <= 127:
                        events.append(
                            (current_time, msg.note)
                        )

            if not events:
                messagebox.showwarning(
                    "No notes",
                    "No MIDI note events were found."
                )
                return

            self.midi_events = events
            self.midi_duration = current_time
            self.midi_name = Path(path).name

            self.file_label.config(
                text=self.midi_name
            )

            self.progress["value"] = 0

            self.status.config(
                text=f"Loaded {len(events)} notes"
            )

        except Exception as e:

            messagebox.showerror(
                "MIDI Error",
                str(e)
            )

    # =====================
    # Playback
    # =====================

    def play(self):

        if self.playing:
            return

        if not self.midi_events:
            messagebox.showwarning(
                "No MIDI",
                "Please import a MIDI file first."
            )
            return

        self.stop_event.clear()
        self.playing = True

        self.overlay.withdraw()

        self.status.config(text="Playing...")
        self.progress["value"] = 0

        threading.Thread(
            target=self.play_worker,
            daemon=True
        ).start()

    def play_worker(self):

        speed = float(self.speed.get())

        start_time = time.monotonic()

        try:

            for index, (event_time, note) in enumerate(self.midi_events):

                if self.stop_event.is_set():
                    break

                target_time = start_time + event_time / speed

                while True:

                    if self.stop_event.is_set():
                        break

                    remaining = target_time - time.monotonic()

                    if remaining <= 0:
                        break

                    self.stop_event.wait(
                        min(remaining, 0.01)
                    )

                if self.stop_event.is_set():
                    break

                if not self.ensure_note_in_range(note):
                    break

                self.click_note(note)

                progress = (
                    (index + 1) / len(self.midi_events)
                ) * 100

                self.root.after(
                    0,
                    lambda p=progress:
                    self.progress.config(value=p)
                )

        except Exception as e:

            self.root.after(
                0,
                lambda err=e:
                messagebox.showerror("Playback Error", str(err))
            )

        finally:

            self.playing = False

            self.root.after(
                0,
                self.playback_finished
            )

    def playback_finished(self):

        if self.stop_event.is_set():
            self.status.config(text="Stopped")
        else:
            self.status.config(text="Finished")

        self.progress["value"] = (
            0 if self.stop_event.is_set() else 100
        )

    def stop(self):

        if self.playing:
            self.stop_event.set()
            self.status.config(text="Stopping...")

    def emergency_stop(self):
        # Called by pynput's global keyboard listener thread.
        # Only signal the worker here; Tkinter UI updates happen in the main thread.
        self.stop_event.set()


# =========================
# Start
# =========================

if __name__ == "__main__":

    root = tk.Tk()

    print("load_midi exists:", hasattr(PianoPlayer, "load_midi"))
    print("PianoPlayer methods:", [
        name for name in dir(PianoPlayer)
        if not name.startswith("__")
    ])

    app = PianoPlayer(root)

    def on_close():
        app.stop()
        app.hotkey_listener.stop()
        save_config(app.cfg)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()
