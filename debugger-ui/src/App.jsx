import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [repoPath, setRepoPath] = useState(
    "https://github.com/AcePK7/autonomous-debugger.git",
  );
  const [issue, setIssue] = useState(
    "The ShoppingCart checkout method in tests/dummy_repo/cart.py calculates tax incorrectly when a discount code is applied. Tax should be calculated on the discounted subtotal, not the original subtotal.",
  );
  const [runId, setRunId] = useState(null);
  const [steps, setSteps] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [runHistory, setRunHistory] = useState([]);
  const [patch, setPatch] = useState(null);

  const eventSourceRef = useRef(null);
  const terminalEndRef = useRef(null);

  const scrollToBottom = () => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [steps]);

  const fetchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/runs");
      const data = await res.json();
      setRunHistory(data);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const startRun = async (e) => {
    e.preventDefault();
    setSteps([]);
    setPatch(null);
    setIsRunning(true);

    try {
      const response = await fetch("http://localhost:8000/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_path: repoPath,
          issue_description: issue,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setSteps([
          {
            error: `Initialization Failed: ${errorData.detail || "Unknown error"}`,
          },
        ]);
        setIsRunning(false);
        return;
      }

      const data = await response.json();
      setRunId(data.id);
      fetchHistory();

      const streamUrl = `http://localhost:8000/api/runs/${data.id}/stream`;
      eventSourceRef.current = new EventSource(streamUrl);

      eventSourceRef.current.onmessage = (event) => {
        const stepData = JSON.parse(event.data);
        setSteps((prev) => [...prev, stepData]);

        if (stepData.patch) {
          setPatch(stepData.patch);
        }

        if (stepData.status === "finished" || stepData.status === "error") {
          eventSourceRef.current.close();
          setIsRunning(false);
          fetchHistory();
        }
      };

      eventSourceRef.current.onerror = () => {
        console.error("SSE connect error");
        setSteps((prev) => [
          ...prev,
          { error: "Lost connection to the telemetry stream." },
        ]);
        eventSourceRef.current.close();
        setIsRunning(false);
      };
    } catch (err) {
      console.error("Network error:", err);
      setSteps([{ error: "Failed to connect to the backend server." }]);
      setIsRunning(false);
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, []);

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>Run History</h2>
        </div>
        <ul className="history-list">
          {runHistory.map((run) => (
            <li key={run.id} className="history-item">
              <span className="repo-name">
                {run.repo_name.split("/").pop().replace(".git", "")}
              </span>
              <span className={`status-badge ${run.status.toLowerCase()}`}>
                {run.status}
              </span>
            </li>
          ))}
        </ul>
      </aside>

      <main className="main-content">
        <header className="main-header">
          <h1>Autonomous Debugger</h1>
          <p className="subtitle">AI-Powered RCA and Patch Generation</p>
        </header>

        <section className="control-panel">
          <form onSubmit={startRun} className="setup-form">
            <div className="input-group">
              <label>Target Repository URL</label>
              <input
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="https://github.com/org/repo.git"
                disabled={isRunning}
              />
            </div>
            <div className="input-group">
              <label>Issue Description</label>
              <textarea
                value={issue}
                onChange={(e) => setIssue(e.target.value)}
                placeholder="Describe the bug or paste a GitHub issue..."
                disabled={isRunning}
              />
            </div>
            <button
              type="submit"
              className={`submit-btn ${isRunning ? "running" : ""}`}
              disabled={isRunning}
            >
              {isRunning ? "Agent is investigating..." : "Initialize Run"}
            </button>
          </form>
        </section>

        <section
          className="terminal-container"
          style={{
            flex: 1,
            minHeight: "400px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div className="terminal-header">
            <span className="dot red"></span>
            <span className="dot yellow"></span>
            <span className="dot green"></span>
            <span className="terminal-title">Agent Runtime Telemetry</span>
          </div>
          <div className="terminal-window">
            {steps.length === 0 && !isRunning && (
              <p className="terminal-placeholder">
                Awaiting target repository configuration...
              </p>
            )}
            {steps.map((step, index) => (
              <div key={index} className="log-entry">
                {step.thought && (
                  <div className="log-line thought">
                    <span className="prefix">SYSTEM:</span> {step.thought}
                  </div>
                )}
                {step.tool && (
                  <div className="log-line action">
                    <span className="prefix">EXEC:</span> {step.tool}
                    {step.output && (
                      <pre className="tool-output">{step.output}</pre>
                    )}
                  </div>
                )}
                {step.summary && (
                  <div className="log-line success">
                    <span className="prefix">RESOLVED:</span> {step.summary}
                  </div>
                )}
                {step.error && (
                  <div className="log-line error">
                    <span className="prefix">FATAL:</span> {step.error}
                  </div>
                )}
              </div>
            ))}
            <div ref={terminalEndRef} />
          </div>
        </section>

        {patch && (
          <section
            className="patch-container"
            style={{
              flexShrink: 0,
              marginTop: "24px",
              backgroundColor: "#18181b",
              border: "1px solid #27272a",
              borderRadius: "12px",
              padding: "20px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "16px",
              }}
            >
              <h3 style={{ fontSize: "16px", color: "#f4f4f5" }}>
                Generated Patch (.patch)
              </h3>
              <button
                onClick={() => navigator.clipboard.writeText(patch)}
                style={{
                  backgroundColor: "#3b82f6",
                  color: "white",
                  border: "none",
                  padding: "8px 16px",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontWeight: "bold",
                }}
              >
                Copy Patch
              </button>
            </div>
            {patch.trim() ? (
              <pre
                style={{
                  backgroundColor: "#000",
                  padding: "16px",
                  borderRadius: "8px",
                  color: "#a8b2c1",
                  overflowX: "auto",
                  fontSize: "13px",
                  fontFamily: "monospace",
                  margin: 0,
                }}
              >
                {patch}
              </pre>
            ) : (
              <p
                style={{
                  color: "#a1a1aa",
                  fontSize: "13px",
                  fontStyle: "italic",
                  margin: 0,
                }}
              >
                No file changes detected.
              </p>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
