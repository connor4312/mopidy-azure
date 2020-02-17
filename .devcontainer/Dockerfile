FROM python:latest

# Mopdiy OS-level dependencies
RUN apt install \
    python3-gst-1.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools

# Setting up virtual environment
RUN pip install tox
RUN tox || echo "Initial tox failed"
ENV PATH="/home/vsonline/workspace/.tox/py38/bin:$PATH"

# Install dependencies for the local Mopidy system
RUN pip install gobject PyGObject
