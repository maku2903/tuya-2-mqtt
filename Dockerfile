# Stage 1: Builder
# Use a base image with dynamic platform support
FROM --platform=$TARGETPLATFORM python:3.13.0-slim-bullseye as builder

# Declare platform argument
ARG TARGETPLATFORM

# Print the TARGETPLATFORM value during the build process
RUN echo "Building for platform: $TARGETPLATFORM"

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    openssl \
    libffi-dev \
    libssl-dev \
    pkg-config \
    python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Rust via rustup
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:$PATH"

# Set environment variables for OpenSSL
# ENV OPENSSL_DIR=/usr/lib/x86_64-linux-gnu
# ENV PKG_CONFIG_PATH=/usr/lib/x86_64-linux-gnu/pkgconfig
ENV RUST_BACKTRACE=1

# Upgrade pip and install Python dependencies from requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install --prefix=/install -r /tmp/requirements.txt

# Stage 2: Final Image
FROM --platform=$TARGETPLATFORM python:3.13.0-slim-bullseye

# Declare platform argument
ARG TARGETPLATFORM

# Print the TARGETPLATFORM value during the runtime stage
RUN echo "Running for platform: $TARGETPLATFORM"

# Copy Python dependencies from builder stage
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application code
COPY src /app

# Run the script
CMD ["python", "/app/entrypoint.py"]
