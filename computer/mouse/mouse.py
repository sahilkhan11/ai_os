import subprocess
import os

def _run_xdotool(args: list):
    display = os.environ.get("DISPLAY", ":99")
    env = os.environ.copy()
    env["DISPLAY"] = display
    subprocess.run(["xdotool"] + args, env=env, check=True)

def move_mouse(x: int, y: int):
    _run_xdotool(["mousemove", str(x), str(y)])

def click(button: int = 1):
    _run_xdotool(["click", str(button)])

def double_click(button: int = 1):
    _run_xdotool(["click", "--repeat", "2", str(button)])

def scroll(direction: str, amount: int = 1):
    """direction: 'up' or 'down'"""
    btn = 4 if direction == "up" else 5
    _run_xdotool(["click", "--repeat", str(amount), str(btn)])

def drag(from_x: int, from_y: int, to_x: int, to_y: int, button: int = 1):
    _run_xdotool(["mousemove", str(from_x), str(from_y), "mousedown", str(button), "mousemove", str(to_x), str(to_y), "mouseup", str(button)])
