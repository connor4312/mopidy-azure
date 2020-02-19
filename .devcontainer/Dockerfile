FROM python:latest

# Mopdiy OS-level dependencies
RUN apt update
RUN apt install -y \
    python3-gst-1.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    pkg-config \
    libcairo2-dev \
    gcc \
    python3-dev \
    libgirepository1.0-dev

# Setting up virtual environment
RUN pip install tox
RUN cd /workspace && tox || echo "Initial tox failed"
RUN echo 'PATH="/workspace/.tox/py38/bin:$PATH"' >> ~/.bashrc
ENV PATH="/workspace/.tox/py38/bin:$PATH"

# Install dependencies for the local Mopidy system
RUN pip install gobject PyGObject
