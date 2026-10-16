# 🤖 Autonomous Debugging Agent (ADA)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, agentic AI debugging pipeline that autonomously clones repositories, investigates GitHub issues, executes local tests within isolated Docker sandboxes, and generates standard `.patch` files for human review. 

Unlike standard LLM wrappers, ADA is built with a **state-aware ReAct (Reasoning + Acting) loop**, robust duplicate-action caching, and an event-driven architecture that streams real-time agent telemetry to a custom React dashboard via Server-Sent Events (SSE).

## 🚀 Key Features

* **Dynamic Ephemeral Sandboxing:** Safely clones target repositories into isolated, temporary directories (managed via Docker) to prevent unpredictable AI execution from modifying host environments.
* **State-Aware ReAct Engine:** Powered by Google Gemini, the agent maintains an internal action cache to detect and prevent infinite loops or duplicate operations, enforcing strict budgeting (max 15 iterations).
* **Real-Time Telemetry UI:** A custom-built React frontend featuring an auto-scrolling terminal that consumes FastAPI Server-Sent Events (SSE) to display the agent's internal thought process, tool execution, and system errors in real-time.
* **Automated Patch Generation:** Upon successfully validating a fix via the internal test suite, the system executes a secure `git diff`, performs garbage collection on the sandbox, and surfaces a downloadable `.patch` file to the UI.
* **Persistent Observability:** All runs, steps, execution durations, and LLM hypotheses are persisted in a PostgreSQL database using SQLModel, with OpenTelemetry tracing (Zipkin) wired for bottleneck analysis.

## 🏗️ System Architecture

### 1. The Infrastructure Layer
* **Backend:** FastAPI, Python 3.11+, PostgreSQL (SQLModel).
* **Frontend:** React, Vite, Custom CSS Grid (Dark Theme IDE aesthetic).
* **Observability:** OpenTelemetry, Zipkin, BatchSpanProcessor.

### 2. The Execution Workflow
1. **Intake:** The user submits a Git repository URL and a natural language bug description via the React UI.
2. **Provisioning:** FastAPI intercepts the request, generates a UUID for the run, creates a database record, and provisions a secure `workspaces/run_{uuid}` directory.
3. **Cloning & Sandboxing:** The target repository is dynamically cloned into the ephemeral workspace, and a Docker container is spun up and bound to this directory.
4. **Agentic Loop:** The `AgentRuntime` initializes the ReAct loop:
   * Analyzes the bug and formulates a hypothesis.
   * Dispatches tools (`read_file`, `list_files`, `search_code`, `run_tests`, `write_file`) via the `ToolRegistry`.
   * Evaluates test outputs and iterates until the bug is resolved.
5. **Delivery & Cleanup:** The backend executes `git diff`, streams the resulting patch to the UI, updates the Postgres record to `SUCCESS`, and gracefully deletes the ephemeral workspace to prevent disk bloat.

## 🛠️ Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Backend API** | FastAPI, Uvicorn, Python `asyncio`, Pydantic |
| **Database & ORM** | PostgreSQL, SQLModel, SQLAlchemy |
| **Agent AI Core** | Google GenAI SDK (`gemini-3.5-flash-lite`), Prompt Engineering |
| **Frontend UI** | React, Vite, Server-Sent Events (SSE) |
| **Infrastructure** | Docker SDK for Python, Git Subprocess, `shutil` |
| **Observability** | OpenTelemetry, Zipkin |

## ⚙️ Local Development & Setup

### Prerequisites
* Python 3.11+
* Node.js 18+
* Docker Desktop (running)
* PostgreSQL (or rely on Docker Compose)
* Google Gemini API Key

### 1. Clone the Repository
```bash
git clone [https://github.com/shreyask-7/Autonomous-Debugging-Agent.git](https://github.com/shreyask-7/Autonomous-Debugging-Agent.git)
cd Autonomous-Debugging-Agent
```
### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set Environment Variables (or create a .env file)
export GEMINI_API_KEY="your_api_key_here"
export DATABASE_URL="postgresql://user:pass@localhost:5432/agent_db"

# Start the FastAPI Server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd debugger-ui
npm install
npm run dev
```
### 4. Telemetry Services (Optional)
If you want to view the OpenTelemetry traces, spin up Zipkin:

```bash
docker-compose up -d zipkin
# Access the Zipkin UI at http://localhost:9411
```

## 🎮 Usage Guide

1. Navigate to http://localhost:5173 in your browser.

2. Under **Target Repository URL**, input a public Git URL (e.g., https://github.com/pallets/flask.git).

3. Under **Issue Description**, paste the text of a GitHub Issue or describe a known bug.

4. Click **Initialize Run**.

5. Watch the Agent Runtime Telemetry window stream the LLM's thought process and test execution in real-time.

6. Once completed, click **Copy Patch** in the Generated Patch window to apply the fix to your local production codebase.

## 🧠 Handling Hallucinations & LLM Fallbacks

To ensure production stability, ADA implements several custom safeguards against LLM degradation:

* **JSON Sanitization**: Intercepts and strips rogue Markdown blocks injected by the LLM before JSON parsing.

* **Duplicate Action Cache**: Tracks action signatures (e.g., `tool:args`) and instantly rejects duplicate execution attempts, forcing the LLM to reassess its hypothesis.

* **Exponential Backoff**: Catches `503 UNAVAILABLE` API traffic spikes and implements asynchronous exponential backoffs without dropping the active SSE client connection.

## 📄 License

This project is licensed under the MIT License.