import unittest
from unittest.mock import patch
import os
from computer.screen.screen import capture_screenshot

class TestScreen(unittest.TestCase):

    @patch('computer.screen.screen.subprocess.run')
    def test_capture_screenshot(self, mock_run):
        path = capture_screenshot("/test/path.png")
        self.assertEqual(path, "/test/path.png")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args, ['scrot', '/test/path.png', '-d', '0', '-z'])

if __name__ == '__main__':
    unittest.main()
