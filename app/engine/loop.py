import json
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from app.config import settings
from app.tools.registry import ToolRegistry
from app.engine.sandbox import SandboxManager
from app.engine.prompts import SYSTEM_PROMPT

class AgentRuntime:
    def __init__(self, repo_path: str):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.sandbox = SandboxManager()
        self.registry = ToolRegistry(self.sandbox)
        self.repo_path = repo_path
        
        self.messages: List[Dict[str, str]] = [
            {"role": "user", "content": SYSTEM_PROMPT}
        ]

    def step(self) -> Dict[str, Any]:
        formatted_contents = [
            types.Content(role=m["role"], parts=[types.Part.from_text(text=m["content"])]) 
            for m in self.messages
        ]

        max_retries = 5
        response = None
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=formatted_contents,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                break
            except Exception as e:
                error_str = str(e)
                if "503" in error_str and attempt < max_retries - 1:
                    print(f"⚠️ API busy (503), retrying in 3 seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(3)
                elif "429" in error_str and attempt < max_retries - 1:
                    print(f"⏳ Rate limit exceeded (429), pausing for 15 seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(15)
                else:
                    raise e

        try:
            decision = json.loads(response.text)
            self.messages.append({"role": "model", "content": response.text})
        except json.JSONDecodeError:
            error_msg = f"Failed to parse JSON. Raw output: {response.text}"
            self.messages.append({"role": "user", "content": error_msg})
            return {"status": "error", "error": "Invalid JSON", "raw": response.text}

        tool_name = decision.get("tool_name")
        tool_args = decision.get("tool_arguments", {})
        thought = decision.get("thought_process", "")

        if tool_name == "finish_run":
            return {"status": "finished", "thought": thought, "summary": tool_args.get("summary", "")}

        tool_output = self.registry.dispatch(tool_name, tool_args)
        
        observation = f"Tool '{tool_name}' executed.\nOutput:\n{tool_output}"
        self.messages.append({"role": "user", "content": observation})

        return {
            "status": "running",
            "thought": thought,
            "tool": tool_name,
            "args": tool_args,
            "output": tool_output
        }