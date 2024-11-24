# Use an official lightweight Python image
FROM arm32v7/python:3.11

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y \
    curl build-essential \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . /root/.cargo/env \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the Rust environment path for subsequent commands
ENV PATH="/root/.cargo/bin:$PATH"

# Install dependencies
RUN pip install --upgrade pip
RUN pip install tinytuya paho-mqtt

# Set working directory
WORKDIR /app

# Copy the script into the container
COPY script.py /app/script.py

# Run the script
CMD ["python", "/app/script.py"]