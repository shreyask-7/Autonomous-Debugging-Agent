import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [repoPath, setRepoPath] = useState("tests/dummy_repo");
  const [issue, setIssue] = useState(
    "Fix ZeroDivision in calculator.py so that divide(10, 0) returns None.",
  );
  const [runId, setRunId] = useState(null);
  const [steps, setSteps] = useState([]);
  const [isRunning, setIsRunning] = useState(false);

  const eventSourceRef = useRef(null);

  const startRun = async (e) => {
    e.preventDefault();
    setSteps([]);
    setIsRunning(true);

    const response = await fetch("http://localhost:8000/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repo_path: repoPath,
        issue_description: issue,
      }),
    });

    const data = await response.json();
    setRunId(data.id);

    const streamUrl = `http://localhost:8000/api/runs/${data.id}/stream`;
    eventSourceRef.current = new EventSource(streamUrl);

    eventSourceRef.current.onmessage = (event) => {
      const stepData = JSON.parse(event.data);
      setSteps((prev) => [...prev, stepData]);

      if (stepData.status === "finished" || stepData.status === "error") {
        eventSourceRef.current.close();
        setIsRunning(false);
      }
    };

    eventSourceReg.current.onerror = () => {
      console.error("SSE connect error");
      eventSourceRef.current.close();
      setIsRunning(false);
    };
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="container">
      <h1>Autonomous Debugger</h1>

      <form onSubmit={startRun} className="setup-form">
        <input
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          placeholder="Repository Path"
          disabled={isRunning}
        />
        <textarea
          value={issue}
          onChange={(e) => setIssue(e.target.value)}
          placeholder="Bug Report"
          disabled={isRunning}
        />
        <button type="submit" disabled={isRunning}>
          {isRunning ? "Agent is Running..." : "Start Debugging"}
        </button>
      </form>

      <div className="terminal">
        {steps.map((step, index) => (
          <div key={index} className="step-block">
            <p className="thought">
              <strong>🤔 Thought:</strong> {step.thought}
            </p>
            {step.tool && (
              <div className="action">
                <p>
                  <strong>🔧 Tool:</strong> {step.tool}
                </p>
                <pre className="output">{step.output}</pre>
              </div>
            )}
            {step.summary && (
              <p className="success">
                <strong>✅ Finished:</strong> {step.summary}
              </p>
            )}
            {step.error && (
              <p className="error">
                <strong>❌ Error:</strong> {step.error}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
