# Use an official lightweight Python image for ARMv7
FROM arm32v7/python:3.11

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && echo 'export PATH=/root/.cargo/bin:$PATH' >> /root/.bashrc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Add Rust target for ARMv7
RUN export PATH=/root/.cargo/bin:$PATH && rustup target add armv7-unknown-linux-gnueabihf

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install tinytuya paho-mqtt

# Set the Rust environment path for subsequent commands
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy the script into the container
COPY script.py /app/script.py

# Run the script
CMD ["python", "/app/script.py"]