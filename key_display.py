#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import struct
import threading
import os
import glob
import time


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
    except Exception:
        pass

    # Override with user config (if exists), otherwise create it
    try:
        if os.path.exists(user_path):
            with open(user_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            merge_config(config, user_config)
        else:
            save_config(config)
    except Exception:
        pass

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
    except Exception:
        pass
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
            self.bg_rect = self.create_rounded_rectangle(
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
            self.bg_rect = self.create_rounded_rectangle(
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
        
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = rounded_rectangle_points(x1, y1, x2, y2, radius)
        return self.canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)
        
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


class ConfigDialog:
    """Visual configuration editor dialog"""
    def __init__(self, parent_app):
        self.app = parent_app
        self.config = create_default_config()
        # Merge current app config
        for section in self.app.config:
            if isinstance(self.app.config[section], dict):
                self.config[section].update(self.app.config[section])
            else:
                self.config[section] = self.app.config[section]

        self.dialog = tk.Toplevel(self.app.root)
        self.dialog.title("Configuration - Keyboard Key Display")
        self.dialog.geometry("650x550")
        self.dialog.configure(bg='#1a1a2e')
        self.dialog.resizable(True, True)
        self.dialog.transient(self.app.root)
        self.app.config_dialog_open = True
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        self.color_widgets = {}
        self.tabs = {}
        self.current_tab = None
        self._build_ui()

    def _build_ui(self):
        # Tab buttons frame
        tab_frame = tk.Frame(self.dialog, bg='#1a1a2e')
        tab_frame.pack(fill='x', padx=10, pady=(10, 0))

        self.tab_buttons = {}
        tab_names = ['Window', 'Colors', 'Keyboard', 'Extra', 'Layout']
        for i, name in enumerate(tab_names):
            btn = tk.Button(
                tab_frame,
                text=name,
                bg='#0f3460',
                fg='white',
                activebackground='#e94560',
                activeforeground='white',
                bd=0,
                padx=15,
                pady=5,
                font=('Noto Sans', 10),
                cursor='hand2'
            )
            btn.pack(side='left', padx=(0, 5))
            btn.config(command=lambda n=name: self._switch_tab(n))
            self.tab_buttons[name] = btn

        # Content frame
        self.content_frame = tk.Frame(self.dialog, bg='#1a1a2e')
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Build all tab contents
        self._build_window_content()
        self._build_colors_content()
        self._build_keyboard_content()
        self._build_extra_content()
        self._build_layout_content()

        # Show first tab
        self._switch_tab('Window')

        # Buttons
        btn_frame = tk.Frame(self.dialog, bg='#1a1a2e')
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="Reset", bg='#0f3460', fg='white',
                  activebackground='#e94560', bd=0, padx=15, pady=5,
                  command=self._reset).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancel", bg='#0f3460', fg='white',
                  activebackground='#e94560', bd=0, padx=15, pady=5,
                  command=self._on_close).pack(side='right', padx=5)
        tk.Button(btn_frame, text="Save", bg='#0f3460', fg='white',
                  activebackground='#e94560', bd=0, padx=15, pady=5,
                  command=self._save).pack(side='right', padx=5)
        tk.Button(btn_frame, text="Apply", bg='#0f3460', fg='white',
                  activebackground='#e94560', bd=0, padx=15, pady=5,
                  command=self._apply).pack(side='right', padx=5)

    def _switch_tab(self, name):
        """Switch to specified tab"""
        # Hide all tabs
        for tab in self.tabs.values():
            tab.pack_forget()
        # Show selected tab
        self.tabs[name].pack(fill='both', expand=True)
        self.current_tab = name
        # Update button colors
        for tab_name, btn in self.tab_buttons.items():
            if tab_name == name:
                btn.config(bg='#e94560')
            else:
                btn.config(bg='#0f3460')

    def _build_window_content(self):
        frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.tabs['Window'] = frame

        row = 0
        tk.Label(frame, text="Alpha (transparency):", bg='#1a1a2e', fg='white',
                 font=('Noto Sans', 10)).grid(row=row, column=0, sticky='w', padx=10, pady=8)
        self.alpha_var = tk.DoubleVar(value=self.config['window']['alpha'])
        alpha_frame = tk.Frame(frame, bg='#1a1a2e')
        alpha_frame.grid(row=row, column=1, sticky='ew', padx=10, pady=8)
        tk.Scale(alpha_frame, from_=0.1, to=1.0, variable=self.alpha_var,
                 orient='horizontal', bg='#1a1a2e', fg='white',
                 highlightthickness=0, length=200).pack(side='left')
        self.alpha_label = tk.Label(alpha_frame, text=f"{self.alpha_var.get():.2f}",
                                     bg='#1a1a2e', fg='white', width=6)
        self.alpha_label.pack(side='left', padx=5)
        self.alpha_var.trace_add('write', lambda *a: self.alpha_label.config(text=f"{self.alpha_var.get():.2f}"))

        row += 1
        self.always_on_top_var = tk.BooleanVar(value=self.config['window']['always_on_top'])
        tk.Checkbutton(frame, text="Always on top", variable=self.always_on_top_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        row += 1
        self.frameless_var = tk.BooleanVar(value=self.config['window'].get('frameless', True))
        tk.Checkbutton(frame, text="Frameless window", variable=self.frameless_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=row, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        row += 1
        tk.Label(frame, text="Corner radius:", bg='#1a1a2e', fg='white',
                 font=('Noto Sans', 10)).grid(row=row, column=0, sticky='w', padx=10, pady=8)
        self.corner_radius_var = tk.IntVar(value=self.config['window'].get('corner_radius', 14))
        tk.Spinbox(frame, from_=0, to=50, textvariable=self.corner_radius_var,
                   width=10, bg='#0f3460', fg='white').grid(row=row, column=1, sticky='w', padx=10, pady=8)

        frame.columnconfigure(1, weight=1)

    def _build_colors_content(self):
        canvas = tk.Canvas(self.content_frame, bg='#1a1a2e', highlightthickness=0)
        self.tabs['Colors'] = canvas

        scrollbar = tk.Scrollbar(canvas, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas, bg='#1a1a2e')
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        colors = self.config['colors']
        color_labels = {
            'background': 'Background', 'border': 'Border', 'title_bar': 'Title Bar',
            'text': 'Title Text', 'text_glow': 'Text Glow', 'key_idle': 'Key Idle Text',
            'key_active': 'Key Active', 'key_text': 'Key Active Text', 'key_border': 'Key Border',
            'status_online': 'Status Dot', 'close_button': 'Close Button',
            'close_button_hover': 'Close Hover', 'mouse_direction_trace': 'Mouse Trace'
        }

        self.color_widgets = {}
        for idx, (key, label) in enumerate(color_labels.items()):
            row = idx // 2
            col = (idx % 2) * 4
            tk.Label(inner, text=f"{label}:", bg='#1a1a2e', fg='white').grid(
                row=row, column=col, sticky='w', padx=(10, 2), pady=4)
            var = tk.StringVar(value=colors.get(key, '#000000'))
            entry = tk.Entry(inner, textvariable=var, width=10, bg='#0f3460', fg='white')
            entry.grid(row=row, column=col + 1, padx=2, pady=4)
            preview = tk.Canvas(inner, width=24, height=24, bg=colors.get(key, '#000000'),
                                highlightthickness=1, highlightbackground='white')
            preview.grid(row=row, column=col + 2, padx=(2, 10), pady=4)
            var.trace_add('write', lambda *a, v=var, p=preview: self._update_preview(p, v))
            btn = tk.Button(inner, text="...", width=3, bg='#0f3460', fg='white',
                            activebackground='#e94560', bd=0,
                            command=lambda v=var, p=preview: self._pick_color(v, p))
            btn.grid(row=row, column=col + 3, padx=(0, 5), pady=4)
            self.color_widgets[key] = var

    def _update_preview(self, preview, var):
        try:
            color = var.get()
            if color.startswith('#') and len(color) == 7:
                preview.configure(bg=color)
        except tk.TclError:
            pass

    def _pick_color(self, var, preview):
        color = colorchooser.askcolor(color=var.get(), parent=self.dialog)
        if color and color[1]:
            var.set(color[1])
            preview.configure(bg=color[1])

    def _build_keyboard_content(self):
        frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.tabs['Keyboard'] = frame

        kb = self.config['keyboard']
        fields = [
            ('key_width', 'Key Width', 10, 100),
            ('key_height', 'Key Height', 10, 100),
            ('key_padding', 'Key Padding', 0, 20),
            ('key_radius', 'Key Corner Radius', 0, 30),
            ('font_size', 'Font Size', 6, 24),
        ]
        self.kb_vars = {}
        for idx, (key, label, lo, hi) in enumerate(fields):
            tk.Label(frame, text=f"{label}:", bg='#1a1a2e', fg='white',
                     font=('Noto Sans', 10)).grid(row=idx, column=0, sticky='w', padx=10, pady=8)
            var = tk.IntVar(value=kb.get(key, 42))
            tk.Spinbox(frame, from_=lo, to=hi, textvariable=var, width=10,
                       bg='#0f3460', fg='white').grid(row=idx, column=1, sticky='w', padx=10, pady=8)
            self.kb_vars[key] = var

        frame.columnconfigure(1, weight=1)

    def _build_extra_content(self):
        frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.tabs['Extra'] = frame

        extra = self.config.get('extra_display', {})
        self.show_mouse_var = tk.BooleanVar(value=extra.get('show_mouse', False))
        self.show_cps_var = tk.BooleanVar(value=extra.get('show_cps', False))
        self.show_mouse_direction_var = tk.BooleanVar(value=extra.get('show_mouse_direction', False))
        self.show_mouse_trace_var = tk.BooleanVar(value=extra.get('show_mouse_trace', True))
        self.mouse_direction_decay_var = tk.DoubleVar(value=extra.get('mouse_direction_decay', 1.25))

        tk.Checkbutton(frame, text="Show mouse buttons", variable=self.show_mouse_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=0, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        tk.Checkbutton(frame, text="Show CPS", variable=self.show_cps_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=1, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        tk.Checkbutton(frame, text="Show mouse direction chart", variable=self.show_mouse_direction_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=2, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        tk.Checkbutton(frame, text="Show mouse trace", variable=self.show_mouse_trace_var,
                       bg='#1a1a2e', fg='white', selectcolor='#0f3460',
                       activebackground='#1a1a2e', activeforeground='white').grid(
            row=3, column=0, columnspan=2, sticky='w', padx=10, pady=8)

        tk.Label(frame, text="Direction decay:", bg='#1a1a2e', fg='white',
                 font=('Noto Sans', 10)).grid(row=4, column=0, sticky='w', padx=10, pady=8)
        tk.Spinbox(frame, from_=1.01, to=5.0, increment=0.05, textvariable=self.mouse_direction_decay_var,
                   width=10, bg='#0f3460', fg='white').grid(row=4, column=1, sticky='w', padx=10, pady=8)

        tk.Label(frame, text="CPS counts mouse clicks per second. Direction decay > 1 means stronger return-to-center damping.",
                 bg='#1a1a2e', fg='#888888').grid(row=5, column=0, sticky='w', padx=10, pady=(5, 10))

        frame.columnconfigure(1, weight=1)

    def _build_layout_content(self):
        frame = tk.Frame(self.content_frame, bg='#1a1a2e')
        self.tabs['Layout'] = frame

        tk.Label(frame, text="Edit keyboard layout (JSON array, one row per line):",
                 bg='#1a1a2e', fg='white', font=('Noto Sans', 10)).pack(anchor='w', padx=10, pady=(10, 5))

        text_frame = tk.Frame(frame, bg='#1a1a2e')
        text_frame.pack(fill='both', expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')

        self.layout_text = tk.Text(text_frame, bg='#0f3460', fg='white', insertbackground='white',
                                    font=('Courier', 10), wrap='none', yscrollcommand=scrollbar.set)
        self.layout_text.pack(fill='both', expand=True)
        scrollbar.config(command=self.layout_text.yview)

        layout_json = json.dumps(self.config['keyboard']['layout'], indent=4, ensure_ascii=False)
        self.layout_text.insert('1.0', layout_json)

        tk.Label(frame, text="Each row is a list of key names. Use KEY_MAP names (e.g. 'Esc', 'Q', 'Space', 'Shift').",
                 bg='#1a1a2e', fg='#888888').pack(anchor='w', padx=10, pady=(5, 10))

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
        try:
            cfg = self._collect_config()
            save_config(cfg)
            messagebox.showinfo("Saved", "Configuration saved!\nPlease restart the application to apply changes.", parent=self.dialog)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}", parent=self.dialog)

    def _save(self):
        try:
            cfg = self._collect_config()
            save_config(cfg)
            messagebox.showinfo("Saved", "Configuration saved!\nPlease restart the application to apply changes.", parent=self.dialog)
            self._on_close()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}", parent=self.dialog)

    def _reset(self):
        if messagebox.askyesno("Reset", "Reset all settings to default?\n(Keyboard layout will be preserved)", parent=self.dialog):
            try:
                cfg = create_default_config()
                # Preserve current keyboard layout
                cfg['keyboard']['layout'] = self.config['keyboard']['layout']
                save_config(cfg)
                messagebox.showinfo("Reset", "Default configuration saved.\nPlease restart the application.", parent=self.dialog)
                self._on_close()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reset configuration:\n{e}", parent=self.dialog)


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
        self.mouse_trace_positions = []
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
            self.cps_bg_rect = self.cps_label.create_polygon(
                rounded_rectangle_points(1, 1, max(int(kb['key_width'] * 3.2), 130) - 1, kb['key_height'] - 1, kb['key_radius']),
                smooth=True,
                splinesteps=24,
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
            pass
            
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
            # Limit trace points: add at most one per 50ms, keep max 20 points
            if not self.mouse_trace_positions or current_time - self.mouse_trace_positions[-1][2] > 0.05:
                self.mouse_trace_positions.append((self.mouse_direction_vector[0], self.mouse_direction_vector[1], current_time))
                if len(self.mouse_trace_positions) > 20:
                    self.mouse_trace_positions.pop(0)
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
        fresh_trace = []
        for i, (tx, ty, t) in enumerate(self.mouse_trace_positions):
            age = now - t
            if age > 0.5:
                continue
            fresh_trace.append((tx, ty, t))
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
        self.mouse_trace_positions = fresh_trace

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
