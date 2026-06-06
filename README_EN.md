<div align="center">

# Keyboard Key Display

A Linux desktop keyboard key display application that listens to global keyboard input even when the window is not focused, and displays the currently pressed keys using a visual keyboard layout.

When starting, it will request permissions. Rest assured, our code is harmless, and you are free to review it.
</div>


## Features

- Global keyboard listening on Linux, no need for the application window to be focused.
- Visual keyboard layout.
- Key press highlighting.
- Always-on-top window support.
- Configurable window transparency, corner radius, border color, key colors, etc.
- Customizable keyboard layout.
- Supports both frameless windows and system native title bar windows.

## Requirements

- Linux desktop environment.
- Python 3.
- tkinter.
- Read permission for `/dev/input`.

On Debian / Ubuntu, if tkinter is missing, you can install it with:

```bash
sudo apt install python3-tk
```

## Getting Started

Navigate to the project directory:

```bash
# For example, if you are in the /home/thinkreally/work/keyb desket directory
cd "/home/thinkreally/work/keyb desket"
./run.sh
```

You can also run it directly:

```bash
python3 key_display.py
```

If the current user does not have read permission for `/dev/input`, `run.sh` will automatically start the application using `sudo -E python3 key_display.py`.

## Closing the Application

- Click the window close button.
- Press `Ctrl + Q` to exit the application.
- If the window cannot be closed normally, you can execute the following in a terminal:

```bash
sudo pkill -f key_display.py
```

## Configuration

The application's appearance and layout are configured via `config.json`.

### window

| Field | Description |
| --- | --- |
| `alpha` | Window transparency, range `0.0` to `1.0`. |
| `always_on_top` | Whether the window should always stay on top. |
| `corner_radius` | Window corner radius. |
| `frameless` | Whether to use a frameless window. `true` for frameless, `false` for system native title bar. |

### colors

| Field | Description |
| --- | --- |
| `background` | Main background color. |
| `border` | Window border color. |
| `title_bar` | Custom title bar background color. |
| `text` | Title text color. |
| `text_glow` | Reserved highlight text color. |
| `key_idle` | Key text color when idle. |
| `key_active` | Key background/border color when pressed. |
| `key_text` | Key text color when pressed. |
| `key_border` | Key border color when idle. |
| `status_online` | Status indicator color. |
| `close_button` | Close button color. |
| `close_button_hover` | Close button hover color. |

### keyboard

| Field | Description |
| --- | --- |
| `layout` | Custom keyboard layout, a 2D array where each string represents a key. |
| `key_width` | Standard key width. |
| `key_height` | Key height. |
| `key_padding` | Key spacing. |
| `key_radius` | Key corner radius. |
| `font_size` | Key font size. |

Example:

```json
{
    "window": {
        "alpha": 0.2,
        "always_on_top": true,
        "corner_radius": 30,
        "frameless": false
    },
    "keyboard": {
        "layout": [
            ["Esc", "1", "2", "3", "Backspace"],
            ["Tab", "Q", "W", "E", "R"],
            ["Ctrl", "A", "S", "D", "Enter"]
        ],
        "key_width": 42,
        "key_height": 42,
        "key_padding": 3,
        "key_radius": 13,
        "font_size": 10
    }
}
```

## Wayland and X11 Notes

- This application has only been tested on Ubuntu 26.04 LTS Wayland.
- Wayland has stricter restrictions on applications moving windows, transparent windows, and transparent corners.
- If you are using Wayland, it is recommended to set `window.frameless` to `false` and use the system native title bar to move and close the window.
- If you are using X11, you can try setting `window.frameless` to `true` to use a frameless window.
- tkinter's `alpha` and transparent corners may not fully work under Wayland due to the fucking window manager limitations.

## Permissions

Global keyboard listening requires reading from `/dev/input/event*`. There are typically two ways to achieve this:

- Start the application using `sudo`.
- Add the current user to the `input` user group.

Example of adding to the `input` group:

```bash
sudo usermod -aG input $USER
```

You will need to log out and log back in for the changes to take effect.

## Notes

Thank you for supporting my project.

Since I am not very familiar with GitHub and I am just a junior high school student, I may not be able to respond to your Pull Requests and Issues in a timely manner. Please be patient.

If the issue is complex, I may need more time to resolve it.

(Fucking Wayland made me fix more bugs)
