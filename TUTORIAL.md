# Amazon Bedrock AgentCore CLI — Lab 1 Reference

Step-by-step CLI commands from the AWS Workshop Studio tutorial:
**Getting Started with Amazon Bedrock AgentCore CLI — Lab 1: Building the Agent Prototype**

---

## Prerequisites

Ensure the following are installed:

- Python 3.10+
- Node.js 18+
- `git`
- `uv` (Python package manager)
- AWS CLI configured with valid credentials

---

## Step 0: Install the AgentCore CLI

There are two AgentCore CLIs. Install the **npm (recommended)** one:

```bash
npm install -g @aws/agentcore
```

Verify:

```bash
agentcore --version
```

The Python toolkit is also available (used internally by some commands):

```bash
pip3 install bedrock-agentcore-starter-toolkit
```

---

## Step 1: Create the Project

Scaffold a new CustomerSupport agent project using Strands Agents SDK with Amazon Bedrock:

```bash
# Interactive mode (follows prompts)
agentcore create

# Non-interactive with defaults
agentcore create \
  --project-name CustomerSupport \
  --agent-framework Strands \
  --model-provider Bedrock \
  --non-interactive
```

Expected output:

```
Agent initializing...
    • Template copied.
    • Venv created and installed.
✓ Agent initialized.
```

Navigate into the project:

```bash
cd CustomerSupport
```

---

## Step 2: Project Structure

```
CustomerSupport/
├── .bedrock_agentcore.yaml     # Main project config
├── .gitignore
├── README.md
├── pyproject.toml              # Python dependencies
├── uv.lock
├── src/
│   ├── main.py                 # Agent entry point  ← edit this
│   ├── mcp_client/
│   │   └── client.py           # Exa AI MCP client (web search)
│   └── model/
│       └── load.py             # Model configuration (Claude Sonnet 4.5)
└── test/
```

Key files:

| File | Purpose |
|------|---------|
| `src/main.py` | Agent entry point — tools, system prompt, handler |
| `src/model/load.py` | Bedrock model config (Claude Sonnet 4.5) |
| `src/mcp_client/client.py` | Exa AI MCP client for web search |
| `.bedrock_agentcore.yaml` | AgentCore project configuration |

---

## Step 3: Customize `src/main.py`

Replace the default `add_numbers` sample with customer support tools.

The updated `main.py` adds:

- `get_return_policy(product_category)` — returns policy for electronics / accessories / audio
- `get_product_info(query)` — looks up products by name, ID, or keyword
- Exa AI MCP client — web search for troubleshooting
- Customer support system prompt

See [`src/main.py`](src/main.py) for the full implementation.

---

## Step 4: Start the Local Dev Server

```bash
# Interactive TUI (chat interface in terminal)
agentcore dev

# Non-interactive mode (shows logs, use for split-terminal testing)
agentcore dev --logs
```

The dev server starts on **port 8080** with hot reload enabled.

---

## Step 5: Test the Agent (Interactive)

Inside the `agentcore dev` TUI, try:

```
What's the return policy for electronics?
```
```
Tell me about the Wireless Headphones
```
```
Search for common Bluetooth headphone troubleshooting tips
```
```
I bought a Smart Watch (PROD-002) and want to return it. What's the policy?
```

Press `Esc` to exit the TUI.

---

## Step 6: Test via CLI (Non-Interactive)

In a second terminal, invoke the agent while `agentcore dev --logs` runs in the first:

```bash
agentcore dev "What can you do?" --stream
```

Output is streamed directly to the terminal — useful for scripting and CI/CD.

---

## Step 7: Deploy to AWS

Deploy your agent to Amazon Bedrock AgentCore Runtime (fully managed, scalable):

```bash
agentcore deploy
```

Check deployment status:

```bash
agentcore status
```

Invoke the deployed cloud agent:

```bash
agentcore invoke "What can you do?"
```

To tear down all deployed resources:

```bash
agentcore destroy
```

---

## What Each Command Does

| Command | What it does |
|---------|-------------|
| `agentcore create` | Scaffolds project directory, venv, and starter agent code |
| `agentcore dev` | Runs local dev server with hot reload on port 8080 |
| `agentcore dev --logs` | Same but non-interactive; shows raw logs |
| `agentcore dev "prompt" --stream` | Sends a one-shot prompt and streams the response |
| `agentcore deploy` | Packages code, provisions IAM + runtime via CDK, deploys to cloud |
| `agentcore status` | Shows runtime status, endpoint, and config |
| `agentcore invoke "prompt"` | Invokes the deployed cloud agent |
| `agentcore destroy` | Tears down all AWS resources for this agent |

---

## Tools Built in Lab 1

| Tool | Description |
|------|-------------|
| `get_return_policy(category)` | Returns return window, conditions, and refund type for a product category |
| `get_product_info(query)` | Searches products by name, ID (e.g. `PROD-001`), or keyword |
| Exa AI MCP (web search) | Live web search via [mcp.exa.ai](https://mcp.exa.ai/mcp) |

---

## Next Steps

- **Lab 2**: Add persistent memory for personalized conversations
- **Lab 3**: Gateway for centralized, secure tool management
- **Lab 4**: Production observability and session management
- **Lab 5**: Continuous quality evaluation
- **Lab 6**: Customer-facing chat interface
- **Lab 7**: Governing agent actions with policies

---

*Workshop: [AWS Workshop Studio — Getting Started with Amazon Bedrock AgentCore CLI](https://catalog.us-east-1.prod.workshops.aws/)*
