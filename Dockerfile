# Use a base image with dynamic platform support
FROM --platform=$TARGETPLATFORM python:3.11

# Declare platform argument
ARG TARGETPLATFORM

# Print the TARGETPLATFORM value during the build process
RUN echo "Building for platform: $TARGETPLATFORM"

# Below adjustments for linux/arm/v7
# Install system dependencies and Rust for arm/v7 and arm64
RUN if [ "$TARGETPLATFORM" = "linux/arm/v7" ] ; then \
      apt-get update && apt-get install -y \
      curl build-essential \
      && curl https://sh.rustup.rs -sSf | sh -s -- -y \
      && . /root/.cargo/env; \
    else \
      echo "Skipping Rust installation for $TARGETPLATFORM"; \
    fi \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Rust environment path if needed
RUN if [ "$TARGETPLATFORM" = "linux/arm/v7" ] ; then \
      echo 'export PATH="/root/.cargo/bin:$PATH"' >> /etc/environment; \
    fi

# Upgrade pip and install Python dependencies from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Set working directory
WORKDIR /app

# Copy application code
COPY src /app

# Run the script
CMD ["python", "/app/entrypoint.py"]
