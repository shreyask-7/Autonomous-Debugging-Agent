import os
from app.engine.loop import AgentRuntime

def test_autonomous_debugging():
    dummy_repo_dir = os.path.abspath("tests/dummy_repo")
    
    # 1. Initialize the runtime
    agent = AgentRuntime(repo_path=dummy_repo_dir)
    
    print("\n[1] Starting Docker sandbox container...")
    agent.sandbox.start_container(dummy_repo_dir)
    
    # 2. Provide the explicit bug report
    bug_report = (
        "Bug Report: The test suite is failing. `test_calculator.py` expects `divide(10, 0)` "
        "to return `None`, but `calculator.py` is throwing a `ZeroDivisionError`. "
        "Please explore the repository, run the tests to verify the error, modify `calculator.py` "
        "to fix the bug, run the tests again to ensure they pass, and then call `finish_run`."
    )
    agent.messages.append({"role": "user", "content": bug_report})

    print("[2] Starting Agent Loop...\n")
    
    try:
        # 3. The Execution Loop (Max 10 iterations to prevent infinite loops)
        for iteration in range(1, 11):
            print(f"--- Iteration {iteration} ---")
            
            result = agent.step()
            
            if result["status"] == "error":
                print(f"[!] ERROR: {result.get('error')}")
                print(f"Raw Output: {result.get('raw')}")
                break

            print(f"🤔 THOUGHT: {result.get('thought')}")
            
            if result["status"] == "finished":
                print(f"✅ FINISHED: {result.get('summary')}")
                break
                
            print(f"🔧 TOOL: {result.get('tool')}")
            print(f"📥 ARGS: {result.get('args')}")
            
            # Truncate output for terminal readability
            output = str(result.get('output', ''))
            display_output = output if len(output) < 300 else output[:300] + "\n...[truncated]"
            print(f"📤 OUTPUT:\n{display_output}\n")

    finally:
        print("\n[3] Cleaning up sandbox...")
        agent.sandbox.stop_container()
        print("Sandbox destroyed.")

if __name__ == "__main__":
    test_autonomous_debugging()