import os
from sqlmodel import Session
from app.models.database import engine
from app.engine.loop import AgentRuntime

def test_autonomous_debugging():
    dummy_repo_dir = os.path.abspath("tests/dummy_repo")
    
    bug_report = (
        "Bug Report: The test suite is failing. `test_calculator.py` expects `divide(10, 0)` "
        "to return `None`, but `calculator.py` is throwing a `ZeroDivisionError`. "
        "Please explore the repository, run the tests to verify the error, modify `calculator.py` "
        "to fix the bug, run the tests again to ensure they pass, and then call `finish_run`."
    )

    print("\n[1] Connecting to Database and Starting Docker sandbox...")
    # Initialize the database session
    with Session(engine) as db_session:
        agent = AgentRuntime(repo_path=dummy_repo_dir, bug_report=bug_report, db=db_session)
        agent.sandbox.start_container(dummy_repo_dir)
        
        print(f"[*] Created AgentRun record with ID: {agent.run_record.id}")
        print("[2] Starting Agent Loop...\n")
        
        try:
            for iteration in range(1, 11):
                print(f"--- Iteration {iteration} ---")
                result = agent.step()
                
                if result["status"] == "error":
                    print(f"[!] ERROR: {result.get('error')}")
                    break

                print(f"🤔 THOUGHT: {result.get('thought')}")
                
                if result["status"] == "finished":
                    print(f"✅ FINISHED: {result.get('summary')}")
                    break
                    
                print(f"🔧 TOOL: {result.get('tool')}")
                # print(f"📥 ARGS: {result.get('args')}")
                # print(f"📤 OUTPUT (truncated for readability): {str(result.get('output'))[:100]}...\n")

        finally:
            print("\n[3] Cleaning up sandbox...")
            agent.sandbox.stop_container()
            print("Sandbox destroyed.")

if __name__ == "__main__":
    test_autonomous_debugging()