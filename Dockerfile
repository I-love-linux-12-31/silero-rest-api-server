FROM fedora:latest

RUN dnf install -y python3 python3-pip python3-virtualenv bash

RUN dnf install -y ffmpeg-free python3-ffmpeg-python

WORKDIR /app

COPY requirements.txt .

RUN python3 -m venv venv

ENV PATH="/app/venv/bin:$PATH"
RUN . venv/bin/activate && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN . venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5500

CMD ["bash", "run_server.sh"]