import docker

def main():
    client = docker.from_env()
    image_name = "selenium/standalone-chrome"
    container_name = "selenium-chrome-container"

    # Check if the Docker image exists locally
    try:
        client.images.get(image_name)
        print(f"Image {image_name} found locally.")
    except docker.errors.ImageNotFound:
        print(f"Image not found locally, now pulling Docker image: {image_name}")
        client.images.pull(image_name)
        print(f"Image {image_name} pulled successfully.")

    # Check if the Docker container exists
    try:
        container = client.containers.get(container_name)
        print(f"Starting existing Docker container: {container_name}")
        container.start()
        print(f"Container {container_name} started successfully.")
    except docker.errors.NotFound:
        print(f"Container {container_name} not found, now Running new Docker container from image {image_name} with container name {container_name}")
        container = client.containers.run(
            image_name,
            name=container_name,
            detach=True,
            ports={'4444/tcp': 4444, '7900/tcp': 7900},
            shm_size="2g"
        )
        print(f"Container {container_name} started successfully.")

if __name__ == "__main__":
    main()