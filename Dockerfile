# Use an official lightweight Python image for ARMv7
FROM python:3.11

# Install Python dependencies
WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt \
  && rm -f /usr/src/requirements.txt

# Set working directory
WORKDIR /app

# Copy the script into the container
COPY script.py /app/script.py

# Run the script
CMD ["python", "/app/script.py"]