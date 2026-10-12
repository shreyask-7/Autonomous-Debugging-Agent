import os
import docker
from docker.models.containers import Container
from typing import Tuple, Optional

class SandboxManager:
  def __init__(self, image: str = "python:3.11-slim"):
    self.image = image
    self.client = docker.from_env()
    self.container: Optional[Container] = None

  def start_container(self, host_repo_path: str) -> str:
    abs_repo_path = os.path.abspath(host_repo_path)
    try:
      self.client.images.get(self.image)
    except docker.errors.ImageNotFound:
      print(f"Pulling sandbox image: {self.image}...")
      self.client.images.pull(self.image)

    self.container = self.client.containers.run(
      image=self.image,
      command="tail -f /dev/null",
      volumes={
        abs_repo_path: {
          "bind": "/workspace",
          "mode": "rw"
        }
      },
      working_dir="/workspace",
      detach=True,
      remove=False
    )
    return self.container.id

  def execute_command(self, cmd: str, timeout_seconds: int = 30) -> Tuple[int, str]:
    if not self.container:
      raise RuntimeError("Sandbox container is not running.")
    exec_instance = self.container.exec_run(
      cmd=["sh", "-c", cmd],
      workdir="/workspace",
      demux=False
    )
    exit_code = exec_instance.exit_code
    output = exec_instance.output.decode("utf-8", errors="replace") if exec_instance.output else ""
    return exit_code, output

  def stop_container(self):
    if self.container:
      try:
        self.container.stop(timeout=5)
        self.container.remove(force=True)
      except Exception as e:
        print(f"Error cleaning up container: {e}")
      finally:
        self.container = None
        