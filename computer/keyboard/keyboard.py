import subprocess
import os

def _run_xdotool(args: list):
    display = os.environ.get("DISPLAY", ":99")
    env = os.environ.copy()
    env["DISPLAY"] = display
    subprocess.run(["xdotool"] + args, env=env, check=True)

def type_text(text: str, delay_ms: int = 12):
    _run_xdotool(["type", "--delay", str(delay_ms), text])

def press_key(key: str):
    _run_xdotool(["key", key])

def hotkey(keys: str):
    """keys like 'ctrl+c'"""
    _run_xdotool(["key", keys])
