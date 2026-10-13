# Autonomous Debugging Agent

A stateful, AI-driven debugging runtime that autonomously reproduces software bugs, navigates repositories, and applies verified patches within an isolated execution environment. 

This project bypasses high-level wrappers (like LangChain) in favor of a custom-built Reason + Act (ReAct) loop to prioritize deterministic state management, secure process isolation, and deep observability.

## 🏗️ Architecture & Tech Stack

*   **Core Engine:** Python, Custom ReAct State Machine, Gemini 3.5 Flash
*   **API & Streaming:** FastAPI, Server-Sent Events (SSE)
*   **Process Isolation:** Docker Engine SDK (Ephemeral Sandboxing)
*   **State Persistence:** PostgreSQL, SQLModel
*   **Observability:** OpenTelemetry, Zipkin
*   **Frontend:** React (Live Telemetry Dashboard)

## ✨ Core Features (MVP)

*   **Secure Docker Sandboxing:** The agent executes tools (file reading, AST searching, test running, and patching) entirely within a dynamically provisioned, network-restricted Docker container, ensuring host system safety.
*   **Custom Tool Registry:** A strict JSON-schema dispatcher that routes LLM decisions to deterministic Python functions, capturing standard output and standard error for the context window.
*   **Real-Time Execution Streaming:** The FastAPI backend utilizes asynchronous generators and SSE to push live telemetry—including agent thoughts, tool selections, and terminal outputs—to the frontend dashboard with millisecond latency.
*   **Fault-Tolerant Engine:** Includes exponential backoff for API rate limits and robust JSON parsing fallbacks to prevent infinite loops or system crashes during malformed model generations.
*   **Distributed Tracing:** Fully instrumented with OpenTelemetry to track API latency, database transaction times, and tool execution durations via Zipkin.

## 🚀 Current Focus & Roadmap

This project is currently in active development. The MVP engine is complete, and the focus is now shifting toward building a research-grade evaluation harness.

- [x] Phase 1: Core ReAct loop and Docker sandboxing.
- [x] Phase 2: PostgreSQL state persistence and API layer.
- [x] Phase 3: Real-time React dashboard and OpenTelemetry integration.
- [ ] **Current:** Building an automated SWE-bench-style batch runner to evaluate the agent against a dataset of 30 isolated bugs from open-source Python repositories.
- [ ] **Upcoming:** Implementing strict regression-aware patching and hypothesis management to prevent destructive side effects.
