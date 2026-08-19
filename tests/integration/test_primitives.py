import time
import os
import sys
import subprocess

# Add root to python path so we can import computer package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from computer.screen.screen import capture_screenshot
from computer.mouse.mouse import move_mouse, click
from computer.keyboard.keyboard import type_text, press_key

def main():
    print("Testing Screen Capture...")
    screenshot_1 = "/workspace/screenshot_before.png"
    capture_screenshot(screenshot_1)
    print(f"Captured initial screenshot to {screenshot_1}")
    
    print("\nStarting Mousepad (text editor) to test keyboard input...")
    # Open mousepad via subprocess to have an active window
    display = os.environ.get("DISPLAY", ":99")
    proc = subprocess.Popen(["mousepad"], env={"DISPLAY": display})
    
    # Wait for mousepad to open and gain focus
    time.sleep(2)
    
    print("\nTesting Mouse Input (Moving to center of screen)...")
    # Move mouse roughly to center (1280x800 resolution)
    move_mouse(640, 400)
    time.sleep(0.5)
    click() # Click to ensure mousepad has focus
    time.sleep(0.5)
    
    print("\nTesting Keyboard Input...")
    type_text("Hello from AI computer primitives!\n")
    time.sleep(0.5)
    type_text("This text was typed via xdotool.\n")
    time.sleep(1)
    
    print("\nCapturing final screenshot...")
    screenshot_2 = "/workspace/screenshot_after.png"
    capture_screenshot(screenshot_2)
    print(f"Captured final screenshot to {screenshot_2}")
    
    print("\nCleaning up (Closing Mousepad)...")
    proc.terminate()
    
    print("\nIntegration Test Complete! Check /workspace for screenshots.")

if __name__ == "__main__":
    main()
