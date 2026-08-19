FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV RESOLUTION=1280x800x24

# Install base utilities and desktop environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    git \
    xfce4 \
    xfce4-terminal \
    xvfb \
    x11vnc \
    python3 \
    python3-numpy \
    python3-numpy \
    scrot \
    mousepad \
    xdotool \
    dbus-x11 \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt --break-system-packages

# Clone OmniParser and install its dependencies (ignoring torch/vision as we have CPU versions)
RUN git clone https://github.com/microsoft/OmniParser.git /opt/OmniParser \
    && pip3 install -r /opt/OmniParser/requirements.txt --break-system-packages || true \
    && sed -i 's/show_log=False,//g; s/max_batch_size=1024,//g; s/max_batch_size=1024//g; s/use_dilation=True,//g; s/use_dilation=False,//g; s/use_dilation=True//g; s/use_dilation=False//g; s/use_gpu=False,//g; s/det_db_score_mode='\''slow'\'',//g; s/rec_batch_num=1024//g' /opt/OmniParser/util/utils.py \
    && sed -i 's/ocr_bbox = None/ocr_bbox = []/g' /opt/OmniParser/util/utils.py \
    && sed -i 's/zip(ocr_bbox, ocr_text)/zip(ocr_bbox or [], ocr_text or [])/g' /opt/OmniParser/util/utils.py \
    && sed -i 's/            else:\n                filtered_boxes.append(box1)/            else:\n                filtered_boxes.append(box1_elem)/g' /opt/OmniParser/util/utils.py

# Download OmniParser weights
COPY desktop/docker/download_weights.py /tmp/download_weights.py
RUN python3 /tmp/download_weights.py

# Install noVNC
RUN git clone --depth 1 https://github.com/novnc/noVNC.git /opt/novnc \
    && git clone --depth 1 https://github.com/novnc/websockify /opt/novnc/utils/websockify

# Install Google Chrome (Stable)
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy startup script
COPY desktop/linux/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Create workspace directory
RUN mkdir -p /workspace
WORKDIR /workspace

EXPOSE 8080

CMD ["/entrypoint.sh"]
