# Use an official lightweight Python image for ARMv7
FROM arm32v7/python:3.11

# Upgrade pip and install Python dependencies
COPY requirements.txt /usr/src/
RUN \
    pip3 install --upgrade pip \
    pip3 install \
        -r /usr/src/requirements.txt \
    && rm -f /usr/src/requirements.txt

# Set working directory
WORKDIR /app

# Copy the script into the container
COPY script.py /app/script.py

# Run the script
CMD ["python", "/app/script.py"]