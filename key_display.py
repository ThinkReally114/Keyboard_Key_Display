#!/usr/bin/env python3

import tkinter as tk
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
    65: 'F7', 66: 'F8', 67: 'F9', 68: 'F10', 69: 'NumLock', 70: 'ScrollLock',
    71: 'Home', 72: '↑', 73: 'PageUp', 74: '-', 75: '←', 76: '', 77: '→', 78: '+',
    79: 'End', 80: '↓', 81: 'PageDown', 82: 'Insert', 83: 'Delete',
    87: 'F11', 88: 'F12', 91: 'Win', 97: 'Ctrl', 100: 'Alt',
    125: 'Super', 126: 'Super',
}

DEFAULT_CONFIG = {
    "window": {"alpha": 0.85, "always_on_top": True, "corner_radius": 14, "frameless": True},
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


def load_config():
    """Load configuration file"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    config = DEFAULT_CONFIG.copy()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for key in user_config:
                    if key in config and isinstance(config[key], dict) and isinstance(user_config[key], dict):
                        config[key].update(user_config[key])
                    else:
                        config[key] = user_config[key]
    except Exception as e:
        print(f"Failed to load configuration file: {e}")
    return config


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
        elif key_name in ['Ctrl', 'Alt']:
            width = int(kb['key_width'] * 1.3)
        else:
            width = kb['key_width']
        
        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=kb['key_height'],
            bg=colors['background'],
            highlightthickness=0
        )
        self.canvas.grid(row=row, column=col, padx=kb['key_padding'], pady=kb['key_padding'])
        
        radius = min(kb.get('key_radius', 8), width // 2, kb['key_height'] // 2)
        self.rect = self.create_rounded_rectangle(
            2, 2, width - 2, kb['key_height'] - 2,
            radius=radius,
            fill=colors['background'],
            outline=colors['key_border'],
            width=2
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
        self.is_pressed = True
        self.start_transition(to_active=True)
        
    def release(self):
        """Release key""" 
        self.is_pressed = False
        self.start_transition(to_active=False)
        
    def start_transition(self, to_active):
        """Start 0.2 second color transition animation"""
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
        self.transition_start = time.monotonic()
        self.animate_transition(to_active)
        
    def animate_transition(self, to_active):
        """Execute color transition animation"""
        colors = self.config['colors']
        duration = 0.2
        progress = min((time.monotonic() - self.transition_start) / duration, 1.0)
        
        if to_active:
            bg_color = self.mix_color(colors['background'], colors['key_active'], progress)
            border_color = self.mix_color(colors['key_border'], colors['key_active'], progress)
            text_color = self.mix_color(colors['key_idle'], colors['key_text'], progress)
        else:
            bg_color = self.mix_color(colors['key_active'], colors['background'], progress)
            border_color = self.mix_color(colors['key_active'], colors['key_border'], progress)
            text_color = self.mix_color(colors['key_text'], colors['key_idle'], progress)
        
        self.canvas.itemconfig(self.rect, fill=bg_color, outline=border_color)
        self.canvas.itemconfig(self.text, fill=text_color)
        
        if progress < 1.0:
            self.animation_id = self.canvas.after(16, self.animate_transition, to_active)
        else:
            self.animation_id = None
            
    def mix_color(self, start_color, end_color, progress):
        """Mix two hexadecimal colors with a given progress"""
        sr, sg, sb = self.hex_to_rgb(start_color)
        er, eg, eb = self.hex_to_rgb(end_color)
        r = int(sr + (er - sr) * progress)
        g = int(sg + (eg - sg) * progress)
        b = int(sb + (eb - sb) * progress)
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def hex_to_rgb(self, color):
        """Hexadecimal color to RGB"""
        color = color.lstrip('#')
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


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
        self.root.bind_all('<ButtonPress-1>', self.handle_pointer_press)
        self.root.bind_all('<ButtonRelease-1>', self.handle_pointer_release)
        self.root.bind_all('<B1-Motion>', self.handle_pointer_motion)
        self.root.bind_all('<Motion>', self.handle_pointer_motion)
        self.root.bind_all('<ButtonPress-3>', lambda event: self.on_closing())
        
        self.current_keys = set()
        self.key_buttons = {}
        self.running = True
        self.closed = False
        self.listener_threads = []
        self._drag_data = {'x': 0, 'y': 0, 'active': False}
        self.title_bar_height = 30
        self.close_area_width = 48
        
        self.setup_ui()
        self.start_keyboard_listener()
        
        self.root.update_idletasks()
        self.fit_window_to_content()
        
    def setup_ui(self):
        """Setup user interface"""
        colors = self.config['colors']
        
        self.window_canvas = tk.Canvas(
            self.root,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )
        self.window_canvas.pack(fill='both', expand=True)
        
        self.main_frame = tk.Frame(self.window_canvas, bg=colors['background'])
        self.window_canvas_window = self.window_canvas.create_window(2, 2, window=self.main_frame, anchor='nw')
        main_frame = self.main_frame
        self.window_canvas.bind('<Configure>', self.on_window_canvas_configure)
        
        title_frame = tk.Frame(main_frame, bg=colors['title_bar'], cursor='fleur', height=self.title_bar_height)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        title_frame.bind('<Button-1>', self.start_drag)
        title_frame.bind('<B1-Motion>', self.on_drag)
        
        title_label = tk.Label(
            title_frame,
            text="KEY DISPLAY",
            font=('Noto Sans', 10, 'bold'),
            fg=colors['text'],
            bg=colors['title_bar'],
            cursor='fleur'
        )
        title_label.pack(side='left', padx=10)
        
        self.status_label = tk.Label(
            title_frame,
            text="●",
            font=('Noto Sans', 8),
            fg=colors['status_online'],
            bg=colors['title_bar'],
            cursor='fleur'
        )
        self.status_label.pack(side='left')
        
        close_area = tk.Frame(title_frame, bg=colors['title_bar'], width=self.close_area_width, height=self.title_bar_height, cursor='hand2')
        close_area.pack(side='right')
        close_area.pack_propagate(False)
        close_btn = tk.Label(
            close_area,
            text="✕",
            font=('Noto Sans', 12, 'bold'),
            fg=colors['close_button'],
            bg=colors['title_bar'],
            cursor='hand2'
        )
        close_btn.pack(fill='both', expand=True)
        for widget in (close_area, close_btn):
            widget.bind('<ButtonPress-1>', lambda e: self.on_closing())
            widget.bind('<ButtonRelease-1>', lambda e: self.on_closing())
            widget.bind('<Enter>', lambda e: close_btn.config(fg=colors['close_button_hover']))
            widget.bind('<Leave>', lambda e: close_btn.config(fg=colors['close_button']))
        for widget in (title_frame, title_label, self.status_label):
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)
        
        keyboard_frame = tk.Frame(main_frame, bg=colors['background'])
        keyboard_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        kb = self.config['keyboard']
        
        for row_idx, row in enumerate(kb['layout']):
            row_frame = tk.Frame(keyboard_frame, bg=colors['background'])
            row_frame.pack(fill='x', pady=1)
            
            for col_idx, key_name in enumerate(row):
                if key_name:
                    btn = KeyButton(row_frame, key_name, 0, col_idx, self.config)
                    self.key_buttons[key_name] = btn
                    
    def listen_device(self, device_path):
        """Listen to a single input device"""
        try:
            with open(device_path, 'rb') as f:
                while self.running:
                    data = f.read(EVENT_SIZE)
                    if not data or len(data) < EVENT_SIZE:
                        break
                    _, _, event_type, code, value = struct.unpack(EVENT_FORMAT, data)
                    if event_type == EV_KEY and code in KEY_MAP:
                        key_name = KEY_MAP[code]
                        if value == KEY_PRESS:
                            self.current_keys.add(key_name)
                            self.root.after(0, self.on_key_press, key_name)
                        elif value == KEY_RELEASE:
                            self.current_keys.discard(key_name)
                            self.root.after(0, self.on_key_release, key_name)
        except PermissionError:
            self.root.after(0, self.show_error, "Permission denied")
        except Exception:
            pass
                
    def start_keyboard_listener(self):
        """Start keyboard listener"""
        devices = find_keyboard_devices()
        if not devices:
            self.show_error("No input devices found")
            return
        for device in devices:
            thread = threading.Thread(target=self.listen_device, args=(device,), daemon=True)
            thread.start()
            self.listener_threads.append(thread)
            
    def show_error(self, message):
        """Show error message"""
        self.status_label.config(text=f"✗ {message}", fg='#ff4444')
        
    def on_key_press(self, key_name):
        """Key press"""
        if (key_name == 'Q' and 'Ctrl' in self.current_keys) or (key_name == 'Ctrl' and 'Q' in self.current_keys):
            self.on_closing()
            return
        if key_name in self.key_buttons:
            self.key_buttons[key_name].press()
            
    def on_key_release(self, key_name):
        """Key release"""
        if key_name in self.key_buttons:
            self.key_buttons[key_name].release()
            
    def fit_window_to_content(self):
        """Fit window to content size and center it"""
        width = self.main_frame.winfo_reqwidth() + 4
        height = self.main_frame.winfo_reqheight() + 4
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.update_idletasks()
        self.draw_window_background(width, height)
        
    def on_window_canvas_configure(self, event):
        self.draw_window_background(event.width, event.height)
        
    def draw_window_background(self, width, height):
        colors = self.config['colors']
        radius = min(self.config['window'].get('corner_radius', 14), width // 2, height // 2)
        self.window_canvas.delete('window_bg')
        border_points = rounded_rectangle_points(0, 0, width, height, radius)
        inner_points = rounded_rectangle_points(2, 2, width - 2, height - 2, max(radius - 2, 1))
        self.window_canvas.create_polygon(
            border_points,
            smooth=True,
            splinesteps=24,
            fill=colors['border'],
            outline=colors['border'],
            tags='window_bg'
        )
        self.window_canvas.create_polygon(
            inner_points,
            smooth=True,
            splinesteps=24,
            fill=colors['background'],
            outline=colors['background'],
            tags='window_bg'
        )
        self.window_canvas.tag_lower('window_bg')
        self.window_canvas.itemconfigure(self.window_canvas_window, width=max(width - 4, 1), height=max(height - 4, 1))
        
    def handle_pointer_press(self, event):
        pointer_x, pointer_y = self.root.winfo_pointerxy()
        local_x = pointer_x - self.root.winfo_rootx()
        local_y = pointer_y - self.root.winfo_rooty()
        if local_y > self.title_bar_height + 2:
            self._drag_data['active'] = False
            return
        if local_x >= self.root.winfo_width() - self.close_area_width - 4:
            self.on_closing()
            return
        self._drag_data['active'] = True
        self._drag_data['x'] = pointer_x - self.root.winfo_x()
        self._drag_data['y'] = pointer_y - self.root.winfo_y()
        self.root.config(cursor='fleur')
        
    def handle_pointer_motion(self, event):
        if not self._drag_data.get('active'):
            return
        pointer_x, pointer_y = self.root.winfo_pointerxy()
        x = pointer_x - self._drag_data['x']
        y = pointer_y - self._drag_data['y']
        self.root.geometry(f'+{x}+{y}')
        
    def handle_pointer_release(self, event):
        self._drag_data['active'] = False
        self.root.config(cursor='')
        
    def start_drag(self, event):
        self.handle_pointer_press(event)
        
    def on_drag(self, event):
        self.handle_pointer_motion(event)
        
    def on_closing(self):
        """Window closing"""
        if self.closed:
            return
        self.closed = True
        self.running = False
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass
        
    def run(self):
        """Run application"""
        self.root.mainloop()


def main():
    print("Keyboard Key Display by ThinkReally is running...")
    print("Configuration file: config.json")
    
    app = KeyDisplayApp()
    app.run()


if __name__ == "__main__":
    main()
DEFAULT_CONFIG = {
    "window": {"alpha": 0.85, "always_on_top": True, "corner_radius": 14, "frameless": True},
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


def load_config():
    """Load configuration file"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    config = DEFAULT_CONFIG.copy()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                for key in user_config:
                    if key in config and isinstance(config[key], dict) and isinstance(user_config[key], dict):
                        config[key].update(user_config[key])
                    else:
                        config[key] = user_config[key]
    except Exception as e:
        print(f"Failed to load configuration file: {e}")
    return config


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
        elif key_name in ['Ctrl', 'Alt']:
            width = int(kb['key_width'] * 1.3)
        else:
            width = kb['key_width']
        
        self.canvas = tk.Canvas(
            parent,
            width=width,
            height=kb['key_height'],
            bg=colors['background'],
            highlightthickness=0
        )
        self.canvas.grid(row=row, column=col, padx=kb['key_padding'], pady=kb['key_padding'])
        
        radius = min(kb.get('key_radius', 8), width // 2, kb['key_height'] // 2)
        self.rect = self.create_rounded_rectangle(
            2, 2, width - 2, kb['key_height'] - 2,
            radius=radius,
            fill=colors['background'],
            outline=colors['key_border'],
            width=2
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
        self.is_pressed = True
        self.start_transition(to_active=True)
        
    def release(self):
        """Release key""" 
        self.is_pressed = False
        self.start_transition(to_active=False)
        
    def start_transition(self, to_active):
        """Start 0.2 second color transition animation"""
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
        self.transition_start = time.monotonic()
        self.animate_transition(to_active)
        
    def animate_transition(self, to_active):
        """Execute color transition animation"""
        colors = self.config['colors']
        duration = 0.2
        progress = min((time.monotonic() - self.transition_start) / duration, 1.0)
        
        if to_active:
            bg_color = self.mix_color(colors['background'], colors['key_active'], progress)
            border_color = self.mix_color(colors['key_border'], colors['key_active'], progress)
            text_color = self.mix_color(colors['key_idle'], colors['key_text'], progress)
        else:
            bg_color = self.mix_color(colors['key_active'], colors['background'], progress)
            border_color = self.mix_color(colors['key_active'], colors['key_border'], progress)
            text_color = self.mix_color(colors['key_text'], colors['key_idle'], progress)
        
        self.canvas.itemconfig(self.rect, fill=bg_color, outline=border_color)
        self.canvas.itemconfig(self.text, fill=text_color)
        
        if progress < 1.0:
            self.animation_id = self.canvas.after(16, self.animate_transition, to_active)
        else:
            self.animation_id = None
            
    def mix_color(self, start_color, end_color, progress):
        """Mix two hexadecimal colors with a given progress"""
        sr, sg, sb = self.hex_to_rgb(start_color)
        er, eg, eb = self.hex_to_rgb(end_color)
        r = int(sr + (er - sr) * progress)
        g = int(sg + (eg - sg) * progress)
        b = int(sb + (eb - sb) * progress)
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def hex_to_rgb(self, color):
        """Hexadecimal color to RGB"""
        color = color.lstrip('#')
        return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


class KeyDisplayApp:
    def __init__(self):
        self.config = load_config()
        colors = self.config['colors']
        
        self.root = tk.KKD.thinkreally()
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
        self.root.bind_all('<ButtonPress-1>', self.handle_pointer_press)
        self.root.bind_all('<ButtonRelease-1>', self.handle_pointer_release)
        self.root.bind_all('<B1-Motion>', self.handle_pointer_motion)
        self.root.bind_all('<Motion>', self.handle_pointer_motion)
        self.root.bind_all('<ButtonPress-3>', lambda event: self.on_closing())
        
        self.current_keys = set()
        self.key_buttons = {}
        self.running = True
        self.closed = False
        self.listener_threads = []
        self._drag_data = {'x': 0, 'y': 0, 'active': False}
        self.title_bar_height = 30
        self.close_area_width = 48
        
        self.setup_ui()
        self.start_keyboard_listener()
        
        self.root.update_idletasks()
        self.fit_window_to_content()
        
    def setup_ui(self):
        """Setup user interface"""
        colors = self.config['colors']
        
        self.window_canvas = tk.Canvas(
            self.root,
            bg=self.transparent_color,
            highlightthickness=0,
            bd=0
        )
        self.window_canvas.pack(fill='both', expand=True)
        
        self.main_frame = tk.Frame(self.window_canvas, bg=colors['background'])
        self.window_canvas_window = self.window_canvas.create_window(2, 2, window=self.main_frame, anchor='nw')
        main_frame = self.main_frame
        self.window_canvas.bind('<Configure>', self.on_window_canvas_configure)
        
        title_frame = tk.Frame(main_frame, bg=colors['title_bar'], cursor='fleur', height=self.title_bar_height)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        title_frame.bind('<Button-1>', self.start_drag)
        title_frame.bind('<B1-Motion>', self.on_drag)
        
        title_label = tk.Label(
            title_frame,
            text="KEY DISPLAY",
            font=('Noto Sans', 10, 'bold'),
            fg=colors['text'],
            bg=colors['title_bar'],
            cursor='fleur'
        )
        title_label.pack(side='left', padx=10)
        
        self.status_label = tk.Label(
            title_frame,
            text="●",
            font=('Noto Sans', 8),
            fg=colors['status_online'],
            bg=colors['title_bar'],
            cursor='fleur'
        )
        self.status_label.pack(side='left')
        
        close_area = tk.Frame(title_frame, bg=colors['title_bar'], width=self.close_area_width, height=self.title_bar_height, cursor='hand2')
        close_area.pack(side='right')
        close_area.pack_propagate(False)
        close_btn = tk.Label(
            close_area,
            text="✕",
            font=('Noto Sans', 12, 'bold'),
            fg=colors['close_button'],
            bg=colors['title_bar'],
            cursor='hand2'
        )
        close_btn.pack(fill='both', expand=True)
        for widget in (close_area, close_btn):
            widget.bind('<ButtonPress-1>', lambda e: self.on_closing())
            widget.bind('<ButtonRelease-1>', lambda e: self.on_closing())
            widget.bind('<Enter>', lambda e: close_btn.config(fg=colors['close_button_hover']))
            widget.bind('<Leave>', lambda e: close_btn.config(fg=colors['close_button']))
        for widget in (title_frame, title_label, self.status_label):
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)
        
        keyboard_frame = tk.Frame(main_frame, bg=colors['background'])
        keyboard_frame.pack(expand=True, fill='both', padx=5, pady=5)
        
        kb = self.config['keyboard']
        
        for row_idx, row in enumerate(kb['layout']):
            row_frame = tk.Frame(keyboard_frame, bg=colors['background'])
            row_frame.pack(fill='x', pady=1)
            
            for col_idx, key_name in enumerate(row):
                if key_name:
                    btn = KeyButton(row_frame, key_name, 0, col_idx, self.config)
                    self.key_buttons[key_name] = btn
                    
    def listen_device(self, device_path):
        """Listen to a single input device"""
        try:
            with open(device_path, 'rb') as f:
                while self.running:
                    data = f.read(EVENT_SIZE)
                    if not data or len(data) < EVENT_SIZE:
                        break
                    _, _, event_type, code, value = struct.unpack(EVENT_FORMAT, data)
                    if event_type == EV_KEY and code in KEY_MAP:
                        key_name = KEY_MAP[code]
                        if value == KEY_PRESS:
                            self.current_keys.add(key_name)
                            self.root.after(0, self.on_key_press, key_name)
                        elif value == KEY_RELEASE:
                            self.current_keys.discard(key_name)
                            self.root.after(0, self.on_key_release, key_name)
        except PermissionError:
            self.root.after(0, self.show_error, "Permission denied")
        except Exception:
            pass
                
    def start_keyboard_listener(self):
        """Start keyboard listener"""
        devices = find_keyboard_devices()
        if not devices:
            self.show_error("No input devices found")
            return
        for device in devices:
            thread = threading.Thread(target=self.listen_device, args=(device,), daemon=True)
            thread.start()
            self.listener_threads.append(thread)
            
    def show_error(self, message):
        """Show error message"""
        self.status_label.config(text=f"✗ {message}", fg='#ff4444')
        
    def on_key_press(self, key_name):
        """Key press"""
        if (key_name == 'Q' and 'Ctrl' in self.current_keys) or (key_name == 'Ctrl' and 'Q' in self.current_keys):
            self.on_closing()
            return
        if key_name in self.key_buttons:
            self.key_buttons[key_name].press()
            
    def on_key_release(self, key_name):
        """Key release"""
        if key_name in self.key_buttons:
            self.key_buttons[key_name].release()
            
    def fit_window_to_content(self):
        """Fit window to content size and center it"""
        width = self.main_frame.winfo_reqwidth() + 4
        height = self.main_frame.winfo_reqheight() + 4
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.update_idletasks()
        self.draw_window_background(width, height)
        
    def on_window_canvas_configure(self, event):
        self.draw_window_background(event.width, event.height)
        
    def draw_window_background(self, width, height):
        colors = self.config['colors']
        radius = min(self.config['window'].get('corner_radius', 14), width // 2, height // 2)
        self.window_canvas.delete('window_bg')
        border_points = rounded_rectangle_points(0, 0, width, height, radius)
        inner_points = rounded_rectangle_points(2, 2, width - 2, height - 2, max(radius - 2, 1))
        self.window_canvas.create_polygon(
            border_points,
            smooth=True,
            splinesteps=24,
            fill=colors['border'],
            outline=colors['border'],
            tags='window_bg'
        )
        self.window_canvas.create_polygon(
            inner_points,
            smooth=True,
            splinesteps=24,
            fill=colors['background'],
            outline=colors['background'],
            tags='window_bg'
        )
        self.window_canvas.tag_lower('window_bg')
        self.window_canvas.itemconfigure(self.window_canvas_window, width=max(width - 4, 1), height=max(height - 4, 1))
        
    def handle_pointer_press(self, event):
        pointer_x, pointer_y = self.root.winfo_pointerxy()
        local_x = pointer_x - self.root.winfo_rootx()
        local_y = pointer_y - self.root.winfo_rooty()
        if local_y > self.title_bar_height + 2:
            self._drag_data['active'] = False
            return
        if local_x >= self.root.winfo_width() - self.close_area_width - 4:
            self.on_closing()
            return
        self._drag_data['active'] = True
        self._drag_data['x'] = pointer_x - self.root.winfo_x()
        self._drag_data['y'] = pointer_y - self.root.winfo_y()
        self.root.config(cursor='fleur')
        
    def handle_pointer_motion(self, event):
        if not self._drag_data.get('active'):
            return
        pointer_x, pointer_y = self.root.winfo_pointerxy()
        x = pointer_x - self._drag_data['x']
        y = pointer_y - self._drag_data['y']
        self.root.geometry(f'+{x}+{y}')
        
    def handle_pointer_release(self, event):
        self._drag_data['active'] = False
        self.root.config(cursor='')
        
    def start_drag(self, event):
        self.handle_pointer_press(event)
        
    def on_drag(self, event):
        self.handle_pointer_motion(event)
        
    def on_closing(self):
        """Window closing"""
        if self.closed:
            return
        self.closed = True
        self.running = False
        try:
            self.root.quit()
            self.root.destroy()
        except tk.TclError:
            pass
        
    def run(self):
        """Run application"""
        self.root.mainloop()


def main():
    print("Keyboard Key Display by ThinkReally is running...")
    print("Configuration file: config.json")
    
    app = KeyDisplayApp()
    app.run()


if __name__ == "__main__":
    main()
