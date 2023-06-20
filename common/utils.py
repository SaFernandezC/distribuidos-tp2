import os
import re

def get_docker_id():
    # Get the process ID of the current running script
    pid = os.getpid()

    # Get the container ID from the cgroup file of the process
    cgroup_file = f"/proc/{pid}/cgroup"
    with open(cgroup_file, 'r') as file:
        content = file.read()

    # Extract the container ID from the cgroup file
    match = re.search(r"/docker/([a-f0-9]+)", content)
    if match:
        container_id = match.group(1)
        return container_id

    return None