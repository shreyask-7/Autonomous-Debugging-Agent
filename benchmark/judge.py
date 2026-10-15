import os
import json
import asyncio
import subprocess
import shutil
from pathlib import Path
from sqlmodel import Session

from app.engine.loop import AgentRuntime
from app.models.database import engine
from app.models.schemas import RunStatus


async def run_evaluation_suite():
  tasks_file = Path("benchmark/tasks.json")
  with open(tasks_file, "r") as f:
    tasks = json.load(f)

  workspaces_base = Path("benchmark/workspaces").resolve()
  workspaces_base.mkdir(parents=True, exist_ok=True)

  with Session(engine) as db:
    for task in tasks:
      print(f"[*] Starting Evaluation: {task['task_id']}")
      workspace_dir = workspaces_base / task['task_id']

      prepare_workspace(task['repo_url'], task['commit_hash'], workspace_dir, task['setup_commands'])

      agent = AgentRuntime(
        repo_path=str(workspace_dir),
        bug_report=task['issue_description'],
        db=db,
        max_iterations=15
      )

      print(f"[*] Agent is running...")

      async for step in agent.run_stream():
        if step.get("status") == "running":
            print(f"\n--- Iteration ---")
            print(f"THOUGHT: {step.get('thought')}")
            print(f"ACTION: {step.get('tool')} {step.get('args')}")
        elif step.get("status") == "error":
            print(f"\n[!] ERROR: {step.get('error')}")
            break
        elif step.get("status") == "finished":
            print(f"\n--- Final Decision ---")
            print(f"THOUGHT: {step.get('thought')}")
            break

      if agent.run_record.status == RunStatus.SUCCESS:
         print("[*] Agent finished. Running verification tests...")
         success = verify_patch(workspace_dir, task['reproduction_test_cmd'], task['regression_test_cmd'])

         agent.run_record.benchmark_success = success
         db.commit()
         print(f"[*] Benchmark Result for {task['task_id']}: {'PASSED' if success else 'FAILED'}")
      else:
         print(f"[*] Agent failed or timed out on {task['task_id']}.")

def prepare_workspace(repo_url: str, commit_hash: str, workspace_dir: Path, setup_cmds: list):
    try:
        if repo_url.startswith("local:"):
            source_dir = repo_url.replace("local:", "")
            if workspace_dir.exists():
                shutil.rmtree(workspace_dir)
            shutil.copytree(source_dir, workspace_dir)
            print(f"    -> Copied local workspace from {source_dir}")
            return

        if not workspace_dir.exists():
            print(f"    -> Cloning {repo_url}...")
            subprocess.run(["git", "clone", repo_url, str(workspace_dir)], check=True, capture_output=True, text=True)
        
        print(f"    -> Checking out commit {commit_hash}...")
        subprocess.run(["git", "checkout", "-f", commit_hash], cwd=workspace_dir, check=True, capture_output=True, text=True)
        subprocess.run(["git", "clean", "-fd"], cwd=workspace_dir, check=True, capture_output=True, text=True)
        
        print("    -> Installing dependencies...")
        for cmd in setup_cmds:
            subprocess.run(cmd.split(), cwd=workspace_dir, check=True, capture_output=True, text=True)
            
    except subprocess.CalledProcessError as e:
        print(f"\n[!] Subprocess Error: {e.cmd}")
        print(f"[!] Git/Pip Output: {e.stderr}")
        raise

def verify_patch(workspace_dir: Path, rep_cmd: str, reg_cmd: str) -> bool:
    print("    -> Running reproduction test...")
    rep_result = subprocess.run(rep_cmd.split(), cwd=workspace_dir, capture_output=True)
    
    if rep_result.returncode != 0:
        print("    -> Reproduction test failed.")
        return False
        
    print("    -> Running full regression suite...")
    reg_result = subprocess.run(reg_cmd.split(), cwd=workspace_dir, capture_output=True)
    
    if reg_result.returncode != 0:
        print("    -> Regression test failed (side effects introduced).")
        return False
        
    return True

if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())