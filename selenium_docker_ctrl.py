import docker
import argparse
import subprocess

def check_docker_installed():
    try:
        x = subprocess.check_output(['docker', '--version'], stderr=subprocess.STDOUT)
        print(f"Great! I see you've already installed {x.decode('utf-8')}") # Print the Docker version if installed
    except FileNotFoundError as e:
        print(e)
        print('\nDocker is not installed. Please install Docker at https://docs.docker.com/get-docker/')
        raise

def start_container(client, image_name, container_name):
    # Check if the Docker image exists locally
    try:
        client.images.get(image_name)
        print(f"\nImage {image_name} found locally.")
    except docker.errors.ImageNotFound:
        print(f"\nImage not found locally, now pulling Docker image: {image_name}")
        client.images.pull(image_name)
        print(f"Image {image_name} pulled successfully.")
    except Exception as e:
        print(f"In start_container/image: {e}")

    # Check if the Docker container exists
    try:
        container = client.containers.get(container_name)
        print(f"Starting existing Docker container: {container_name}")
        container.start()
        print(f"Container {container_name} started successfully.")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found. Now starting a new Docker container {container_name} from image {image_name}")
        container = client.containers.run(
            image_name,
            name=container_name,
            detach=True,
            ports={'4444/tcp': 4444, '7900/tcp': 7900},
            shm_size="2g"
        )
        print(f"Container {container_name} started successfully.")
    except Exception as e:
        print(f"In start_container/container: {e}")

def stop_container(client, container_name):
    # Check if the Docker container exists
    try:
        container = client.containers.get(container_name)
        print(f"\nStopping existing Docker container: {container_name}")
        container.stop()
        print(f"Container {container_name} stopped successfully.")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found, cannot stop.")
    except Exception as e:
        print(f"In stop_container: {e}")

def selenium_docker_ctrl(action):
    client = docker.from_env()
    image_name = "selenium/standalone-chrome"
    container_name = "selenium-chrome-container"
    if action=='start':
        start_container(client, image_name, container_name)
    elif action=='stop':
        stop_container(client, container_name)
    else:
        raise ValueError("selenium_docker_ctrl(action), where action should be either 'start' or 'stop'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start or stop a Docker container for Selenium Chrome.")
    parser.add_argument('action', choices=['start', 'stop'], help="Action to perform on the Docker container.")
    args = parser.parse_args()

    selenium_docker_ctrl(args.action)