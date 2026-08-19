import unittest
from unittest.mock import patch
import os
from computer.keyboard.keyboard import type_text, press_key, hotkey

class TestKeyboard(unittest.TestCase):

    @patch('computer.keyboard.keyboard.subprocess.run')
    def test_type_text(self, mock_run):
        type_text("hello", 12)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'type', '--delay', '12', 'hello'])

    @patch('computer.keyboard.keyboard.subprocess.run')
    def test_press_key(self, mock_run):
        press_key("Return")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'key', 'Return'])

    @patch('computer.keyboard.keyboard.subprocess.run')
    def test_hotkey(self, mock_run):
        hotkey("ctrl+c")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'key', 'ctrl+c'])

if __name__ == '__main__':
    unittest.main()
