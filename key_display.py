#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import struct
import threading
import os
import glob
import time
from collections import deque


EVENT_FORMAT = 'llHHi'
EVENT_SIZE = struct.calcsize(EVENT_FORMAT)

EV_KEY = 0x01
EV_REL = 0x02

REL_X = 0x00
REL_Y = 0x01

KEY_PRESS = 1
KEY_RELEASE = 0

KEY_MAP = {
    1: 'Esc', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
    12: '-', 13: '=', 14: 'Backspace', 15: 'Tab',
    16: 'Q', 17: 'W', 18: 'E', 19: 'R', 20: 'T', 21: 'Y', 22: 'U', 23: 'I', 24: 'O', 25: 'P',
    26: '[', 27: ']', 28: 'Enter', 29: 'Ctrl',
    30: 'A', 31: 'S', 32: 'D', 33: 'F', 34: 'G', 35: 'H', 36: 'J', 37: 'K', 38: 'L',
    39: ';', 40: "'", 41: '`', 42: 'Shift', 43: '\\',
    44: 'Z', 45: 'X', 46: 'C', 47: 'V', 48: 'B', 49: 'N', 50: 'M',
    51: ',', 52: '.', 53: '/', 54: 'Shift', 55: '*', 56: 'Alt', 57: 'Space',
    58: 'CapsLock', 59: 'F1', 60: 'F2', 61: 'F3', 62: 'F4', 63: 'F5', 64: 'F6',
    65: 'F7', 66: 'F8', 67: 'F9', 68: 'F10', 69: 'F11', 70: 'F12',
    71: 'ScrollLock', 72: 'Pause',
    73: 'Insert', 74: 'Home', 75: 'PageUp', 76: 'Delete', 77: 'End', 78: 'PageDown',
    79: 'Right', 80: 'Left', 81: 'Down', 82: 'Up',
    100: 'Alt', 125: 'Super', 126: 'Super',
    272: 'Mouse Left', 273: 'Mouse Right', 274: 'Mouse Middle', 275: 'Mouse Side', 276: 'Mouse Extra'
}

DEFAULT_CONFIG = {
    "window": {
        "alpha": 0.2,
        "always_on_top": True,
        "frameless": True,
        "corner_radius": 14,
        "position": {
            "x": None,
            "y": None
        },
        "mouse_position": {
            "x": None,
            "y": None
        }
    },
    "colors": {
        "background": "#1a1a2e",
        "border": "#e94560",
        "title_bar": "#0f3460",
        "text": "#e94560",
        "text_glow": "#ff6b6b",
        "key_idle": "#4a4a6a",
        "key_active": "#e94560",
        "key_text": "#ffffff",
        "key_border": "#533483",
        "status_online": "#00ff88",
        "close_button": "#ff6b6b",
        "close_button_hover": "#ffffff",
        "mouse_direction_trace": "#e94560"
    },
    "keyboard": {
        "layout": [
            ["Esc", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "Backspace"],
            ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Enter"],
            ["Shift", "Z", "X", "C", "V", "B", "N", "M"]
        ],
        "key_width": 42,
        "key_height": 42,
        "key_padding": 3,
        "key_radius": 8,
        "font_size": 10
    },
    "extra_display": {
        "show_mouse": False,
        "show_cps": False,
        "show_mouse_direction": False,
        "show_mouse_trace": True,
        "mouse_direction_decay": 1.25
    }
}


def get_user_config_path():
    """Get user-writable config path"""
    config_dir = os.path.expanduser('~/.config/keyboard-key-display')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')


def get_bundled_config_path():
    """Get bundled config path (read-only fallback)"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')


def merge_config(base, override):
    """Merge nested configuration dictionaries"""
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge_config(base[key], value)
        else:
            base[key] = value
    return base


def load_config():
    """Load configuration file"""
    user_path = get_user_config_path()
    bundled_path = get_bundled_config_path()

    config = create_default_config()

    # Load from bundled config first (if exists)
    try:
        if os.path.exists(bundled_path):
            with open(bundled_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            merge_config(config, file_config)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in bundled config: {e}")
    except Exception as e:
        print(f"Warning: Failed to load bundled config: {e}")

    # Override with user config (if exists), otherwise create it
    try:
        if os.path.exists(user_path):
            with open(user_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            merge_config(config, user_config)
        else:
            save_config(config)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in user config: {e}")
    except Exception as e:
        print(f"Warning: Failed to load user config: {e}")

    return config


def save_config(config):
    """Save configuration to user-writable config path"""
    user_path = get_user_config_path()
    with open(user_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def rounded_rectangle_points(x1, y1, x2, y2, radius):
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]


def create_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Create a rounded rectangle on canvas"""
    points = rounded_rectangle_points(x1, y1, x2, y2, radius)
    return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


def find_input_devices(include_mouse=False):
    """Find keyboard and optional mouse input devices"""
    input_devices = []
    try:
        with open('/proc/bus/input/devices', 'r') as f:
            content = f.read()
            sections = content.split('\n\n')
            for section in sections:
                section_lower = section.lower()
                is_keyboard = 'EV=' in section and ('120013' in section or '100013' in section or 'kbd' in section_lower)
                is_mouse = include_mouse and 'EV=' in section and ('mouse' in section_lower or 'touchpad' in section_lower)
                if is_keyboard or is_mouse:
                    for line in section.split('\n'):
                        if line.startswith('H: Handlers='):
                            handlers = line.split('=')[1].strip()
                            for handler in handlers.split():
                                if handler.startswith('event'):
                                    device_path = f'/dev/input/{handler}'
                                    if os.path.exists(device_path):
                                        input_devices.append(device_path)
    except Exception as e:
        print(f"Warning: Failed to parse input devices: {e}")
    if not input_devices:
        for event_file in sorted(glob.glob('/dev/input/event*')):
            input_devices.append(event_file)
    return input_devices


def find_keyboard_devices():
    """Find keyboard devices"""
    return find_input_devices(False)


class KeyButton:
    """Single key button widget - drawn using Canvas"""
    def __init__(self, parent, key_name, row, col, config, hidden=False):
        self.key_name = key_name
        self.is_pressed = False
        self.config = config
        self.animation_id = None
        self.transition_start = 0
        colors = config['colors']
        kb = config['keyboard']

        if key_name == 'Mouse Left':
            width = int(kb['key_width'] * 1.5)
        elif key_name == 'Mouse Right':
            width = int(kb['key_width'] * 1.5)
        elif key_name.startswith('Mouse '):
            width = kb['key_width'] * 2
        elif key_name in ['Backspace', 'Enter', 'Shift', 'CapsLock']:
            width = kb['key_width'] * 2
        elif key_name == 'Space':
            width = kb['key_width'] * 5
        elif key_name == 'Tab':
            width = int(kb['key_width'] * 1.5)
        else:
            width = kb['key_width']

        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=kb['key_height'],
            bg=colors['background'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(row=row, column=col, padx=kb['key_padding'], pady=kb['key_padding'])

        # If hidden, start with transparent colors (same as background)
        if hidden:
            self.bg_rect = create_rounded_rect(
                self.canvas,
                1, 1, width - 1, kb['key_height'] - 1,
                kb['key_radius'],
                fill=colors['background'],
                outline=colors['background'],
                width=1
            )
            self.text = self.canvas.create_text(
                width // 2,
                kb['key_height'] // 2,
                text='LMB' if key_name == 'Mouse Left' else 'RMB' if key_name == 'Mouse Right' else key_name,
                fill=colors['background'],
                font=('Noto Sans', kb['font_size'], 'bold')
            )
        else:
            self.bg_rect = create_rounded_rect(
                self.canvas,
                1, 1, width - 1, kb['key_height'] - 1,
                kb['key_radius'],
                fill=colors['background'],
                outline=colors['key_border'],
                width=1
            )
            self.text = self.canvas.create_text(
                width // 2,
                kb['key_height'] // 2,
                text='LMB' if key_name == 'Mouse Left' else 'RMB' if key_name == 'Mouse Right' else key_name,
                fill=colors['key_idle'],
                font=('Noto Sans', kb['font_size'], 'bold')
            )
        

        
    def press(self):
        """Press key"""
        if self.is_pressed:
            return
        self.is_pressed = True
        self.transition_start = time.time()
        self._animate_press()
        
    def release(self):
        """Release key"""
        if not self.is_pressed:
            return
        self.is_pressed = False
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
        colors = self.config['colors']
        self.canvas.itemconfig(self.bg_rect, fill=colors['background'], outline=colors['key_border'])
        self.canvas.itemconfig(self.text, fill=colors['key_idle'])
        
    def _animate_press(self):
        """Press animation - 0.2s transition"""
        if not self.is_pressed:
            return
            
        colors = self.config['colors']
        elapsed = time.time() - self.transition_start
        progress = min(elapsed / 0.2, 1.0)
        
        bg_color = self._interpolate_color(colors['background'], colors['key_active'], progress)
        text_color = self._interpolate_color(colors['key_idle'], colors['key_text'], progress)
        border_color = self._interpolate_color(colors['key_border'], colors['key_active'], progress)
        
        self.canvas.itemconfig(self.bg_rect, fill=bg_color, outline=border_color)
        self.canvas.itemconfig(self.text, fill=text_color)
        
        if progress < 1.0:
            self.animation_id = self.canvas.after(16, self._animate_press)

    def animate_entrance(self, delay, duration=0.5):
        """Entrance animation - fade in from transparent"""
        # Store animation parameters
        self._entrance_duration = duration
        self._entrance_delay = delay

        def start_animation():
            self._entrance_start_time = time.time()
            self._animate_entrance_frame()

        self.canvas.after(int(delay * 1000), start_animation)

    def _animate_entrance_frame(self):
        """Animate a single frame of entrance"""
        colors = self.config['colors']
        elapsed = time.time() - self._entrance_start_time
        progress = min(elapsed / self._entrance_duration, 1.0)

        # Easing function: ease-out cubic (smooth deceleration)
        ease_progress = 1 - (1 - progress) ** 3

        # Fade in effect
        alpha = ease_progress

        # Interpolate colors
        bg_r, bg_g, bg_b = KeyButton.hex_to_rgb_static(colors['background'])
        text_r, text_g, text_b = KeyButton.hex_to_rgb_static(colors['key_idle'])
        border_r, border_g, border_b = KeyButton.hex_to_rgb_static(colors['key_border'])

        # Fade in: text and border from background color to target color
        faded_text = '#{:02x}{:02x}{:02x}'.format(
            int(text_r * alpha + bg_r * (1 - alpha)),
            int(text_g * alpha + bg_g * (1 - alpha)),
            int(text_b * alpha + bg_b * (1 - alpha))
        )
        faded_border = '#{:02x}{:02x}{:02x}'.format(
            int(border_r * alpha + bg_r * (1 - alpha)),
            int(border_g * alpha + bg_g * (1 - alpha)),
            int(border_b * alpha + bg_b * (1 - alpha))
        )

        self.canvas.itemconfig(self.bg_rect, fill=colors['background'], outline=faded_border)
        self.canvas.itemconfig(self.text, fill=faded_text)

        if progress < 1.0:
            self.canvas.after(16, self._animate_entrance_frame)
        else:
            # Ensure final state
            self.canvas.itemconfig(self.bg_rect, fill=colors['background'], outline=colors['key_border'])
            self.canvas.itemconfig(self.text, fill=colors['key_idle'])
        
    def _interpolate_color(self, color1, color2, factor):
        """Interpolate between two colors"""
        r1, g1, b1 = self.hex_to_rgb(color1)
        r2, g2, b2 = self.hex_to_rgb(color2)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def hex_to_rgb(self, color):
        """Hexadecimal color to RGB"""
        return KeyButton.hex_to_rgb_static(color)

    @staticmethod
    def hex_to_rgb_static(color):
        """Hexadecimal color to RGB (static)"""
        color = color.lstrip('#')
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def create_default_config():
    """Create a deep copy of default config"""
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


class ModernSwitch(tk.Canvas):
    """Modern toggle switch widget"""
    def __init__(self, parent, variable, command=None, **kwargs):
        self.variable = variable
        self.command = command
        self.width = kwargs.pop('width', 44)
        self.height = kwargs.pop('height', 24)
        super().__init__(parent, width=self.width, height=self.height, 
                        bg='#1a1a2e', highlightthickness=0, **kwargs)
        
        self.bg_color_off = '#3a3a5c'
        self.bg_color_on = '#e94560'
        self.knob_color = '#ffffff'
        
        self.bind('<Button-1>', self._toggle)
        self.variable.trace_add('write', lambda *args: self._update())
        self._update()
    
    def _toggle(self, event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()
    
    def _update(self):
        self.delete('all')
        is_on = self.variable.get()
        
        # Draw background with rounded corners
        radius = self.height // 2
        bg_color = self.bg_color_on if is_on else self.bg_color_off
        
        # Create rounded rectangle
        points = rounded_rectangle_points(2, 2, self.width-2, self.height-2, radius)
        self.create_polygon(points, smooth=True, fill=bg_color, outline='')
        
        # Draw knob
        knob_x = self.width - radius - 2 if is_on else radius + 2
        self.create_oval(knob_x - radius + 4, 4, knob_x + radius - 4, self.height - 4,
                        fill=self.knob_color, outline='')


class ModernSlider(tk.Canvas):
    """Modern slider widget with gradient track"""
    def __init__(self, parent, variable, from_=0, to=1, command=None, **kwargs):
        self.variable = variable
        self.from_ = from_
        self.to = to
        self.command = command
        self.width = kwargs.pop('width', 200)
        self.height = kwargs.pop('height', 24)
        super().__init__(parent, width=self.width, height=self.height,
                        bg='#1a1a2e', highlightthickness=0, **kwargs)
        
        self.track_color = '#3a3a5c'
        self.fill_color = '#e94560'
        self.knob_color = '#ffffff'
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.variable.trace_add('write', lambda *args: self._update())
        self._update()
    
    def _get_value_from_x(self, x):
        ratio = max(0, min(1, (x - 10) / (self.width - 20)))
        return self.from_ + ratio * (self.to - self.from_)
    
    def _on_click(self, event):
        value = self._get_value_from_x(event.x)
        self.variable.set(round(value, 2))
        if self.command:
            self.command()
    
    def _on_drag(self, event):
        self._on_click(event)
    
    def _update(self):
        self.delete('all')
        value = self.variable.get()
        ratio = (value - self.from_) / (self.to - self.from_)
        fill_width = 10 + ratio * (self.width - 20)
        
        # Draw track background
        self.create_line(10, self.height//2, self.width-10, self.height//2,
                        fill=self.track_color, width=4, capstyle='round')
        
        # Draw filled portion
        if ratio > 0:
            self.create_line(10, self.height//2, fill_width, self.height//2,
                            fill=self.fill_color, width=4, capstyle='round')
        
        # Draw knob
        self.create_oval(fill_width-6, self.height//2-6, fill_width+6, self.height//2+6,
                        fill=self.knob_color, outline='#e94560', width=2)


class ConfigDialog:
    """Modern glassmorphism configuration editor dialog"""
    
    # Modern color scheme
    BG_DARK = '#0d0d1a'
    BG_CARD = '#16162a'
    BG_CARD_HOVER = '#1e1e3a'
    ACCENT_PRIMARY = '#e94560'
    ACCENT_SECONDARY = '#533483'
    ACCENT_GLOW = '#ff6b6b'
    TEXT_PRIMARY = '#ffffff'
    TEXT_SECONDARY = '#a0a0b8'
    BORDER_COLOR = '#2a2a4a'
    
    def __init__(self, parent_app):
        self.app = parent_app
        self.config = create_default_config()
        for section in self.app.config:
            if isinstance(self.app.config[section], dict):
                self.config[section].update(self.app.config[section])
            else:
                self.config[section] = self.app.config[section]

        self.dialog = tk.Toplevel(self.app.root)
        self.dialog.title("Settings")
        self.dialog.geometry("720x600")
        self.dialog.configure(bg=self.BG_DARK)
        self.dialog.resizable(True, True)
        self.dialog.transient(self.app.root)
        self.app.config_dialog_open = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 720) // 2
        y = (self.dialog.winfo_screenheight() - 600) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.color_widgets = {}
        self.tabs = {}
        self.current_tab = None
        self._build_ui()

    def _build_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.dialog, bg=self.BG_DARK)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_frame = tk.Frame(main_container, bg=self.BG_DARK)
        title_frame.pack(fill='x', pady=(0, 20))
        tk.Label(title_frame, text="Settings", font=('Noto Sans', 24, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_DARK).pack(side='left')
        
        # Tab buttons frame - modern pill style
        tab_frame = tk.Frame(main_container, bg=self.BG_DARK)
        tab_frame.pack(fill='x', pady=(0, 15))
        
        self.tab_buttons = {}
        tab_names = ['Window', 'Colors', 'Keyboard', 'Extra', 'Layout']
        for i, name in enumerate(tab_names):
            btn = tk.Label(
                tab_frame,
                text=name,
                bg=self.BG_CARD,
                fg=self.TEXT_SECONDARY,
                font=('Noto Sans', 11),
                padx=20,
                pady=8,
                cursor='hand2'
            )
            btn.pack(side='left', padx=(0, 8))
            btn.bind('<Enter>', lambda e, b=btn: b.config(bg=self.BG_CARD_HOVER))
            btn.bind('<Leave>', lambda e, b=btn, n=name: b.config(
                bg=self.ACCENT_PRIMARY if self.current_tab == n else self.BG_CARD))
            btn.bind('<Button-1>', lambda e, n=name: self._switch_tab(n))
            self.tab_buttons[name] = btn
        
        # Content frame - card style
        self.content_frame = tk.Frame(main_container, bg=self.BG_CARD,
                                     highlightbackground=self.BORDER_COLOR,
                                     highlightthickness=1)
        self.content_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Build all tab contents
        self._build_window_content()
        self._build_colors_content()
        self._build_keyboard_content()
        self._build_extra_content()
        self._build_layout_content()
        
        # Show first tab
        self._switch_tab('Window')
        
        # Buttons frame - modern style
        btn_frame = tk.Frame(main_container, bg=self.BG_DARK)
        btn_frame.pack(fill='x')
        
        # Reset button - outlined style
        reset_btn = tk.Label(btn_frame, text="Reset to Default", 
                            bg=self.BG_DARK, fg=self.ACCENT_PRIMARY,
                            font=('Noto Sans', 11), padx=20, pady=10,
                            cursor='hand2', highlightbackground=self.ACCENT_PRIMARY,
                            highlightthickness=1)
        reset_btn.pack(side='left')
        reset_btn.bind('<Enter>', lambda e: reset_btn.config(bg=self.BG_CARD))
        reset_btn.bind('<Leave>', lambda e: reset_btn.config(bg=self.BG_DARK))
        reset_btn.bind('<Button-1>', lambda e: self._reset())
        
        # Cancel button
        cancel_btn = tk.Label(btn_frame, text="Cancel",
                             bg=self.BG_DARK, fg=self.TEXT_SECONDARY,
                             font=('Noto Sans', 11), padx=20, pady=10,
                             cursor='hand2')
        cancel_btn.pack(side='right', padx=(10, 0))
        cancel_btn.bind('<Enter>', lambda e: cancel_btn.config(fg=self.TEXT_PRIMARY))
        cancel_btn.bind('<Leave>', lambda e: cancel_btn.config(fg=self.TEXT_SECONDARY))
        cancel_btn.bind('<Button-1>', lambda e: self._on_close())
        
        # Save button - primary style
        save_btn = tk.Label(btn_frame, text="Save Changes",
                           bg=self.ACCENT_PRIMARY, fg=self.TEXT_PRIMARY,
                           font=('Noto Sans', 11, 'bold'), padx=25, pady=10,
                           cursor='hand2')
        save_btn.pack(side='right', padx=(10, 0))
        save_btn.bind('<Enter>', lambda e: save_btn.config(bg=self.ACCENT_GLOW))
        save_btn.bind('<Leave>', lambda e: save_btn.config(bg=self.ACCENT_PRIMARY))
        save_btn.bind('<Button-1>', lambda e: self._save())

    def _switch_tab(self, name):
        """Switch to specified tab with animation"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()
        # Show selected tab
        self.tabs[name].pack(fill='both', expand=True, padx=20, pady=20)
        self.current_tab = name
        # Update button colors
        for tab_name, btn in self.tab_buttons.items():
            if tab_name == name:
                btn.config(bg=self.ACCENT_PRIMARY, fg=self.TEXT_PRIMARY)
            else:
                btn.config(bg=self.BG_CARD, fg=self.TEXT_SECONDARY)

    def _build_window_content(self):
        """Build modern window settings tab"""
        frame = tk.Frame(self.content_frame, bg=self.BG_CARD)
        self.tabs['Window'] = frame
        
        # Section title
        tk.Label(frame, text="Window Appearance", font=('Noto Sans', 16, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 20))
        
        # Settings container
        settings_container = tk.Frame(frame, bg=self.BG_CARD)
        settings_container.pack(fill='x')
        
        # Alpha slider
        self._create_setting_row(settings_container, "Transparency", 0)
        self.alpha_var = tk.DoubleVar(value=self.config['window']['alpha'])
        alpha_slider = ModernSlider(settings_container, self.alpha_var, from_=0.1, to=1.0)
        alpha_slider.pack(fill='x', pady=(5, 15))
        
        # Value label
        alpha_value_label = tk.Label(settings_container, 
                                     text=f"{self.alpha_var.get():.0%}",
                                     fg=self.TEXT_SECONDARY, bg=self.BG_CARD,
                                     font=('Noto Sans', 10))
        alpha_value_label.pack(anchor='e')
        self.alpha_var.trace_add('write', 
            lambda *a: alpha_value_label.config(text=f"{self.alpha_var.get():.0%}"))
        
        # Divider
        self._create_divider(settings_container)
        
        # Toggle switches section
        toggles_frame = tk.Frame(settings_container, bg=self.BG_CARD)
        toggles_frame.pack(fill='x', pady=10)
        
        # Always on top toggle
        self.always_on_top_var = tk.BooleanVar(value=self.config['window']['always_on_top'])
        self._create_toggle_row(toggles_frame, "Always on top", self.always_on_top_var, 0)
        
        # Frameless toggle
        self.frameless_var = tk.BooleanVar(value=self.config['window'].get('frameless', True))
        self._create_toggle_row(toggles_frame, "Frameless window", self.frameless_var, 1)
        
        # Divider
        self._create_divider(settings_container)
        
        # Corner radius slider
        self._create_setting_row(settings_container, "Corner Radius", 2)
        self.corner_radius_var = tk.IntVar(value=self.config['window'].get('corner_radius', 14))
        radius_slider = ModernSlider(settings_container, self.corner_radius_var, from_=0, to=50)
        radius_slider.pack(fill='x', pady=(5, 15))
        
        # Value label
        radius_value_label = tk.Label(settings_container,
                                      text=f"{self.corner_radius_var.get()}px",
                                      fg=self.TEXT_SECONDARY, bg=self.BG_CARD,
                                      font=('Noto Sans', 10))
        radius_value_label.pack(anchor='e')
        self.corner_radius_var.trace_add('write',
            lambda *a: radius_value_label.config(text=f"{self.corner_radius_var.get()}px"))
    
    def _create_setting_row(self, parent, label_text, row):
        """Create a setting label row"""
        row_frame = tk.Frame(parent, bg=self.BG_CARD)
        row_frame.pack(fill='x', pady=(15, 5))
        tk.Label(row_frame, text=label_text, font=('Noto Sans', 13),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(side='left')
    
    def _create_toggle_row(self, parent, label_text, variable, row):
        """Create a modern toggle switch row"""
        row_frame = tk.Frame(parent, bg=self.BG_CARD)
        row_frame.pack(fill='x', pady=8)
        
        tk.Label(row_frame, text=label_text, font=('Noto Sans', 12),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(side='left')
        
        ModernSwitch(row_frame, variable).pack(side='right')
    
    def _create_divider(self, parent):
        """Create a horizontal divider line"""
        divider = tk.Frame(parent, height=1, bg=self.BORDER_COLOR)
        divider.pack(fill='x', pady=10)

    def _build_colors_content(self):
        """Build modern colors settings tab with color cards"""
        # Create main container with scrollbar
        container = tk.Frame(self.content_frame, bg=self.BG_CARD)
        self.tabs['Colors'] = container
        
        # Section title
        tk.Label(container, text="Color Scheme", font=('Noto Sans', 16, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 20))
        
        # Create scrollable canvas for colors
        canvas_frame = tk.Frame(container, bg=self.BG_CARD)
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, bg=self.BG_CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.BG_CARD)
        
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas_window = canvas.create_window((0, 0), window=inner, anchor='nw', width=640)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        canvas.bind_all('<MouseWheel>', on_mousewheel)
        
        colors = self.config['colors']
        color_groups = {
            'Window': ['background', 'border', 'title_bar'],
            'Text': ['text', 'text_glow'],
            'Keys': ['key_idle', 'key_active', 'key_text', 'key_border'],
            'UI Elements': ['status_online', 'close_button', 'close_button_hover', 'mouse_direction_trace']
        }
        
        color_labels = {
            'background': 'Background', 'border': 'Border', 'title_bar': 'Title Bar',
            'text': 'Title Text', 'text_glow': 'Text Glow', 'key_idle': 'Key Idle',
            'key_active': 'Key Active', 'key_text': 'Key Text', 'key_border': 'Key Border',
            'status_online': 'Status Online', 'close_button': 'Close Button',
            'close_button_hover': 'Close Hover', 'mouse_direction_trace': 'Mouse Trace'
        }
        
        self.color_widgets = {}
        
        for group_name, group_colors in color_groups.items():
            # Group title
            group_frame = tk.Frame(inner, bg=self.BG_CARD)
            group_frame.pack(fill='x', pady=(15, 10), anchor='w')
            
            tk.Label(group_frame, text=group_name, font=('Noto Sans', 14, 'bold'),
                    fg=self.ACCENT_PRIMARY, bg=self.BG_CARD).pack(anchor='w')
            
            # Color cards grid
            cards_frame = tk.Frame(inner, bg=self.BG_CARD)
            cards_frame.pack(fill='x', pady=5)
            
            for idx, key in enumerate(group_colors):
                if key not in color_labels:
                    continue
                    
                # Color card
                card = tk.Frame(cards_frame, bg=self.BG_CARD_HOVER,
                               highlightbackground=self.BORDER_COLOR,
                               highlightthickness=1)
                card.grid(row=idx//2, column=idx%2, padx=5, pady=5, sticky='ew')
                cards_frame.grid_columnconfigure(0, weight=1)
                cards_frame.grid_columnconfigure(1, weight=1)
                
                # Color preview circle
                var = tk.StringVar(value=colors.get(key, '#000000'))
                preview_canvas = tk.Canvas(card, width=40, height=40, 
                                          bg=self.BG_CARD_HOVER, highlightthickness=0)
                preview_canvas.pack(side='left', padx=10, pady=10)
                
                color_val = colors.get(key, '#000000')
                preview_circle = preview_canvas.create_oval(4, 4, 36, 36, 
                                                           fill=color_val, outline='')
                
                # Label and hex value
                info_frame = tk.Frame(card, bg=self.BG_CARD_HOVER)
                info_frame.pack(side='left', fill='y', expand=True, pady=10)
                
                tk.Label(info_frame, text=color_labels[key], font=('Noto Sans', 11),
                        fg=self.TEXT_PRIMARY, bg=self.BG_CARD_HOVER).pack(anchor='w')
                
                hex_label = tk.Label(info_frame, text=color_val.upper(), 
                                    font=('Noto Sans', 10, 'bold'),
                                    fg=self.TEXT_SECONDARY, bg=self.BG_CARD_HOVER)
                hex_label.pack(anchor='w')
                
                # Edit button
                edit_btn = tk.Label(card, text="Edit", font=('Noto Sans', 10),
                                   fg=self.ACCENT_PRIMARY, bg=self.BG_CARD_HOVER,
                                   cursor='hand2', padx=15, pady=5)
                edit_btn.pack(side='right', padx=10)
                edit_btn.bind('<Enter>', lambda e, b=edit_btn: b.config(fg=self.ACCENT_GLOW))
                edit_btn.bind('<Leave>', lambda e, b=edit_btn: b.config(fg=self.ACCENT_PRIMARY))
                edit_btn.bind('<Button-1>', lambda e, v=var, p=preview_canvas, c=preview_circle, h=hex_label: 
                             self._pick_color_modern(v, p, c, h))
                
                self.color_widgets[key] = var
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _pick_color_modern(self, var, preview_canvas, preview_circle, hex_label):
        """Modern color picker with live preview"""
        color = colorchooser.askcolor(color=var.get(), parent=self.dialog,
                                     title="Choose Color")
        if color and color[1]:
            var.set(color[1])
            preview_canvas.itemconfig(preview_circle, fill=color[1])
            hex_label.config(text=color[1].upper())

    def _build_keyboard_content(self):
        """Build modern keyboard settings tab"""
        frame = tk.Frame(self.content_frame, bg=self.BG_CARD)
        self.tabs['Keyboard'] = frame

        # Section title
        tk.Label(frame, text="Keyboard Layout", font=('Noto Sans', 16, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 20))

        kb = self.config['keyboard']
        fields = [
            ('key_width', 'Key Width', 10, 100, 'px'),
            ('key_height', 'Key Height', 10, 100, 'px'),
            ('key_padding', 'Key Padding', 0, 20, 'px'),
            ('key_radius', 'Corner Radius', 0, 30, 'px'),
            ('font_size', 'Font Size', 6, 24, 'pt'),
        ]
        self.kb_vars = {}

        # Create cards for each setting
        for idx, (key, label, lo, hi, unit) in enumerate(fields):
            card = tk.Frame(frame, bg=self.BG_CARD_HOVER,
                           highlightbackground=self.BORDER_COLOR,
                           highlightthickness=1)
            card.pack(fill='x', pady=8)

            # Label row
            label_frame = tk.Frame(card, bg=self.BG_CARD_HOVER)
            label_frame.pack(fill='x', padx=15, pady=(10, 5))

            tk.Label(label_frame, text=label, font=('Noto Sans', 12),
                    fg=self.TEXT_PRIMARY, bg=self.BG_CARD_HOVER).pack(side='left')

            var = tk.IntVar(value=kb.get(key, 42))
            value_label = tk.Label(label_frame, text=f"{var.get()}{unit}",
                                  font=('Noto Sans', 11, 'bold'),
                                  fg=self.ACCENT_PRIMARY, bg=self.BG_CARD_HOVER)
            value_label.pack(side='right')

            # Slider
            slider = ModernSlider(card, var, from_=lo, to=hi, width=560)
            slider.pack(fill='x', padx=15, pady=(0, 15))

            # Update value label on change
            var.trace_add('write', lambda *a, v=var, l=value_label, u=unit: 
                         l.config(text=f"{int(v.get())}{u}"))

            self.kb_vars[key] = var

    def _build_extra_content(self):
        """Build modern extra settings tab"""
        frame = tk.Frame(self.content_frame, bg=self.BG_CARD)
        self.tabs['Extra'] = frame

        # Section title
        tk.Label(frame, text="Extra Features", font=('Noto Sans', 16, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 20))

        extra = self.config.get('extra_display', {})

        # Features section
        features_frame = tk.Frame(frame, bg=self.BG_CARD)
        features_frame.pack(fill='x', pady=10)

        tk.Label(features_frame, text="Display Options", font=('Noto Sans', 14, 'bold'),
                fg=self.ACCENT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 10))

        # Toggle options
        self.show_mouse_var = tk.BooleanVar(value=extra.get('show_mouse', False))
        self.show_cps_var = tk.BooleanVar(value=extra.get('show_cps', False))
        self.show_mouse_direction_var = tk.BooleanVar(value=extra.get('show_mouse_direction', False))
        self.show_mouse_trace_var = tk.BooleanVar(value=extra.get('show_mouse_trace', True))

        toggles = [
            ("Show mouse buttons", self.show_mouse_var, "Display left and right mouse buttons"),
            ("Show CPS counter", self.show_cps_var, "Display clicks per second"),
            ("Show direction chart", self.show_mouse_direction_var, "Visualize mouse movement direction"),
            ("Show mouse trace", self.show_mouse_trace_var, "Show mouse movement trail"),
        ]

        for label, var, desc in toggles:
            self._create_feature_toggle(features_frame, label, var, desc)

        # Divider
        self._create_divider(frame)

        # Advanced settings
        advanced_frame = tk.Frame(frame, bg=self.BG_CARD)
        advanced_frame.pack(fill='x', pady=10)

        tk.Label(advanced_frame, text="Advanced", font=('Noto Sans', 14, 'bold'),
                fg=self.ACCENT_PRIMARY, bg=self.BG_CARD).pack(anchor='w', pady=(0, 10))

        # Direction decay slider
        self.mouse_direction_decay_var = tk.DoubleVar(value=extra.get('mouse_direction_decay', 1.25))

        decay_card = tk.Frame(advanced_frame, bg=self.BG_CARD_HOVER,
                             highlightbackground=self.BORDER_COLOR,
                             highlightthickness=1)
        decay_card.pack(fill='x', pady=8)

        label_frame = tk.Frame(decay_card, bg=self.BG_CARD_HOVER)
        label_frame.pack(fill='x', padx=15, pady=(10, 5))

        tk.Label(label_frame, text="Direction Decay", font=('Noto Sans', 12),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD_HOVER).pack(side='left')

        decay_value_label = tk.Label(label_frame, text=f"{self.mouse_direction_decay_var.get():.2f}x",
                                    font=('Noto Sans', 11, 'bold'),
                                    fg=self.ACCENT_PRIMARY, bg=self.BG_CARD_HOVER)
        decay_value_label.pack(side='right')

        decay_slider = ModernSlider(decay_card, self.mouse_direction_decay_var, 
                                   from_=1.01, to=5.0, width=560)
        decay_slider.pack(fill='x', padx=15, pady=(0, 10))

        self.mouse_direction_decay_var.trace_add('write',
            lambda *a: decay_value_label.config(text=f"{self.mouse_direction_decay_var.get():.2f}x"))

        # Description
        tk.Label(advanced_frame, 
                text="Higher decay values create stronger return-to-center damping for the direction indicator.",
                font=('Noto Sans', 10), fg=self.TEXT_SECONDARY, bg=self.BG_CARD,
                wraplength=600).pack(anchor='w', pady=(10, 0))

    def _create_feature_toggle(self, parent, label, var, description):
        """Create a feature toggle row with description"""
        card = tk.Frame(parent, bg=self.BG_CARD_HOVER,
                       highlightbackground=self.BORDER_COLOR,
                       highlightthickness=1)
        card.pack(fill='x', pady=6)

        # Main row with toggle
        row = tk.Frame(card, bg=self.BG_CARD_HOVER)
        row.pack(fill='x', padx=15, pady=12)

        # Text info
        info_frame = tk.Frame(row, bg=self.BG_CARD_HOVER)
        info_frame.pack(side='left', fill='y')

        tk.Label(info_frame, text=label, font=('Noto Sans', 12),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD_HOVER).pack(anchor='w')

        tk.Label(info_frame, text=description, font=('Noto Sans', 10),
                fg=self.TEXT_SECONDARY, bg=self.BG_CARD_HOVER).pack(anchor='w')

        # Toggle switch
        ModernSwitch(row, var).pack(side='right')

    def _build_layout_content(self):
        """Build modern layout editor tab"""
        frame = tk.Frame(self.content_frame, bg=self.BG_CARD)
        self.tabs['Layout'] = frame

        # Section title with icon hint
        header_frame = tk.Frame(frame, bg=self.BG_CARD)
        header_frame.pack(fill='x', pady=(0, 15))

        tk.Label(header_frame, text="Keyboard Layout Editor", font=('Noto Sans', 16, 'bold'),
                fg=self.TEXT_PRIMARY, bg=self.BG_CARD).pack(side='left')

        # Help button
        help_btn = tk.Label(header_frame, text="?", font=('Noto Sans', 12, 'bold'),
                           fg=self.ACCENT_PRIMARY, bg=self.BG_CARD_HOVER,
                           cursor='hand2', padx=10, pady=2)
        help_btn.pack(side='right')
        help_btn.bind('<Enter>', lambda e: help_btn.config(fg=self.ACCENT_GLOW))
        help_btn.bind('<Leave>', lambda e: help_btn.config(fg=self.ACCENT_PRIMARY))
        help_btn.bind('<Button-1>', lambda e: self._show_layout_help())

        # Editor card
        editor_card = tk.Frame(frame, bg=self.BG_CARD_HOVER,
                              highlightbackground=self.BORDER_COLOR,
                              highlightthickness=1)
        editor_card.pack(fill='both', expand=True, pady=10)

        # Toolbar
        toolbar = tk.Frame(editor_card, bg=self.BG_CARD_HOVER)
        toolbar.pack(fill='x', padx=10, pady=(10, 0))

        tk.Label(toolbar, text="JSON Format", font=('Noto Sans', 10),
                fg=self.TEXT_SECONDARY, bg=self.BG_CARD_HOVER).pack(side='left')

        # Format button
        format_btn = tk.Label(toolbar, text="Format", font=('Noto Sans', 10),
                             fg=self.ACCENT_PRIMARY, bg=self.BG_CARD_HOVER,
                             cursor='hand2', padx=10)
        format_btn.pack(side='right')
        format_btn.bind('<Enter>', lambda e: format_btn.config(fg=self.ACCENT_GLOW))
        format_btn.bind('<Leave>', lambda e: format_btn.config(fg=self.ACCENT_PRIMARY))
        format_btn.bind('<Button-1>', lambda e: self._format_layout_json())

        # Text editor
        text_frame = tk.Frame(editor_card, bg=self.BG_CARD_HOVER)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Line numbers canvas
        self.line_numbers = tk.Canvas(text_frame, width=40, bg=self.BG_CARD,
                                     highlightthickness=0)
        self.line_numbers.pack(side='left', fill='y')

        # Text widget with custom styling
        self.layout_text = tk.Text(text_frame, bg=self.BG_DARK, fg=self.TEXT_PRIMARY,
                                   insertbackground=self.ACCENT_PRIMARY,
                                   font=('JetBrains Mono', 11), wrap='none',
                                   padx=10, pady=10, relief='flat',
                                   selectbackground=self.ACCENT_SECONDARY,
                                   selectforeground=self.TEXT_PRIMARY)
        self.layout_text.pack(side='left', fill='both', expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(text_frame, bg=self.BG_CARD, troughcolor=self.BG_CARD,
                                activebackground=self.ACCENT_PRIMARY)
        scrollbar.pack(side='right', fill='y')
        self.layout_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.layout_text.yview)

        # Insert initial content
        layout_json = json.dumps(self.config['keyboard']['layout'], indent=2, ensure_ascii=False)
        self.layout_text.insert('1.0', layout_json)

        # Update line numbers
        self._update_line_numbers()
        self.layout_text.bind('<KeyRelease>', lambda e: self._update_line_numbers())
        self.layout_text.bind('<Scroll>', lambda e: self._update_line_numbers())

        # Info footer
        footer_frame = tk.Frame(frame, bg=self.BG_CARD)
        footer_frame.pack(fill='x', pady=(10, 0))

        tk.Label(footer_frame,
                text="Tip: Each row is a JSON array of key names. Use KEY_MAP names like 'Esc', 'Q', 'Space', 'Shift'.",
                font=('Noto Sans', 10), fg=self.TEXT_SECONDARY, bg=self.BG_CARD,
                wraplength=600).pack(anchor='w')

    def _update_line_numbers(self):
        """Update line number display"""
        self.line_numbers.delete('all')
        text = self.layout_text.get('1.0', 'end')
        lines = text.split('\n')
        for i, _ in enumerate(lines[:-1], 1):
            self.line_numbers.create_text(25, i * 20 - 10, text=str(i),
                                         fill=self.TEXT_SECONDARY, font=('JetBrains Mono', 10),
                                         anchor='e')

    def _format_layout_json(self):
        """Format the layout JSON"""
        try:
            content = self.layout_text.get('1.0', 'end')
            layout = json.loads(content)
            formatted = json.dumps(layout, indent=2, ensure_ascii=False)
            self.layout_text.delete('1.0', 'end')
            self.layout_text.insert('1.0', formatted)
            self._update_line_numbers()
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"Failed to parse JSON:\n{e}", parent=self.dialog)

    def _show_layout_help(self):
        """Show layout editor help"""
        help_text = """Keyboard Layout Format:

Each row is a JSON array of key names.

Available keys:
- Letters: A-Z
- Numbers: 0-9
- Function: F1-F12
- Special: Esc, Tab, Enter, Space, Backspace
- Modifiers: Ctrl, Shift, Alt, Super, CapsLock
- Navigation: Up, Down, Left, Right, Home, End, PageUp, PageDown
- Mouse: Mouse Left, Mouse Right, Mouse Middle

Example:
[
  ["Esc", "1", "2", "3"],
  ["Tab", "Q", "W", "E"],
  ["Ctrl", "A", "S", "D"]
]"""
        messagebox.showinfo("Layout Help", help_text, parent=self.dialog)

    def _on_close(self):
        self.app.config_dialog_open = False
        self.dialog.destroy()

    def _collect_config(self):
        cfg = create_default_config()
        cfg['window']['alpha'] = round(self.alpha_var.get(), 2)
        cfg['window']['always_on_top'] = self.always_on_top_var.get()
        cfg['window']['frameless'] = self.frameless_var.get()
        cfg['window']['corner_radius'] = self.corner_radius_var.get()
        for key, var in self.color_widgets.items():
            cfg['colors'][key] = var.get()
        for key, var in self.kb_vars.items():
            cfg['keyboard'][key] = var.get()
        cfg['extra_display']['show_mouse'] = self.show_mouse_var.get()
        cfg['extra_display']['show_cps'] = self.show_cps_var.get()
        cfg['extra_display']['show_mouse_direction'] = self.show_mouse_direction_var.get()
        cfg['extra_display']['show_mouse_trace'] = self.show_mouse_trace_var.get()
        cfg['extra_display']['mouse_direction_decay'] = round(self.mouse_direction_decay_var.get(), 2)
        # Parse layout from text editor
        try:
            layout_text = self.layout_text.get('1.0', 'end').strip()
            layout = json.loads(layout_text)
            if isinstance(layout, list):
                cfg['keyboard']['layout'] = layout
        except (json.JSONDecodeError, tk.TclError):
            cfg['keyboard']['layout'] = self.config['keyboard']['layout']
        return cfg

    def _apply(self):
        """Apply configuration without closing"""
        try:
            cfg = self._collect_config()
            save_config(cfg)
            self._show_notification("Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}", parent=self.dialog)

    def _save(self):
        """Save configuration and close"""
        try:
            cfg = self._collect_config()
            save_config(cfg)
            self._on_close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}", parent=self.dialog)

    def _reset(self):
        """Reset to default configuration"""
        if messagebox.askyesno("Reset Settings", 
                              "Reset all settings to default values?\n\nKeyboard layout will be preserved.",
                              icon='warning', parent=self.dialog):
            try:
                cfg = create_default_config()
                cfg['keyboard']['layout'] = self.config['keyboard']['layout']
                save_config(cfg)
                self._show_notification("Settings reset to default")
                self._on_close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset configuration:\n{e}", parent=self.dialog)

    def _show_notification(self, message):
        """Show a temporary notification"""
        notification = tk.Label(self.dialog, text=message, 
                               font=('Noto Sans', 11), fg=self.TEXT_PRIMARY,
                               bg=self.ACCENT_PRIMARY, padx=20, pady=10)
        notification.place(relx=0.5, rely=0.9, anchor='center')
        self.dialog.after(2000, notification.destroy)


class KeyDisplayApp:
    def __init__(self):
        self.config = load_config()
        colors = self.config['colors']
        
        self.root = tk.Tk()
        self.root.title("Keyboard Key Display")
        
        self.transparent_color = '#010203'
        self.root.geometry("1x1+0+0")
        self.root.configure(bg=self.transparent_color)
        
        try:
            self.root.attributes('-alpha', self.config['window']['alpha'])
            self.root.attributes('-transparentcolor', self.transparent_color)
        except Exception:
            pass  
        
        if self.config['window']['always_on_top']:
            self.root.attributes('-topmost', True)
        
        self.frameless = self.config['window'].get('frameless', True)
        self.root.overrideredirect(self.frameless)
        # Hide window initially to prevent flash, will show with fade-in animation
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind_all('<Control-q>', lambda event: self.on_closing())
        self.root.bind_all('<Control-F9>', lambda event: self.open_config_dialog())
        
        self.current_keys = set()
        self.mouse_window = None
        self.mouse_canvas = None
        self.mouse_border = None
        self.mouse_canvas_window = None
        self.mouse_frame = None
        self.mouse_buttons = {}
        self.left_click_timestamps = []
        self.right_click_timestamps = []
        self.mouse_direction_canvas = None
        self.mouse_direction_vector = [0, 0]
        self.mouse_trace_positions = deque(maxlen=20)
        self.mouse_direction_job = None
        self.cps_label = None
        self.cps_text = None
        self.cps_update_job = None
        self.key_buttons = {}
        self.running = True
        self.closed = False
        self.config_dialog_open = False
        self.listener_threads = []
        self.permission_denied = False
        self._drag_data = {'offset_x': 0, 'offset_y': 0, 'active': False}
        self._mouse_drag_data = {'offset_x': 0, 'offset_y': 0, 'active': False}
        self.title_bar_height = 30 if self.frameless else 0
        self.close_area_width = 48
        if self.frameless:
            self.root.bind_all('<ButtonPress-1>', self.handle_pointer_press)
            self.root.bind_all('<ButtonRelease-1>', self.handle_pointer_release)
            self.root.bind_all('<B1-Motion>', self.handle_pointer_motion)
        
        self.setup_ui()

        # Prepare everything before showing window
        self.root.update_idletasks()
        self.fit_window_to_content()
        self.setup_extra_display()

        # Start keyboard listener after UI is ready
        self.start_keyboard_listener()

        # Start window fade-in animation (this will deiconify the window)
        self._animate_window_entrance()
        
    def setup_ui(self):
        colors = self.config['colors']
        kb = self.config['keyboard']
        
        self.window_canvas = tk.Canvas(
            self.root,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )
        self.window_canvas.pack(fill='both', expand=True)
        self.window_border = self.window_canvas.create_rectangle(
            1, 1, 1, 1,
            outline=colors['border'],
            width=2,
            fill=colors['background']
        )

        self.main_frame = tk.Frame(self.window_canvas, bg=colors['background'])
        self.window_canvas_window = self.window_canvas.create_window(3, 3, window=self.main_frame, anchor='nw')
        main_frame = self.main_frame
        self.window_canvas.bind('<Configure>', self.on_window_canvas_configure)
        
        if self.frameless:
            title_frame = tk.Frame(main_frame, bg=colors['title_bar'], cursor='fleur', height=self.title_bar_height)
            title_frame.pack(fill='x')
            title_frame.pack_propagate(False)
            title_frame.bind('<Button-1>', self.start_drag)
            title_frame.bind('<B1-Motion>', self.on_drag)
            title_frame.bind('<ButtonRelease-1>', self.handle_pointer_release)

            title_label = tk.Label(
                title_frame,
                text="KEY DISPLAY",
                font=('Noto Sans', 10, 'bold'),
                fg=colors['text'],
                bg=colors['title_bar'],
                cursor='fleur'
            )
            title_label.pack(side='left', padx=10)
            title_label.bind('<Button-1>', self.start_drag)
            title_label.bind('<B1-Motion>', self.on_drag)
            title_label.bind('<ButtonRelease-1>', self.handle_pointer_release)

            self.status_label = tk.Label(
                title_frame,
                text="●",
                font=('Noto Sans', 8),
                fg=colors['status_online'],
                bg=colors['title_bar'],
                cursor='fleur'
            )
            self.status_label.pack(side='left')
            self.status_label.bind('<Button-1>', self.start_drag)
            self.status_label.bind('<B1-Motion>', self.on_drag)
            self.status_label.bind('<ButtonRelease-1>', self.handle_pointer_release)

            close_label = tk.Label(
                title_frame,
                text="✕",
                font=('Noto Sans', 12, 'bold'),
                fg=colors['close_button'],
                bg=colors['title_bar'],
                cursor='hand2',
                padx=10
            )
            close_label.pack(side='right', fill='y')
            close_label.bind('<Enter>', lambda e: close_label.config(fg=colors['close_button_hover']))
            close_label.bind('<Leave>', lambda e: close_label.config(fg=colors['close_button']))
            close_label.bind('<Button-1>', lambda e: self.on_closing())
        else:
            self.status_label = None
        
        self.keyboard_frame = tk.Frame(main_frame, bg=colors['background'])
        self.keyboard_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        for row_idx, row_keys in enumerate(kb['layout']):
            row_frame = tk.Frame(self.keyboard_frame, bg=colors['background'])
            # Only add bottom padding for non-last rows
            if row_idx < len(kb['layout']) - 1:
                row_frame.pack(fill='x', pady=(0, kb['key_padding']))
            else:
                row_frame.pack(fill='x')
            for col_idx, key_name in enumerate(row_keys):
                btn = KeyButton(row_frame, key_name, row_idx, col_idx, self.config, hidden=True)
                self.key_buttons[key_name] = btn

    def _start_entrance_animation(self):
        """Start wave entrance animation for all key buttons"""
        import random

        all_buttons = list(self.key_buttons.items())

        # Sort by row then column for wave effect
        kb_layout = self.config['keyboard']['layout']
        button_positions = {}
        for row_idx, row_keys in enumerate(kb_layout):
            for col_idx, key_name in enumerate(row_keys):
                button_positions[key_name] = (row_idx, col_idx)

        # Sort buttons by row + col for diagonal wave effect
        all_buttons.sort(key=lambda x: button_positions.get(x[0], (0, 0))[0] + button_positions.get(x[0], (0, 0))[1] * 0.5)

        for i, (key_name, btn) in enumerate(all_buttons):
            # Wave delay based on position
            row, col = button_positions.get(key_name, (0, 0))
            delay = (row * 0.08 + col * 0.03) + random.uniform(0, 0.05)

            btn.animate_entrance(delay, duration=0.35)

        # Animate mouse buttons if they exist
        if self.mouse_buttons:
            for i, (key_name, btn) in enumerate(self.mouse_buttons.items()):
                delay = 0.3 + i * 0.1  # Delay after keyboard animation
                btn.animate_entrance(delay, duration=0.35)

        # Animate CPS display if it exists
        if hasattr(self, 'cps_label') and self.cps_label:
            self._animate_cps_entrance(0.5)

        # Animate mouse direction canvas if it exists
        if hasattr(self, 'mouse_direction_canvas') and self.mouse_direction_canvas:
            self._animate_mouse_direction_entrance(0.2)

    def _animate_window_entrance(self):
        """Animate window fade-in from transparent to opaque"""
        # Show window and start with transparent alpha
        self.root.deiconify()
        self.root.attributes('-alpha', 0.0)
        self._window_entrance_start = time.time()
        self._animate_window_frame()

    def _animate_window_frame(self, duration=0.3):
        """Animate a single frame of window entrance"""
        elapsed = time.time() - self._window_entrance_start
        progress = min(elapsed / duration, 1.0)

        # Easing function: ease-out cubic
        ease_progress = 1 - (1 - progress) ** 3
        alpha = ease_progress

        self.root.attributes('-alpha', alpha)

        if progress < 1.0:
            self.root.after(16, lambda: self._animate_window_frame(duration))
        else:
            # Window fully visible, start button animations
            self._start_entrance_animation()
            # Also animate mouse window if it exists
            if self.mouse_window is not None:
                self._animate_mouse_window_entrance()

    def _animate_mouse_window_entrance(self, duration=0.3):
        """Animate mouse window fade-in"""
        if self.mouse_window is None:
            return
        # Show the window first
        self.mouse_window.deiconify()
        self._mouse_window_entrance_start = time.time()
        self._animate_mouse_window_frame(duration)

    def _animate_mouse_window_frame(self, duration):
        """Animate a single frame of mouse window entrance"""
        if self.mouse_window is None:
            return
        elapsed = time.time() - self._mouse_window_entrance_start
        progress = min(elapsed / duration, 1.0)

        # Easing function: ease-out cubic
        ease_progress = 1 - (1 - progress) ** 3
        alpha = ease_progress

        # Get final alpha from config
        final_alpha = self.config['window'].get('alpha', 0.95)
        current_alpha = alpha * final_alpha

        self.mouse_window.attributes('-alpha', current_alpha)

        if progress < 1.0:
            self.root.after(16, lambda: self._animate_mouse_window_frame(duration))

    def _animate_cps_entrance(self, delay, duration=0.4):
        """Animate CPS display entrance"""
        colors = self.config['colors']

        def animate():
            self._cps_entrance_start = time.time()
            self._animate_cps_frame(duration, colors)

        self.root.after(int(delay * 1000), animate)

    def _animate_cps_frame(self, duration, colors):
        """Animate a single frame of CPS entrance"""
        elapsed = time.time() - self._cps_entrance_start
        progress = min(elapsed / duration, 1.0)

        # Easing function: ease-out cubic
        ease_progress = 1 - (1 - progress) ** 3
        alpha = ease_progress

        # Interpolate colors
        bg_r, bg_g, bg_b = KeyButton.hex_to_rgb_static(colors['background'])
        text_r, text_g, text_b = KeyButton.hex_to_rgb_static(colors['key_idle'])
        border_r, border_g, border_b = KeyButton.hex_to_rgb_static(colors['key_border'])

        faded_text = '#{:02x}{:02x}{:02x}'.format(
            int(text_r * alpha + bg_r * (1 - alpha)),
            int(text_g * alpha + bg_g * (1 - alpha)),
            int(text_b * alpha + bg_b * (1 - alpha))
        )
        faded_border = '#{:02x}{:02x}{:02x}'.format(
            int(border_r * alpha + bg_r * (1 - alpha)),
            int(border_g * alpha + bg_g * (1 - alpha)),
            int(border_b * alpha + bg_b * (1 - alpha))
        )

        self.cps_label.itemconfig(self.cps_bg_rect, outline=faded_border)
        self.cps_label.itemconfig(self.cps_text, fill=faded_text)

        if progress < 1.0:
            self.root.after(16, lambda: self._animate_cps_frame(duration, colors))
        else:
            self.cps_label.itemconfig(self.cps_bg_rect, outline=colors['key_border'])
            self.cps_label.itemconfig(self.cps_text, fill=colors['key_idle'])

    def _animate_mouse_direction_entrance(self, delay, duration=0.4):
        """Animate mouse direction canvas entrance"""
        colors = self.config['colors']

        def animate():
            self._mouse_dir_entrance_start = time.time()
            self._animate_mouse_direction_frame(duration, colors)

        self.root.after(int(delay * 1000), animate)

    def _animate_mouse_direction_frame(self, duration, colors):
        """Animate a single frame of mouse direction entrance"""
        elapsed = time.time() - self._mouse_dir_entrance_start
        progress = min(elapsed / duration, 1.0)

        # Easing function: ease-out cubic
        ease_progress = 1 - (1 - progress) ** 3
        alpha = ease_progress

        # Interpolate colors
        bg_r, bg_g, bg_b = KeyButton.hex_to_rgb_static(colors['background'])
        border_r, border_g, border_b = KeyButton.hex_to_rgb_static(colors['key_border'])

        faded_border = '#{:02x}{:02x}{:02x}'.format(
            int(border_r * alpha + bg_r * (1 - alpha)),
            int(border_g * alpha + bg_g * (1 - alpha)),
            int(border_b * alpha + bg_b * (1 - alpha))
        )

        # Redraw chart with faded color
        self.draw_mouse_direction_chart(override_color=faded_border)

        if progress < 1.0:
            self.root.after(16, lambda: self._animate_mouse_direction_frame(duration, colors))
        else:
            # Redraw with final colors and start decay
            self.draw_mouse_direction_chart()
            self.schedule_mouse_direction_decay()

    def setup_extra_display(self):
        extra = self.config.get('extra_display', {})
        if not extra.get('show_mouse', False) and not extra.get('show_cps', False) and not extra.get('show_mouse_direction', False):
            return

        colors = self.config['colors']
        kb = self.config['keyboard']

        self.mouse_window = tk.Toplevel(self.root)
        self.mouse_window.title("Keyboard Key Display - Mouse")
        self.mouse_window.configure(bg=self.transparent_color)
        self.mouse_window.resizable(False, False)
        self.mouse_window.overrideredirect(self.frameless)
        # Hide initially to prevent flash
        self.mouse_window.withdraw()
        if self.config['window']['always_on_top']:
            self.mouse_window.attributes('-topmost', True)
        try:
            self.mouse_window.attributes('-alpha', 0.0)  # Start transparent for animation
            self.mouse_window.attributes('-transparentcolor', self.transparent_color)
        except Exception:
            pass

        mouse_canvas = tk.Canvas(
            self.mouse_window,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )
        mouse_canvas.pack(fill='both', expand=True)
        self.mouse_canvas = mouse_canvas
        self.mouse_border = mouse_canvas.create_rectangle(
            1, 1, 1, 1,
            outline=colors['border'],
            width=2,
            fill=colors['background']
        )

        self.mouse_frame = tk.Frame(mouse_canvas, bg=colors['background'])
        self.mouse_canvas_window = mouse_canvas.create_window(3, 3, window=self.mouse_frame, anchor='nw')

        def on_mouse_canvas_configure(event):
            mouse_canvas.coords(self.mouse_border, 1, 1, event.width - 2, event.height - 2)
            mouse_canvas.itemconfig(self.mouse_canvas_window, width=event.width - 6, height=event.height - 6)

        mouse_canvas.bind('<Configure>', on_mouse_canvas_configure)

        if extra.get('show_mouse_direction', False):
            self.mouse_direction_canvas = tk.Canvas(
                self.mouse_frame,
                width=90,
                height=90,
                bg=colors['background'],
                highlightthickness=0,
                bd=0
            )
            self.mouse_direction_canvas.grid(row=0, column=0, columnspan=2, padx=kb['key_padding'], pady=kb['key_padding'])
            # Store initial colors for animation
            self._mouse_direction_canvas_items = []
            self.draw_mouse_direction_chart()

        mouse_button_row = 1 if extra.get('show_mouse_direction', False) else 0
        if extra.get('show_mouse', False):
            for mouse_name in ['Mouse Left', 'Mouse Right']:
                btn = KeyButton(self.mouse_frame, mouse_name, mouse_button_row, len(self.mouse_buttons), self.config, hidden=True)
                self.mouse_buttons[mouse_name] = btn

        if extra.get('show_cps', False):
            cps_row = mouse_button_row + (1 if extra.get('show_mouse', False) else 0)
            self.cps_label = tk.Canvas(
                self.mouse_frame,
                width=max(int(kb['key_width'] * 3.2), 130),
                height=kb['key_height'],
                bg=colors['background'],
                highlightthickness=0,
                bd=0
            )
            self.cps_label.grid(row=cps_row, column=0, columnspan=max(1, len(self.mouse_buttons), 2), padx=kb['key_padding'], pady=kb['key_padding'])
            # Start with transparent/hidden colors
            self.cps_bg_rect = create_rounded_rect(
                self.cps_label,
                1, 1, max(int(kb['key_width'] * 3.2), 130) - 1, kb['key_height'] - 1, kb['key_radius'],
                fill=colors['background'],
                outline=colors['background'],  # Start hidden
                width=1
            )
            self.cps_text = self.cps_label.create_text(
                max(int(kb['key_width'] * 3.2), 130) // 2,
                kb['key_height'] // 2,
                text="L CPS: 0 | R CPS: 0",
                fill=colors['background'],  # Start hidden
                font=('Noto Sans', kb['font_size'], 'bold')
            )
            self.schedule_cps_update()

        self.mouse_window.update_idletasks()
        mouse_width = self.mouse_frame.winfo_reqwidth() + 6
        mouse_height = self.mouse_frame.winfo_reqheight() + 6

        # Restore saved mouse window position or place below main window
        saved_mouse_pos = self.config.get('window', {}).get('mouse_position', {})
        saved_mx = saved_mouse_pos.get('x')
        saved_my = saved_mouse_pos.get('y')

        if saved_mx is not None and saved_my is not None:
            # Validate position is within screen bounds
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            # Ensure window is at least partially visible
            if saved_mx < screen_width - 50 and saved_my < screen_height - 50 and saved_mx + mouse_width > 50 and saved_my + mouse_height > 50:
                x, y = saved_mx, saved_my
            else:
                x = self.root.winfo_x()
                y = self.root.winfo_y() + self.root.winfo_height() + 10
        else:
            x = self.root.winfo_x()
            y = self.root.winfo_y() + self.root.winfo_height() + 10

        self.mouse_window.geometry(f"{mouse_width}x{mouse_height}+{x}+{y}")
        mouse_canvas.config(width=mouse_width, height=mouse_height)

        if self.frameless:
            self.bind_mouse_window_drag()
                
    def bind_mouse_window_drag(self):
        for widget in [self.mouse_canvas, self.mouse_frame, self.mouse_direction_canvas, self.cps_label, *self.mouse_buttons.values()]:
            if widget is None:
                continue
            target = widget.canvas if isinstance(widget, KeyButton) else widget
            target.bind('<Button-1>', self.start_mouse_window_drag)
            target.bind('<B1-Motion>', self.on_mouse_window_drag)
            target.bind('<ButtonRelease-1>', self.stop_mouse_window_drag)

    def start_mouse_window_drag(self, event):
        if self.mouse_window is None:
            return
        self._mouse_drag_data['offset_x'] = event.x_root - self.mouse_window.winfo_rootx()
        self._mouse_drag_data['offset_y'] = event.y_root - self.mouse_window.winfo_rooty()
        self._mouse_drag_data['active'] = True

    def on_mouse_window_drag(self, event):
        if self.mouse_window is not None and self._mouse_drag_data['active']:
            x = event.x_root - self._mouse_drag_data['offset_x']
            y = event.y_root - self._mouse_drag_data['offset_y']
            self.mouse_window.geometry(f"+{x}+{y}")

    def stop_mouse_window_drag(self, event):
        self._mouse_drag_data['active'] = False
                
    def on_window_canvas_configure(self, event=None):
        self.window_canvas.coords(self.window_border, 1, 1, event.width - 2, event.height - 2)
        self.window_canvas.itemconfig(self.window_canvas_window, width=event.width - 6, height=event.height - 6)
                
    def fit_window_to_content(self):
        self.root.update_idletasks()

        # Use Tk's actual requested size to avoid clipping after padding/border changes
        window_width = self.main_frame.winfo_reqwidth() + 6
        window_height = self.main_frame.winfo_reqheight() + 6

        # Restore saved position or center on screen
        saved_pos = self.config.get('window', {}).get('position', {})
        saved_x = saved_pos.get('x')
        saved_y = saved_pos.get('y')

        if saved_x is not None and saved_y is not None:
            # Validate position is within screen bounds
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            # Ensure window is at least partially visible
            if saved_x < screen_width - 50 and saved_y < screen_height - 50 and saved_x + window_width > 50 and saved_y + window_height > 50:
                x, y = saved_x, saved_y
            else:
                # Center if saved position is off-screen
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
        else:
            # Center on first run
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window_canvas.config(width=window_width, height=window_height)
        
    def handle_pointer_press(self, event):
        """Handle mouse press for dragging window"""
        if not self.frameless:
            return

        # Don't start drag if clicking inside config dialog
        try:
            widget = event.widget
            while widget:
                if isinstance(widget, tk.Toplevel) and widget is not self.root and not (
                    self.mouse_window and widget is self.mouse_window
                ):
                    return
                widget = widget.master
        except Exception:
            pass

        pointer_x = event.x_root
        pointer_y = event.y_root
        rel_x = pointer_x - self.root.winfo_rootx()
        rel_y = pointer_y - self.root.winfo_rooty()

        if 0 <= rel_y <= self.title_bar_height and rel_x < self.root.winfo_width() - self.close_area_width:
            self._drag_data['offset_x'] = rel_x
            self._drag_data['offset_y'] = rel_y
            self._drag_data['active'] = True

    def handle_pointer_release(self, event):
        """Handle mouse release"""
        self._drag_data['active'] = False

    def handle_pointer_motion(self, event):
        """Handle mouse motion for dragging window"""
        if self._drag_data['active'] and self.frameless:
            x = event.x_root - self._drag_data['offset_x']
            y = event.y_root - self._drag_data['offset_y']
            self.root.geometry(f"+{x}+{y}")

    def start_drag(self, event):
        """Start dragging from title bar"""
        if not self.frameless:
            return
        self._drag_data['offset_x'] = event.x_root - self.root.winfo_rootx()
        self._drag_data['offset_y'] = event.y_root - self.root.winfo_rooty()
        self._drag_data['active'] = True

    def on_drag(self, event):
        """Continue dragging from title bar"""
        if self._drag_data['active'] and self.frameless:
            x = event.x_root - self._drag_data['offset_x']
            y = event.y_root - self._drag_data['offset_y']
            self.root.geometry(f"+{x}+{y}")

    def start_keyboard_listener(self):
        if os.environ.get('KEY_DISPLAY_DEBUG_PERMISSION_DENIED') == '1':
            self.set_permission_warning()
            return

        devices = find_input_devices(
            self.config.get('extra_display', {}).get('show_mouse', False)
            or self.config.get('extra_display', {}).get('show_cps', False)
            or self.config.get('extra_display', {}).get('show_mouse_direction', False)
        )
        if not devices:
            print("Warning: No keyboard devices found")
            self.set_permission_warning()
            return

        readable_devices = []
        permission_denied = False
        for device_path in devices:
            try:
                with open(device_path, 'rb'):
                    pass
                readable_devices.append(device_path)
            except PermissionError:
                permission_denied = True
            except Exception:
                pass

        if permission_denied and not readable_devices:
            self.set_permission_warning()
            return

        if permission_denied:
            self.set_permission_warning()

        for device_path in readable_devices:
            thread = threading.Thread(target=self.listen_device, args=(device_path,), daemon=True)
            thread.start()
            self.listener_threads.append(thread)

    def set_permission_warning(self):
        self.permission_denied = True
        self.root.title("Keyboard Key Display - Insufficient permissions.")
        if self.status_label is not None:
            self.status_label.config(fg=self.config['colors']['close_button'])
            
    def listen_device(self, device_path):
        try:
            with open(device_path, 'rb') as f:
                while self.running:
                    event = f.read(EVENT_SIZE)
                    if not event:
                        time.sleep(0.001)
                        continue
                    tv_sec, tv_usec, type_, code, value = struct.unpack(EVENT_FORMAT, event)
                    if type_ == EV_REL:
                        self.root.after(0, lambda c=code, v=value: self.on_mouse_relative_motion(c, v))
                    elif type_ == EV_KEY:
                        key_name = KEY_MAP.get(code, f'Key{code}')
                        if value == KEY_PRESS:
                            self.root.after(0, lambda k=key_name: self.on_key_press(k))
                        elif value == KEY_RELEASE:
                            self.root.after(0, lambda k=key_name: self.on_key_release(k))
        except PermissionError:
            self.root.after(0, self.set_permission_warning)
        except Exception as e:
            print(f"Device listener error for {device_path}: {e}")
            
    def on_key_press(self, key_name):
        """Key press"""
        if key_name.startswith('Mouse '):
            self.on_mouse_press(key_name)
            return
        if (key_name == 'Q' and 'Ctrl' in self.current_keys) or (key_name == 'Ctrl' and 'Q' in self.current_keys):
            self.on_closing()
            return
        if 'Ctrl' in self.current_keys and key_name == 'F9':
            self.root.after(0, self.open_config_dialog)
            return
        if key_name in self.key_buttons:
            self.key_buttons[key_name].press()
        self.current_keys.add(key_name)
        
    def on_key_release(self, key_name):
        """Key release"""
        if key_name.startswith('Mouse '):
            self.on_mouse_release(key_name)
            return
        if key_name in self.key_buttons:
            self.key_buttons[key_name].release()
        self.current_keys.discard(key_name)
        
    def on_mouse_relative_motion(self, code, value):
        if self.mouse_direction_canvas is None:
            return
        if code == REL_X:
            self.mouse_direction_vector[0] += value * 0.35
        elif code == REL_Y:
            self.mouse_direction_vector[1] += value * 0.35
        else:
            return
        # Only add trace point if trace is enabled and throttle to reduce lag
        extra = self.config.get('extra_display', {})
        if extra.get('show_mouse_trace', True):
            current_time = time.time()
            # Limit trace points: add at most one per 50ms, deque auto-limits to 20 points
            if not self.mouse_trace_positions or current_time - self.mouse_trace_positions[-1][2] > 0.05:
                self.mouse_trace_positions.append((self.mouse_direction_vector[0], self.mouse_direction_vector[1], current_time))
        self.draw_mouse_direction_chart()

    def draw_mouse_direction_chart(self, override_color=None):
        if self.mouse_direction_canvas is None:
            return
        colors = self.config['colors']
        canvas = self.mouse_direction_canvas
        canvas.delete('all')
        size = 90
        center = size // 2
        radius = 34
        # Use override color for animation, otherwise use normal colors
        border_color = override_color if override_color else colors['key_border']
        canvas.create_oval(center - radius, center - radius, center + radius, center + radius,
                           outline=border_color, width=2)
        canvas.create_line(center - radius, center, center + radius, center, fill=border_color)
        canvas.create_line(center, center - radius, center, center + radius, fill=border_color)

        # Draw trace with fading tail
        now = time.time()
        trace_color = colors.get('mouse_direction_trace', '#e94560')
        for i, (tx, ty, t) in enumerate(self.mouse_trace_positions):
            age = now - t
            if age > 0.5:
                continue
            alpha = max(0.0, 1.0 - age / 0.5)
            length_t = max((tx * tx + ty * ty) ** 0.5, 1)
            scale_t = min(radius, length_t) / length_t
            px = center + int(tx * scale_t)
            py = center + int(ty * scale_t)
            dot_size = max(1, int(3 * alpha))
            r, g, b = KeyButton.hex_to_rgb_static(trace_color)
            faded = '#{:02x}{:02x}{:02x}'.format(int(r * alpha), int(g * alpha), int(b * alpha))
            canvas.create_oval(px - dot_size, py - dot_size, px + dot_size, py + dot_size,
                               fill=faded, outline='')

        # Draw current direction dot (origin)
        dx, dy = self.mouse_direction_vector
        length = max((dx * dx + dy * dy) ** 0.5, 1)
        scale = min(radius, length) / length
        origin_x = center + dx * scale
        origin_y = center + dy * scale
        canvas.create_oval(origin_x - 3, origin_y - 3, origin_x + 3, origin_y + 3,
                           fill=colors['key_text'], outline=colors['key_active'], width=1)

    def schedule_mouse_direction_decay(self):
        if self.mouse_direction_canvas is None or not self.running:
            return
        decay = max(self.config.get('extra_display', {}).get('mouse_direction_decay', 1.25), 1.01)
        self.mouse_direction_vector[0] /= decay
        self.mouse_direction_vector[1] /= decay
        if abs(self.mouse_direction_vector[0]) < 0.5:
            self.mouse_direction_vector[0] = 0
        if abs(self.mouse_direction_vector[1]) < 0.5:
            self.mouse_direction_vector[1] = 0
        self.draw_mouse_direction_chart()
        self.mouse_direction_job = self.root.after(80, self.schedule_mouse_direction_decay)

    def on_mouse_press(self, key_name):
        extra = self.config.get('extra_display', {})
        if extra.get('show_mouse', False) and key_name in self.mouse_buttons:
            self.mouse_buttons[key_name].press()
        if extra.get('show_cps', False):
            if key_name == 'Mouse Left':
                self.left_click_timestamps.append(time.time())
            elif key_name == 'Mouse Right':
                self.right_click_timestamps.append(time.time())
            self.update_cps_display()

    def on_mouse_release(self, key_name):
        if key_name in self.mouse_buttons:
            self.mouse_buttons[key_name].release()

    def update_cps_display(self):
        if self.cps_label is None or self.cps_text is None or not self.running:
            return
        now = time.time()
        self.left_click_timestamps = [t for t in self.left_click_timestamps if now - t <= 1.0]
        self.right_click_timestamps = [t for t in self.right_click_timestamps if now - t <= 1.0]
        self.cps_label.itemconfig(self.cps_text, text=f"L CPS: {len(self.left_click_timestamps)}    R CPS: {len(self.right_click_timestamps)}")

    def schedule_cps_update(self):
        self.update_cps_display()
        if self.cps_label is not None and self.running:
            self.cps_update_job = self.root.after(100, self.schedule_cps_update)
        
    def on_closing(self):
        if self.closed:
            return
        self.closed = True
        self.running = False
        # Start fade-out animation instead of immediate close
        self._animate_window_exit()

    def _animate_window_exit(self, duration=0.2):
        """Animate window fade-out before closing"""
        # Save window positions before closing
        try:
            self.config['window']['position']['x'] = self.root.winfo_rootx()
            self.config['window']['position']['y'] = self.root.winfo_rooty()
            if self.mouse_window is not None:
                self.config['window']['mouse_position']['x'] = self.mouse_window.winfo_rootx()
                self.config['window']['mouse_position']['y'] = self.mouse_window.winfo_rooty()
            save_config(self.config)
        except Exception:
            pass

        self._window_exit_start = time.time()
        self._animate_window_exit_frame(duration)

    def _animate_window_exit_frame(self, duration):
        """Animate a single frame of window exit"""
        elapsed = time.time() - self._window_exit_start
        progress = min(elapsed / duration, 1.0)

        # Easing function: ease-in cubic (reverse of entrance)
        ease_progress = progress ** 3
        alpha = 1.0 - ease_progress

        try:
            # Fade out mouse window first if it exists
            if self.mouse_window is not None:
                final_alpha = self.config['window'].get('alpha', 0.95)
                mouse_alpha = alpha * final_alpha
                self.mouse_window.attributes('-alpha', max(0.0, mouse_alpha))

            # Fade out main window
            self.root.attributes('-alpha', max(0.0, alpha))
        except tk.TclError:
            pass

        if progress < 1.0:
            self.root.after(16, lambda: self._animate_window_exit_frame(duration))
        else:
            # Animation complete, destroy windows
            self._destroy_windows()

    def _destroy_windows(self):
        """Destroy all windows after fade-out animation"""
        if self.cps_update_job is not None:
            try:
                self.root.after_cancel(self.cps_update_job)
            except tk.TclError:
                pass
        if self.mouse_direction_job is not None:
            try:
                self.root.after_cancel(self.mouse_direction_job)
            except tk.TclError:
                pass
        if self.mouse_window is not None:
            try:
                self.mouse_window.destroy()
            except tk.TclError:
                pass
        self.root.destroy()
        
    def open_config_dialog(self):
        """Open configuration dialog"""
        ConfigDialog(self)

    def run(self):
        """Run application"""
        self.root.mainloop()


def main():
    print("Keyboard Key Display by ThinkReally is running...")
    print(f"Configuration file: config.json")
    app = KeyDisplayApp()
    app.run()


if __name__ == "__main__":
    main()
