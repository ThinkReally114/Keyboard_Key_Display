#!/usr/bin/env python3
"""Tests for key_display.py"""

import unittest
import json
import os
import sys

# Get the project root directory (where this test file is located)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_file_path(filename):
    """Get absolute path to a file in the project root"""
    return os.path.join(PROJECT_ROOT, filename)


class TestConfig(unittest.TestCase):
    """Test configuration file"""

    def test_config_exists(self):
        """Test that config.json exists"""
        self.assertTrue(os.path.exists(get_file_path('config.json')))

    def test_config_valid_json(self):
        """Test that config.json is valid JSON"""
        with open(get_file_path('config.json'), 'r') as f:
            config = json.load(f)
        self.assertIsInstance(config, dict)

    def test_config_has_required_sections(self):
        """Test that config has required sections"""
        with open(get_file_path('config.json'), 'r') as f:
            config = json.load(f)
        self.assertIn('window', config)
        self.assertIn('colors', config)
        self.assertIn('keyboard', config)

    def test_window_config(self):
        """Test window configuration"""
        with open(get_file_path('config.json'), 'r') as f:
            config = json.load(f)
        window = config['window']
        self.assertIn('alpha', window)
        self.assertIn('always_on_top', window)
        self.assertIn('corner_radius', window)
        self.assertIn('frameless', window)

    def test_colors_config(self):
        """Test colors configuration"""
        with open(get_file_path('config.json'), 'r') as f:
            config = json.load(f)
        colors = config['colors']
        required_colors = [
            'background', 'border', 'title_bar', 'text',
            'key_idle', 'key_active', 'key_text', 'key_border',
            'status_online', 'close_button', 'close_button_hover'
        ]
        for color in required_colors:
            self.assertIn(color, colors)

    def test_keyboard_config(self):
        """Test keyboard configuration"""
        with open(get_file_path('config.json'), 'r') as f:
            config = json.load(f)
        keyboard = config['keyboard']
        self.assertIn('layout', keyboard)
        self.assertIn('key_width', keyboard)
        self.assertIn('key_height', keyboard)
        self.assertIn('key_padding', keyboard)
        self.assertIn('key_radius', keyboard)
        self.assertIn('font_size', keyboard)


class TestKeyDisplay(unittest.TestCase):
    """Test key_display.py"""

    def test_key_display_exists(self):
        """Test that key_display.py exists"""
        self.assertTrue(os.path.exists(get_file_path('key_display.py')))

    def test_key_display_executable(self):
        """Test that key_display.py has shebang"""
        with open(get_file_path('key_display.py'), 'r') as f:
            first_line = f.readline()
        self.assertTrue(first_line.startswith('#!'))


class TestRunScript(unittest.TestCase):
    """Test run.sh"""

    def test_run_script_exists(self):
        """Test that run.sh exists"""
        self.assertTrue(os.path.exists(get_file_path('run.sh')))

    def test_run_script_executable(self):
        """Test that run.sh is executable or has shebang"""
        with open(get_file_path('run.sh'), 'r') as f:
            first_line = f.readline()
        self.assertTrue(first_line.startswith('#!'))


if __name__ == '__main__':
    unittest.main()
