import subprocess
import os

def capture_screenshot(output_path: str = "/workspace/screenshot.png") -> str:
    """Captures a screenshot of the virtual display and saves it to output_path."""
    display = os.environ.get("DISPLAY", ":99")
    env = os.environ.copy()
    env["DISPLAY"] = display
    try:
        # Use scrot to take a screenshot
        subprocess.run(["scrot", output_path, "-d", "0", "-z"], env=env, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to capture screenshot: {e}")
