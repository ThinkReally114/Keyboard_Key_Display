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
    100: 'Alt', 125: 'Super', 126: 'Super'
}

DEFAULT_CONFIG = {
    "window": {
        "alpha": 0.2,
        "always_on_top": True,
        "frameless": True,
        "corner_radius": 14
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
        "close_button_hover": "#ffffff"
    },
    "keyboard": {
        "layout": [
            ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
            ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Backspace"],
            ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
            ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
            ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"]
        ],
        "key_width": 42,
        "key_height": 42,
        "key_padding": 3,
        "key_radius": 8,
        "font_size": 10
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


def load_config():
    """Load configuration file"""
    user_path = get_user_config_path()
    bundled_path = get_bundled_config_path()

    config = DEFAULT_CONFIG.copy()

    # Load from bundled config first (if exists)
    try:
        if os.path.exists(bundled_path):
            with open(bundled_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            config.update(file_config)
    except Exception:
        pass

    # Override with user config (if exists), otherwise create it
    try:
        if os.path.exists(user_path):
            with open(user_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            config.update(user_config)
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


def find_keyboard_devices():
    """Find keyboard devices"""
    keyboard_devices = []
    try:
        with open('/proc/bus/input/devices', 'r') as f:
            content = f.read()
            sections = content.split('\n\n')
            for section in sections:
                if 'EV=' in section and ('120013' in section or '100013' in section or 'kbd' in section.lower()):
                    for line in section.split('\n'):
                        if line.startswith('H: Handlers='):
                            handlers = line.split('=')[1].strip()
                            for handler in handlers.split():
                                if handler.startswith('event'):
                                    device_path = f'/dev/input/{handler}'
                                    if os.path.exists(device_path):
                                        keyboard_devices.append(device_path)
    except Exception:
        pass
    if not keyboard_devices:
        for event_file in sorted(glob.glob('/dev/input/event*')):
            keyboard_devices.append(event_file)
    return keyboard_devices


class KeyButton:
    """Single key button widget - drawn using Canvas"""
    def __init__(self, parent, key_name, row, col, config):
        self.key_name = key_name
        self.is_pressed = False
        self.config = config
        self.animation_id = None
        self.transition_start = 0
        colors = config['colors']
        kb = config['keyboard']
        
        if key_name in ['Backspace', 'Enter', 'Shift', 'CapsLock']:
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
            text=key_name,
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
        self.dialog.grab_set()
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
        tab_names = ['Window', 'Colors', 'Keyboard', 'Layout']
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
            'close_button_hover': 'Close Hover'
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
        self.root.title("Keyboard Key Display by ThinkReally")
        
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind_all('<Control-q>', lambda event: self.on_closing())
        self.root.bind_all('<Control-F9>', lambda event: self.open_config_dialog())
        
        self.current_keys = set()
        self.key_buttons = {}
        self.running = True
        self.closed = False
        self.config_dialog_open = False
        self.listener_threads = []
        self._drag_data = {'x': 0, 'y': 0, 'active': False}
        self.title_bar_height = 30
        self.close_area_width = 48
        
        self.setup_ui()
        self.start_keyboard_listener()
        
        self.root.update_idletasks()
        self.fit_window_to_content()
        
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
                btn = KeyButton(row_frame, key_name, row_idx, col_idx, self.config)
                self.key_buttons[key_name] = btn
                
    def on_window_canvas_configure(self, event=None):
        self.window_canvas.coords(self.window_border, 1, 1, event.width - 2, event.height - 2)
        self.window_canvas.itemconfig(self.window_canvas_window, width=event.width - 6, height=event.height - 6)
                
    def fit_window_to_content(self):
        self.root.update_idletasks()

        # Use Tk's actual requested size to avoid clipping after padding/border changes
        window_width = self.main_frame.winfo_reqwidth() + 6
        window_height = self.main_frame.winfo_reqheight() + 6

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window_canvas.config(width=window_width, height=window_height)
        
    def handle_pointer_press(self, event):
        """Handle mouse press for dragging window"""
        if self.config_dialog_open:
            return
        # Use event coordinates directly
        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root
        self._drag_data['active'] = True

    def handle_pointer_release(self, event):
        """Handle mouse release"""
        self._drag_data['active'] = False

    def handle_pointer_motion(self, event):
        """Handle mouse motion for dragging window"""
        if self._drag_data['active'] and not self.config_dialog_open:
            dx = event.x_root - self._drag_data['x']
            dy = event.y_root - self._drag_data['y']
            x = self.root.winfo_x() + dx
            y = self.root.winfo_y() + dy
            self.root.geometry(f"+{x}+{y}")
            self._drag_data['x'] = event.x_root
            self._drag_data['y'] = event.y_root

    def start_drag(self, event):
        """Start dragging from title bar"""
        if self.config_dialog_open:
            return
        self._drag_data['x'] = event.x_root
        self._drag_data['y'] = event.y_root
        self._drag_data['active'] = True

    def on_drag(self, event):
        """Continue dragging from title bar"""
        if self._drag_data['active'] and not self.config_dialog_open:
            dx = event.x_root - self._drag_data['x']
            dy = event.y_root - self._drag_data['y']
            x = self.root.winfo_x() + dx
            y = self.root.winfo_y() + dy
            self.root.geometry(f"+{x}+{y}")
            self._drag_data['x'] = event.x_root
            self._drag_data['y'] = event.y_root

    def start_keyboard_listener(self):
        devices = find_keyboard_devices()
        if not devices:
            print("Warning: No keyboard devices found")
            return
        for device_path in devices:
            thread = threading.Thread(target=self.listen_device, args=(device_path,), daemon=True)
            thread.start()
            self.listener_threads.append(thread)
            
    def listen_device(self, device_path):
        try:
            with open(device_path, 'rb') as f:
                while self.running:
                    event = f.read(EVENT_SIZE)
                    if not event:
                        continue
                    tv_sec, tv_usec, type_, code, value = struct.unpack(EVENT_FORMAT, event)
                    if type_ == EV_KEY:
                        key_name = KEY_MAP.get(code, f'Key{code}')
                        if value == KEY_PRESS:
                            self.root.after(0, lambda k=key_name: self.on_key_press(k))
                        elif value == KEY_RELEASE:
                            self.root.after(0, lambda k=key_name: self.on_key_release(k))
        except PermissionError:
            pass
        except Exception as e:
            pass
            
    def on_key_press(self, key_name):
        """Key press"""
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
        if key_name in self.key_buttons:
            self.key_buttons[key_name].release()
        self.current_keys.discard(key_name)
        
    def on_closing(self):
        if self.closed:
            return
        self.closed = True
        self.running = False
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
