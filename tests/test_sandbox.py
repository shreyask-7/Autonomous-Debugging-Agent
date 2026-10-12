import os
from app.engine.sandbox import SandboxManager

def test_sandbox_lifecycle():
    sandbox = SandboxManager()
    dummy_repo_dir = os.path.abspath("tests/dummy_repo")

    print("\n[1] Starting Docker sandbox container...")
    container_id = sandbox.start_container(dummy_repo_dir)
    print(f"Container started with ID: {container_id[:12]}")

    try:
        print("[2] Listing workspace directory inside container...")
        exit_code, output = sandbox.execute_command("ls -la")
        print(f"Exit Code: {exit_code}\nOutput:\n{output}")

        print("[3] Running pytest (or python -m unittest) inside container...")
        # Since python:3.11-slim doesn't have pytest by default, let's test running python directly
        exit_code, output = sandbox.execute_command("python -m unittest test_calculator.py")
        print(f"Exit Code: {exit_code}\nOutput:\n{output}")

    finally:
        print("[4] Cleaning up sandbox...")
        sandbox.stop_container()
        print("Sandbox destroyed successfully.")

if __name__ == "__main__":
    test_sandbox_lifecycle()