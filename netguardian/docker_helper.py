"""NetGuardian Unix Socket Docker API Helper

Provides zero-dependency interaction with the local Docker daemon socket
(/var/run/docker.sock) using Python's built-in socket library.
Allows container isolation and dynamic execution commands.
"""

from __future__ import annotations

import json
import socket
import os
from typing import Any

DOCKER_SOCKET_PATH = "/var/run/docker.sock"


def _unix_socket_request(method: str, path: str, payload: dict | None = None) -> tuple[int, dict | str]:
    """Sends a raw HTTP request over the Unix Socket to the Docker daemon."""
    if not os.path.exists(DOCKER_SOCKET_PATH):
        raise FileNotFoundError(f"Docker socket not found at {DOCKER_SOCKET_PATH}")

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.connect(DOCKER_SOCKET_PATH)
        
        body = ""
        if payload is not None:
            body = json.dumps(payload)
            
        content_length_header = f"Content-Length: {len(body)}\r\n" if body else ""
        content_type_header = "Content-Type: application/json\r\n" if body else ""
        
        request = (
            f"{method} {path} HTTP/1.1\r\n"
            f"Host: localhost\r\n"
            f"{content_type_header}"
            f"{content_length_header}"
            f"Connection: close\r\n\r\n"
            f"{body}"
        )
        s.sendall(request.encode("utf-8"))
        
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()
        
        resp_str = response.decode("utf-8", errors="ignore")
        parts = resp_str.split("\r\n\r\n", 1)
        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ""
        
        # Parse Status Code
        status_line = header_part.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1])
        
        try:
            parsed_body = json.loads(body_part)
            return status_code, parsed_body
        except json.JSONDecodeError:
            return status_code, body_part
            
    except Exception as exc:
        if s:
            s.close()
        raise exc


def disconnect_container_from_network(network_name: str, container_name: str) -> bool:
    """Disconnects a container physically from a specified Docker network."""
    path = f"/networks/{network_name}/disconnect"
    payload = {"Container": container_name, "Force": True}
    try:
        status_code, _ = _unix_socket_request("POST", path, payload)
        # 200 OK or 204 No Content are success states
        return status_code in (200, 204)
    except Exception as exc:
        print(f"[DockerHelper] Failed to disconnect container: {exc}")
        return False


def is_container_connected_to_network(network_name: str, container_name: str) -> bool:
    """Checks if a container is currently attached to a specified Docker network."""
    path = f"/containers/{container_name}/json"
    try:
        status_code, data = _unix_socket_request("GET", path)
        if status_code != 200 or not isinstance(data, dict):
            return False
        networks = data.get("NetworkSettings", {}).get("Networks", {})
        return network_name in networks
    except Exception as exc:
        print(f"[DockerHelper] Failed to inspect container network: {exc}")
        return False


def execute_command_in_container(container_name: str, command_list: list[str]) -> tuple[bool, str]:
    """Executes a command inside a running container using Docker Exec API."""
    create_path = f"/containers/{container_name}/exec"
    create_payload = {
        "AttachStdout": True,
        "AttachStderr": True,
        "Cmd": command_list
    }
    try:
        # 1. Create Exec Instance
        status_code, data = _unix_socket_request("POST", create_path, create_payload)
        if status_code != 201 or not isinstance(data, dict):
            return False, f"Failed to create exec instance (Status: {status_code})"
            
        exec_id = data.get("Id")
        if not exec_id:
            return False, "Failed to retrieve Exec ID from response"
            
        # 2. Start Exec Instance
        start_path = f"/exec/{exec_id}/start"
        start_payload = {"Detach": False, "Tty": False}
        start_status, start_data = _unix_socket_request("POST", start_path, start_payload)
        
        output = str(start_data)
        return start_status == 200, output
        
    except Exception as exc:
        print(f"[DockerHelper] Failed to execute command inside container: {exc}")
        return False, str(exc)
