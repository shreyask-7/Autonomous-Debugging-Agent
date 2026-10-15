import json
import time
import traceback
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any
from google import genai
from google.genai import types
from sqlmodel import Session
from app.config import settings
from app.tools.registry import ToolRegistry
from app.engine.sandbox import SandboxManager
from app.engine.prompts import SYSTEM_PROMPT
from app.models.schemas import AgentRun, AgentStep, RunStatus, StepType

class AgentRuntime:
    def __init__(self, repo_path: str, bug_report: str, db: Session, max_iterations: int = 15):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.sandbox = SandboxManager()
        self.registry = ToolRegistry(self.sandbox)
        self.db = db
        self.max_iterations = max_iterations
        self.repo_path = repo_path

        self.run_record = AgentRun(
            repo_name=repo_path.split("/")[-1] if "/" in repo_path else repo_path.split("\\")[-1],
            issue_description=bug_report,
            status=RunStatus.RUNNING,
            created_at = datetime.now(timezone.utc)
        )
        self.db.add(self.run_record)
        self.db.commit()
        self.db.refresh(self.run_record)
        
        self.messages: List[Dict[str, str]] = [
            {"role": "user", "content": bug_report}
        ]
        self.step_count = 0
        self.action_history = []

    def _fail_run(self, error_message: str) -> Dict[str, Any]:
        self.run_record.status = RunStatus.FAILED
        self.run_record.completed_at = datetime.now(timezone.utc)
        self.run_record.iterations = self.step_count
        self.db.commit()
        return {"status": "error", "error": error_message}
        
    def step(self) -> Dict[str, Any]:
        self.step_count += 1
        if self.step_count > self.max_iterations:
            return self._fail_run(f"Budget exhausted: Reached maximum limit of {self.max_iterations} iterations without resolving the bug.")
        
        formatted_contents = [
            types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])]) 
            for m in self.messages
        ]

        max_retries = 5
        response = None
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=formatted_contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    return self._fail_run(f"LLM API failure after {max_retries} attempts: {str(e)}")

                sleep_time = (2 ** attempt)
                print(f"⚠️ API error ({str(e)}), backing off for {sleep_time} seconds...")
                time.sleep(sleep_time)

        try:
            decision = json.loads(response.text)
            self.messages.append({"role": "model", "content": response.text})
        except json.JSONDecodeError:
            return self._fail_run(f"Agent generated invalid JSON: {response.text}")

        tool_name = decision.get("tool_name")
        tool_args = decision.get("tool_arguments", {})
        thought = decision.get("thought_process", "")

        if tool_name == "finish_run":
            self.run_record.status = RunStatus.SUCCESS
            self.run_record.completed_at = datetime.now(timezone.utc)
            self.run_record.iterations = self.step_count
            self.db.commit()
            return {"status": "finished", "thought": thought, "summary": tool_args.get("summary", "")}

        action_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"
        
        if action_signature in self.action_history:
            tool_output = "SYSTEM ERROR: You just executed this exact action with these exact arguments. Re-evaluate your hypothesis and try a different approach. Do not repeat failed actions."
            duration_ms = 0
        else:
            self.action_history.append(action_signature)
            if tool_name == "write_file":
                self.action_history.clear()
            start_time = time.time()
            try:
                tool_output = self.registry.dispatch(tool_name, tool_args)
            except Exception as e:
                tool_output = f"SYSTEM EXCEPTION during tool execution:\n{traceback.format_exc()}"
            duration_ms = int((time.time() - start_time) * 1000)

        observation = f"Tool '{tool_name}' executed.\nOutput:\n{tool_output}"
        self.messages.append({"role": "user", "content": observation})

        step_record = AgentStep(
            run_id = self.run_record.id,
            step_number = self.step_count,
            step_type = StepType.TOOL_EXECUTION,
            tool_name = tool_name,
            tool_input = tool_args,
            tool_output = tool_output,
            duration_ms = duration_ms,
            created_at = datetime.now(timezone.utc)
        )
        self.db.add(step_record)
        self.db.commit()

        return {
            "status": "running",
            "thought": thought,
            "tool": tool_name,
            "args": tool_args,
            "output": tool_output
        }

    async def run_stream(self):
        self.sandbox.start_container(self.repo_path)
        try:
            while True: 
                step_result = await asyncio.to_thread(self.step)
                yield step_result
                if step_result["status"] in ("finished", "error"):
                    break
        finally:
            self.sandbox.stop_container()