import os
from huggingface_hub import snapshot_download

def download():
    print("Downloading OmniParser weights from HuggingFace...")
    # Downloading to the expected weights directory for OmniParser v2.0
    snapshot_download(
        repo_id="microsoft/OmniParser-v2.0",
        local_dir="/opt/OmniParser/weights",
        local_dir_use_symlinks=False,
        ignore_patterns=["*.md", "*.txt"]
    )
    print("Download complete.")

if __name__ == "__main__":
    download()
