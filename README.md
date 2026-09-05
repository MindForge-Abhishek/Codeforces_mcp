# Codeforces MCP Server

A custom MCP (Model Context Protocol) server that connects Claude AI to the Codeforces public API. Built to streamline competitive programming problem logging — Claude can automatically fetch your latest submission data instead of you having to type it manually.

---

## What is MCP?

MCP (Model Context Protocol) is a protocol developed by Anthropic that lets Claude connect to external services and tools. Instead of Claude only knowing what you type, it can directly call APIs, read databases, and interact with external services on your behalf.

This project turns the Codeforces public API into an MCP server that Claude can use as a custom connector.

---

## What Does This Server Do?

Once connected to Claude, this server gives Claude the ability to:

| Tool | What it does |
|------|-------------|
| `get_user_submissions` | Fetch your latest CF submissions with problem name, rating, tags, verdict, contest ID |
| `get_user_info` | Get your current rating, rank, and profile info |
| `get_user_rating` | Get your full rating history across all contests |
| `get_contest_standings` | Check your rank in any specific contest |
| `get_contest_status` | Get all submissions from a specific contest |
| `get_contest_list` | List all past and upcoming Codeforces contests |

### Primary Use Case

The main reason this was built is to automate problem logging. When solving problems on Codeforces, instead of manually providing the problem name, number, rating, and tags every time — Claude fetches all of that automatically from your submission history. You only need to provide:
- How difficult it felt
- What happened during solving
- What you learned

---

## Project Structure

```
codeforces-mcp/
├── codeforces_mcp.py    # Main server file — all tools and API logic
├── requirements.txt      # Python dependencies
├── .gitignore           # Files excluded from version control
└── README.md            # This file
```

---

## How It Works

```
Claude → MCP Connector URL → This Server → Codeforces Public API → Back to Claude
```

1. Claude receives a trigger from the user
2. Claude calls the appropriate tool on this MCP server
3. The server makes a request to the Codeforces public API
4. Codeforces returns the data
5. The server sends it back to Claude
6. Claude uses that data to respond

The Codeforces API is completely public — no authentication or API keys required.

---

## Tech Stack

- **Python 3.11**
- **FastMCP** (`mcp[server]<2`) — framework for building MCP servers
- **httpx** — async HTTP client for making API requests
- **uvicorn** — ASGI server (comes with mcp[server])
- **SSE (Server-Sent Events)** — transport protocol used by Claude to communicate with MCP servers

---

## Local Setup

### Prerequisites
- Python 3.11
- Miniforge / Conda

### Step 1 — Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/codeforces-mcp.git
cd codeforces-mcp
```

### Step 2 — Create conda environment

```bash
conda create -n codeforces-mcp python=3.11
conda activate codeforces-mcp
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Run the server

```bash
python3 codeforces_mcp.py
```

You should see:
```
INFO: Starting Codeforces MCP server...
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## Deployment (Railway)

The server needs to be deployed to a hosting platform so Claude can reach it over the internet. Railway is the recommended option — free tier is sufficient.

### Step 1 — Create a Railway account
Go to [railway.app](https://railway.app) and sign up with GitHub.

### Step 2 — Create a new project
- Click **New Project**
- Select **Deploy from GitHub repo**
- Select this repo

### Step 3 — Add a Procfile
Create a file called `Procfile` (no extension) in the root of the project:
```
web: python3 codeforces_mcp.py
```
Push this to GitHub — Railway will use it to know how to start the server.

### Step 4 — Get your public URL
Railway will give you a URL like:
```
https://codeforces-mcp-production.up.railway.app
```

---

## Connecting to Claude

Once deployed:

1. Go to [claude.ai](https://claude.ai)
2. Open **Settings** → **Connectors**
3. Click **Add custom connector**
4. Paste your Railway URL with `/sse` at the end:
```
https://codeforces-mcp-production.up.railway.app/sse
```
5. Save — Claude can now use all the tools in this server

---

## Available API Endpoints (Internal)

These are the Codeforces API endpoints this server uses internally:

| Server Tool | CF API Endpoint |
|-------------|----------------|
| `get_user_submissions` | `user.status` |
| `get_user_info` | `user.info` |
| `get_user_rating` | `user.rating` |
| `get_contest_standings` | `contest.standings` |
| `get_contest_status` | `contest.status` |
| `get_contest_list` | `contest.list` |

Full Codeforces API documentation: [codeforces.com/apiHelp](https://codeforces.com/apiHelp)

---

## Why Not Use the CF API Directly?

Claude's `web_fetch` tool goes through Anthropic's proxy server, which intercepts and rewrites certain URLs — making direct CF API calls unreliable from inside Claude. This MCP server solves that by acting as a middleman that Claude can reliably call.
