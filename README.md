# OMEGA - Autonomous Terminal AI Agent Runtime

OMEGA is an open-source autonomous terminal AI agent runtime that provides a comprehensive AI-powered development environment with specialist agents, persistent memory, permissioned plugins, and OpenRouter model routing.

## Installation

### Prerequisites
- Windows PowerShell or Git Bash
- Python 3.13+

### Step 1: Create Virtual Environment
```powershell
py -m venv .venv
```

### Step 2: Activate Virtual Environment
```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1

# Git Bash
source .\.venv\Scripts\activate
```

**Note:** If your prompt already shows `(.venv)`, the virtual environment is already active.

### Step 3: Install Dependencies
```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -e ".[dev,documents]"
```

### Step 4: Configure Environment
```powershell
copy .env.example .env
notepad .env
```

In Notepad, set:
```
OPENROUTER_API_KEY=your_openrouter_key_here
```

Save and close Notepad.

**Note:** Set `OPENROUTER_API_KEY` in `.env` or your shell to enable model-backed planning, research, coding strategy, and critique. Without the key, OMEGA still runs deterministic local planning, memory, plugins, and verification flows.

### Step 5: Initialize and Test
```powershell
# Using the omega command (if in PATH)
omega init
omega plugins
omega run "Build a tiny Python notes CLI"

# Using the direct executable (if omega not recognized)
.\venv\Scripts\omega.exe init
.\venv\Scripts\omega.exe plugins
.\venv\Scripts\omega.exe run "Build a tiny Python notes CLI"
```

## API Server

To start the FastAPI server:
```powershell
omega serve --host 127.0.0.1 --port 8765
```

Open the API documentation at:
```
http://127.0.0.1:8765/docs
```

## Available Commands

### Core Commands

#### `omega init`
**Purpose:** Initialize OMEGA configuration and directories
**Description:** Creates the necessary directory structure and configuration files for OMEGA to operate. This is the first step when setting up a new workspace.

#### `omega run <goal> [--online] [--approved] [--json]`
**Purpose:** Execute a high-level goal using OMEGA's autonomous agents
**Description:** Runs OMEGA's specialist agents (planner, research, coding, browser, DevOps, memory, critic, executor) to accomplish the specified goal. Supports online mode for web search and approval mode for pre-approving confirmation-gated actions.

**Options:**
- `--online`: Allow web search where plugins permit it
- `--approved`: Pre-approve confirmation-gated plugin actions
- `--json`: Print raw JSON output instead of formatted results

#### `omega plugins`
**Purpose:** List all available plugins and their descriptions
**Description:** Displays the manifest of all registered plugins, including built-in adapters and user-added plugins. Shows plugin names, descriptions, and permissions.

#### `omega improve`
**Purpose:** Analyze task history and generate self-improvement proposals
**Description:** Runs the self-improvement engine to analyze task execution history and generate approval-gated improvement proposals for OMEGA's internal systems.

#### `omega serve [--host] [--port]`
**Purpose:** Start the FastAPI API server
**Description:** Launches the web API interface for programmatic interaction with OMEGA. Allows remote execution of goals, plugin calls, and memory operations.

### Memory Commands

#### `omega memory search <query> [--limit]`
**Purpose:** Search persistent memory for specific information
**Description:** Queries OMEGA's memory system (short-term, long-term, semantic, episodic, procedural, and user-style records) for relevant information based on the search query.

**Options:**
- `--limit`: Maximum number of records to return (default: 10)

### Workflow Commands

#### `omega workflow run <path> [--online] [--approved]`
**Purpose:** Execute a multi-step workflow defined in YAML/JSON
**Description:** Runs complex, multi-step workflows defined in JSON/YAML files. Workflows coordinate multiple agent actions and can include conditional logic and error handling.

**Options:**
- `--online`: Allow web search where plugins permit it
- `--approved`: Pre-approve confirmation-gated plugin actions

## API Endpoints

The OMEGA API provides programmatic access to all core functionality:

### Health Check
- **Method:** `GET`
- **Endpoint:** `/health`
- **Description:** Returns service health status

### Plugins Management
- **Method:** `GET`
- **Endpoint:** `/plugins`
- **Description:** Returns manifest of all available plugins

### Goal Execution
- **Method:** `POST`
- **Endpoint:** `/goals`
- **Body:** `{"goal": "string", "online": bool, "approved": bool}`
- **Description:** Execute a goal via API

### Plugin Execution
- **Method:** `POST`
- **Endpoint:** `/plugins/call`
- **Body:** `{"plugin": "string", "action": "string", "arguments": dict, "approved": bool}`
- **Description:** Call a specific plugin with arguments

### Memory Search
- **Method:** `GET`
- **Endpoint:** `/memory/search?query=...&limit=10`
- **Description:** Search memory records

## Architecture

### Core Components

- **`omega/runtime.py`**: Wires settings, memory, permissions, plugins, model routing, OpenRouter, and the executor
- **`omega/agents/`**: Contains the internal agent operating system (planner, research, coding, browser, DevOps, memory, critic, executor)
- **`omega/plugins/`**: Safe tool adapters for filesystem, terminal, git, database, Docker, API, browser, search, RAG, MCP, notes, calendar, email, spreadsheets, PDF, OCR, vision, audio, and YouTube
- **`omega/memory.py`**: Stores persistent memories, task history, and a lightweight knowledge graph in SQLite
- **`omega/permissions.py`**: Enforces allow, deny, and require-confirmation decisions
- **`omega/workflows.py`**: Runs JSON/YAML multi-step workflows
- **`omega/self_improvement.py`**: Analyzes task history and records approval-gated improvement proposals

### Memory System

OMEGA supports multiple memory types:
- **Short-term**: Temporary working memory
- **Long-term**: Persistent knowledge storage
- **Semantic**: Fact and concept storage
- **Episodic**: Event and experience recording
- **Procedural**: Action and behavior patterns
- **User-style**: Personalized memory organization

### Safety Model

OMEGA implements comprehensive safety controls:
- **Path Resolution**: Resolves file paths against the configured workspace and blocks path escapes
- **Permission Enforcement**: Destructive actions (writes, deletes, terminal commands, commits, pushes, email sends, uploads, removals) require approval unless explicitly allowed
- **Default Policy**: Allows safe reads, listing, search, memory, notes, calendar, git inspection, read-only database access, and API/search requests

### Dynamic Plugins

User plugins can be added dynamically:
- **Location**: Drop Python files into `.omega/plugins`
- **Export**: Each plugin must export `omega_plugin()` returning an instance of `omega.plugins.base.Plugin`
- **Refresh**: Run `omega plugins` after adding a plugin to refresh the manifest

### MCP Support

Model Context Protocol (MCP) servers are supported:
- **Configuration**: Stored in `.omega/mcp_servers.json`
- **Discovery**: MCP plugin can list configured servers and query `tools/list` over stdio JSON-RPC

## Docker Support

Run OMEGA in Docker:
```bash
docker compose up --build
```

The API container:
- Listens on port `8765`
- Mounts the repository as `/workspace`
- Stores OMEGA data in a named volume

## Verification

Test your installation:
```bash
python -m compileall omega tests
python -m unittest discover tests
python scripts/benchmark.py
```

The benchmark checks local memory retrieval latency against the 200 ms target on a small dataset.

## Configuration

### Environment Variables
- `OPENROUTER_API_KEY`: API key for OpenRouter model access

### Configuration Files
- `.env`: Environment configuration
- `.omega/mcp_servers.json`: MCP server configuration

## Contributing

OMEGA is an open-source project. Contributions are welcome! Please refer to the contributing guidelines in the repository for more information.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
