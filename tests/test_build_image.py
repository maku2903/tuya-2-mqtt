import subprocess
import pytest

# Full path to the Docker binary
DOCKER_BINARY = "/usr/bin/docker"  # Adjust this path for your environment

# Architectures to test
PLATFORMS = ["linux/amd64", "linux/arm64", "linux/arm/v7"]

# Base image tag for testing
IMAGE_NAME = "tuya-2-mqtt-build-test"

@pytest.mark.parametrize("platform", PLATFORMS)
def test_docker_build(platform):
    """
    Test building the Docker image for each specified architecture.
    """
    tag = f"{IMAGE_NAME}:{platform.replace('/', '_')}"  # Replace "/" in platform for valid tag
    command = [
        DOCKER_BINARY, "buildx", "build",
        "--no-cache",  # Ensure a fresh build for every test
        "--platform", platform,  # Target platform
        "-t", tag,  # Image tag
        "--load",  # Load the image into the local Docker daemon
        "."
    ]

    try:
        # Run the Docker build command
        print(f"Building for platform: {platform}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        # Output logs for debugging if needed
        print(result.stdout)
        print(result.stderr)

    except subprocess.CalledProcessError as e:
        pytest.fail(f"Build failed for platform {platform}\n{e.stderr}")
