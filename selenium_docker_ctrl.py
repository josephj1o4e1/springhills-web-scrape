import docker
import argparse
import subprocess
from utils import setup_logger

logger = setup_logger()

def check_docker_installed():
    try:
        x = subprocess.check_output(['docker', '--version'], stderr=subprocess.STDOUT)
        print(f"Great! I see you've already installed {x.decode('utf-8')}") # Print the Docker version if installed
    except FileNotFoundError as e:
        logger.error(e)
        print('\nDocker is not installed. Please install Docker at https://docs.docker.com/get-docker/')
        raise

def start_container(client, image_name, container_name):
    # Check if the Docker image exists locally
    try:
        client.images.get(image_name)
        logger.info(f"Image {image_name} found locally.")
    except docker.errors.ImageNotFound:
        logger.info(f"\nImage not found locally, now pulling Docker image: {image_name}")
        client.images.pull(image_name)
        logger.info(f"Image {image_name} pulled successfully.")

    # Check if the Docker container exists
    try:
        container = client.containers.get(container_name)
        logger.info(f"Starting existing Docker container: {container_name}")
        container.start()
        logger.info(f"Container {container_name} started successfully.")
    except docker.errors.NotFound:
        logger.info(f"\nContainer {container_name} not found. Now starting a new Docker container {container_name} from image {image_name}")
        container = client.containers.run(
            image_name,
            name=container_name,
            detach=True,
            ports={'4444/tcp': 4444, '7900/tcp': 7900},
            shm_size="2g"
        )
        logger.info(f"Container {container_name} started successfully.")

def stop_container(client, container_name):
    # Check if the Docker container exists
    try:
        container = client.containers.get(container_name)
        logger.info(f"Stopping existing Docker container: {container_name}")
        container.stop()
        logger.info(f"Container {container_name} stopped successfully.")
    except docker.errors.NotFound:
        logger.info(f"\nContainer {container_name} not found, cannot stop.")
        raise

def selenium_docker_ctrl(action):
    client = docker.from_env()
    image_name = "selenium/standalone-chrome"
    container_name = "selenium-chrome-container"
    if action=='start':
        print('Starting selenium docker...')
        start_container(client, image_name, container_name)
    elif action=='stop':
        print('Stopping selenium docker...')
        stop_container(client, container_name)
    else:
        raise ValueError("selenium_docker_ctrl(action), where action should be either 'start' or 'stop'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start or stop a Docker container for Selenium Chrome.")
    parser.add_argument('action', choices=['start', 'stop'], help="Action to perform on the Docker container.")
    args = parser.parse_args()

    selenium_docker_ctrl(args.action)