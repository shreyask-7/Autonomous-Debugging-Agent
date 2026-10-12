from typing import Dict, Any, List
from app.engine.sandbox import SandboxManager

class ToolRegistry:
  def __init__(self, sandbox: SandboxManager):
    self.sandbox = sandbox

  def list_files(self, directory: str = ".") -> str:
    cmd = f"find {directory} -maxdepth 3 -not -path '*/.*'"
    exit_code, output = self.sandbox.execute_command(cmd)
    return output.strip() if exit_code == 0 else f"Error: {output}"

  def read_files(self, filepath: str) -> str:
    cmd = f"cat {filepath}"
    exit_code, output = self.sandbox.execute_command(cmd)
    return output if exit_code == 0 else f"Error reading file: {output}"

  def search_code(self, pattern: str) -> str:
    cmd = f"grep -rnw '.' -e '{pattern}' --exclude-dir=.*"
    exit_code, output = self.sandbox.execute_command(cmd) 
    if exit_code == 1:
      return "No matches found."
    return output if exit_code == 0 else f"Error searching code: {output}"

  def run_tests(self, test_cmd: str = "python -m unittest") -> str:
    exit_code, output = self.sandbox.execute_command(test_cmd)
    status = "PASSED" if exit_code == 0 else "FAILED"
    return f"[{status} - Exit Code {exit_code}]\n{output}"

  def write_file(self, file_path: str, content: str) -> str:
    escaped_content = content.replace("'", "'\\''")
    cmd = f"printf '%s' '{escaped_content}' > {file_path}"
    exit_code, output = self.sandbox.execute_command(cmd)
    return "File updated successfully." if exit_code == 0 else f"Error writing file: {output}"

  def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> str:
    tools = {
      "list_files": lambda args: self.list_files(args.get("directory", ".")),
      "read_file": lambda args: self.read_files(args.get("filepath", "")),
      "search_code": lambda args: self.search_code(args.get("pattern", "")),
      "run_tests": lambda args: self.run_tests(args.get("test_cmd", "python -m unittest")),
      "write_file": lambda args: self.write_file(args.get("filepath", ""), args.get("content", ""))
    }

    if tool_name not in tools:
      return f"Error: Unknown tool '{tool_name}'."
    return tools[tool_name](arguments)