# Integration Tests

This directory contains scripts meant to be run manually by a human against the live AI container to verify end-to-end functionality.

## Test Primitives (`test_primitives.py`)

This script verifies that the lowest-level primitives (screen capture, mouse, keyboard) work by opening a text editor, typing some text, and taking before/after screenshots.

### How to Run

1. Ensure the `ai_computer_runtime` container is running (`docker compose up -d`).
2. Execute the script inside the container:
   ```bash
   docker exec -it ai_computer_runtime python3 /app/tests/integration/test_primitives.py
   ```
3. Check the `workspace/` directory on your host machine for the `screenshot_before.png` and `screenshot_after.png` files to visually confirm it worked!
