# MIDI Piano Player

A Python-based desktop MIDI automation tool that reads MIDI files and plays notes by clicking the keys of an in-game vertical piano.
Currently designed for Linux X11 and Windows 10+ to play the instruments in Lurkers.io (an online video game by Bergice Productions).

## !Important! (Must Read Before Use)

During playback, the program takes control of the system mouse. Make sure the game window and calibration coordinates are correct before starting.

If playback behaves unexpectedly, press `F8` or `Esc` to stop it immediately.

Do not test extremely long MIDI files or any Black MIDI.

While the playback is going, please stop it first before going to another window.

You might be banned by using automation script, so ask moderators or developers is recommended, and promise never use the player for any other purposes.

## Features

- Import `.mid` and `.midi` files.
- Automatically click the corresponding keys according to MIDI event timing.
- Adjustable playback speed: `0.5x`, `0.75x`, `1.0x`, `1.25x`, `1.5x`, and `2.0x`.
- Movable and resizable calibration overlay for aligning the keys.
- Supports both white-key and black-key coordinate calculations.
- Default piano range (Same as ingame): **C4–C6**.
- Automatically click the `−` and `+` buttons above the in-game piano to change the octave range.
- Saves piano position, size, and octave button coordinates in `config.json`.
- Global emergency-stop shortcuts that work even when the player window is in the background.

## Keyboard Shortcuts

| Shortcut | Function |
|---|---|
| `F8` | Emergency stop |
| `Esc` | Emergency stop |
| `F6` | Save the position of the in-game `−` button during calibration |
| `F7` | Save the position of the in-game `+` button during calibration |

## Requirements

- Linux X11 or Windows desktop environment
- Python 3.1+
- Tkinter
- mido
- pynput

> If you are using a Linux Wayland session, global shortcuts or mouse control may not work correctly. An X11 session is recommended.

## Installation (Linux)

First, ensure you have python:

```bash
python3 --version
```

If you don't have python yet:

```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

Navigate to the project directory (It can be other directory):

```bash
cd ~/Downloads/midi-piano-player
```

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the required Python packages:

```bash
python -m pip install --upgrade pip
python -m pip install mido pynput
```

If Tkinter is not installed, you can install it on Debian, Ubuntu or Linux Mint with:

```bash
sudo apt install python3-tk python3-venv
```

## Installation (Windows)

First, ensure you have python:

```bash
python --version
```

Use winget to install python:

```bash
winget install Python.Python.3.13
```

Use PowerShell to install python:

```bash
$installer = "$env:TEMP\python-installer.exe"
Invoke-WebRequest "https://www.python.org/ftp/python/3.13.9/python-3.13.9-amd64.exe" -OutFile $installer
Start-Process $installer -Wait
```

Install python packages:

```bash
py -m venv venv
venv\Scripts\activate.bat
python -m pip install mido pynput
python main.py
```

## Running the Application

Make sure you are in the project directory and your virtual environment is activated.

Run:

```bash
python main.py
```

If you are not in the project directory:

```bash
python your extracted py file path
```

## Initial Calibration

### 1. Calibrating the Piano Area

1. Make sure the in-game instrument's keyboard is visible, which by right click screen when you are holding an instrument.
2. Click **Show / Calibrate Piano** in the player.
3. Drag the calibration overlay to align it with the in-game piano.
4. Resize the overlay using the purple rectangle in the bottom-right corner.
5. Click the button again to hide the overlay when calibration is complete.

The overlay position and size are saved in `config.json`.

### 2. Calibrating the Octave Buttons

The in-game `−` button is located near the upper-left corner of the piano, while the `+` button is near the upper-right corner.

To calibrate the `−` button:

1. Click **Set − position** in the player.
2. Move the mouse to the center of the in-game `−` button.
3. Press `F6` to save its position.

To calibrate the `+` button:

1. Click **Set + position** in the player.
2. Move the mouse to the center of the in-game `+` button.
3. Press `F7` to save its position.

Pressing `F6` or `F7` during calibration only records the current mouse coordinates. It does not click the in-game buttons.

## How to Use

1. Make sure the in-game piano is currently set to **C4–C6**.
2. Confirm that the piano area and the `−` / `+` buttons have been calibrated.
3. Click **Import MIDI** and select a MIDI file.
4. Choose a playback speed.
5. Click **PLAY** to start playback.
6. To stop playback, click **STOP** or press `F8` / `Esc`.

## How It Works & Limitations

- The program triggers notes by clicking the ingame keyboard with the system mouse. It does not need to connect directly to a MIDI device.
- A mouse pointer can only be at one position at a time. Therefore, notes that occur simultaneously must be clicked one after another rather than pressed simultaneously.
- Very dense MIDI files, such as Black MIDI, may sound like rapid, chaotic clicking. Missed notes and timing inaccuracies may also occur. This is a limitation of mouse-based playback.
- The current implementation processes `note_on` events and clicks the corresponding keys. It is not a full MIDI synthesizer and does not use `note_off` events to control how long a key is held.
- Automatic octave switching depends on correctly calibrated `−` and `+` button coordinates. Make sure the game piano starts at C4–C6 before playback.
- It is recommended to test key positions, octave switching, and emergency-stop shortcuts with a short MIDI file before playing longer or denser files.

## Configuration

The program reads and writes `config.json` in the same directory as `main.py`.

The configuration includes:

- Calibration overlay position and dimensions
- White-key and black-key click position ratios
- Screen coordinates of the in-game `−` and `+` buttons

If you change your monitor, resolution, display scaling, or game window position, you may need to recalibrate the piano.

## Copyright & License

Copyright © 2026 AethericNebula.

Original code was posted on GitHub.

MIT License

## Disclaimer

This software is provided "as is", without warranty of any kind.

The author is not responsible for:
- Any unintended mouse or keyboard input.
- Unexpected behavior during MIDI playback.
- Data loss or other issues caused by using this software.
- Any consequences resulting from its use in third-party games
  or applications.

Use this software at your own risk.

Users are responsible for ensuring that their use complies
with the rules and terms of service of the applications
they interact with.