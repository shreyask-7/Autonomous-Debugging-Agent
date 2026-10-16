import { useState, useRef, useEffect } from "react";
import "./App.css";

function App() {
  const [repoPath, setRepoPath] = useState("tests/dummy_repo");
  const [issue, setIssue] = useState(
    "The ShoppingCart checkout method calculates tax incorrectly when a discount code is applied. Tax should be calculated on the discounted subtotal, not the original subtotal.",
  );
  const [runId, setRunId] = useState(null);
  const [steps, setSteps] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [runHistory, setRunHistory] = useState([]);

  const eventSourceRef = useRef(null);

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
    fetchHistory();

    const streamUrl = `http://localhost:8000/api/runs/${data.id}/stream`;
    eventSourceRef.current = new EventSource(streamUrl);

    eventSourceRef.current.onmessage = (event) => {
      const stepData = JSON.parse(event.data);
      setSteps((prev) => [...prev, stepData]);

      if (stepData.status === "finished" || stepData.status === "error") {
        eventSourceRef.current.close();
        setIsRunning(false);
        fetchHistory();
      }
    };

    eventSourceRef.current.onerror = () => {
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
    <div
      className="app-layout"
      style={{ display: "flex", height: "100vh", width: "100vw" }}
    >
      <div
        className="sidebar"
        style={{
          width: "300px",
          borderRight: "1px solid #ccc",
          padding: "1rem",
          overflowY: "auto",
        }}
      >
        <h2>Run History</h2>
        <ul className="history-list" style={{ listStyle: "none", padding: 0 }}>
          {runHistory.map((run) => (
            <li
              key={run.id}
              className="history-item"
              style={{
                marginBottom: "1rem",
                padding: "0.5rem",
                border: "1px solid #eee",
                borderRadius: "4px",
              }}
            >
              <strong>{run.repo_name}</strong>
              <div
                style={{
                  fontSize: "0.85em",
                  color: "#666",
                  marginTop: "0.25rem",
                }}
              >
                Status: {run.status || "UNKNOWN"}
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div
        className="main-content"
        style={{
          flex: 1,
          padding: "2rem",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <h1>Autonomous Debugger</h1>

        <form
          onSubmit={startRun}
          className="setup-form"
          style={{ marginBottom: "2rem" }}
        >
          <input
            value={repoPath}
            onChange={(e) => setRepoPath(e.target.value)}
            placeholder="Repository Path"
            disabled={isRunning}
            style={{
              display: "block",
              width: "100%",
              marginBottom: "1rem",
              padding: "0.5rem",
            }}
          />
          <textarea
            value={issue}
            onChange={(e) => setIssue(e.target.value)}
            placeholder="Bug Report"
            disabled={isRunning}
            style={{
              display: "block",
              width: "100%",
              minHeight: "80px",
              marginBottom: "1rem",
              padding: "0.5rem",
            }}
          />
          <button
            type="submit"
            disabled={isRunning}
            style={{
              padding: "0.75rem 1.5rem",
              cursor: isRunning ? "not-allowed" : "pointer",
            }}
          >
            {isRunning ? "Agent is Running..." : "Start Debugging"}
          </button>
        </form>

        <div
          className="terminal"
          style={{
            backgroundColor: "#1e1e1e",
            color: "#fff",
            padding: "1rem",
            borderRadius: "8px",
            overflowY: "auto",
            flex: 1,
          }}
        >
          {steps.map((step, index) => (
            <div
              key={index}
              className="step-block"
              style={{
                marginBottom: "1.5rem",
                borderBottom: "1px solid #333",
                paddingBottom: "1rem",
              }}
            >
              <p className="thought" style={{ color: "#88aaff" }}>
                <strong>🤔 Thought:</strong> {step.thought}
              </p>
              {step.tool && (
                <div className="action">
                  <p style={{ color: "#ffaa88" }}>
                    <strong>🔧 Tool:</strong> {step.tool}
                  </p>
                  <pre
                    className="output"
                    style={{
                      backgroundColor: "#000",
                      padding: "0.5rem",
                      fontSize: "0.85em",
                      overflowX: "auto",
                    }}
                  >
                    {step.output}
                  </pre>
                </div>
              )}
              {step.summary && (
                <p className="success" style={{ color: "#88ff88" }}>
                  <strong>✅ Finished:</strong> {step.summary}
                </p>
              )}
              {step.error && (
                <p className="error" style={{ color: "#ff8888" }}>
                  <strong>❌ Error:</strong> {step.error}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
