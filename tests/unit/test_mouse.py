import unittest
from unittest.mock import patch
import os
from computer.mouse.mouse import move_mouse, click, double_click, scroll, drag

class TestMouse(unittest.TestCase):

    @patch('computer.mouse.mouse.subprocess.run')
    def test_move_mouse(self, mock_run):
        move_mouse(100, 200)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'mousemove', '100', '200'])

    @patch('computer.mouse.mouse.subprocess.run')
    def test_click(self, mock_run):
        click(1)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'click', '1'])

    @patch('computer.mouse.mouse.subprocess.run')
    def test_double_click(self, mock_run):
        double_click(1)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'click', '--repeat', '2', '1'])

    @patch('computer.mouse.mouse.subprocess.run')
    def test_scroll(self, mock_run):
        scroll('up', 3)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'click', '--repeat', '3', '4'])

    @patch('computer.mouse.mouse.subprocess.run')
    def test_drag(self, mock_run):
        drag(10, 20, 100, 200)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['xdotool', 'mousemove', '10', '20', 'mousedown', '1', 'mousemove', '100', '200', 'mouseup', '1'])

if __name__ == '__main__':
    unittest.main()
