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

- **Lab 2**: Add persistent memory for personalized conversations ✅ (see below)
- **Lab 3**: Gateway for centralized, secure tool management
- **Lab 4**: Production observability and session management
- **Lab 5**: Continuous quality evaluation
- **Lab 6**: Customer-facing chat interface
- **Lab 7**: Governing agent actions with policies

---

---

# Lab 2: Add Memory to Your Agent

**Estimated time: ~20 minutes**

Adds persistent memory so the agent remembers customers across sessions using SEMANTIC (facts) and SUMMARIZATION (conversation history) strategies.

---

## Step 1: Add Memory Resource

```bash
agentcore add memory \
  --name SharedMemory \
  --strategies SEMANTIC,SUMMARIZATION \
  --expiry 30
```

Expected output:
```
Added memory 'SharedMemory'
```

This updates `agentcore/agentcore.json` with the memory configuration (SEMANTIC + SUMMARIZATION namespaces).

---

## Step 2: Create the Memory Session Manager

```bash
mkdir -p app/CustomerSupport/memory
touch app/CustomerSupport/memory/__init__.py
touch app/CustomerSupport/memory/session.py
```

Contents of `app/CustomerSupport/memory/session.py`:

```python
import os
from typing import Optional
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

MEMORY_ID = os.getenv("MEMORY_SHAREDMEMORY_ID")
REGION = os.getenv("AWS_REGION")

def get_memory_session_manager(session_id: str, actor_id: str) -> Optional[AgentCoreMemorySessionManager]:
    if not MEMORY_ID:
        return None

    retrieval_config = {
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.3),
        f"/summaries/{actor_id}/{session_id}": RetrievalConfig(top_k=3, relevance_score=0.3)
    }

    return AgentCoreMemorySessionManager(
        AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config=retrieval_config,
        ),
        REGION
    )
```

---

## Step 3: Update `agentcore.json` — Add Header Allowlist

Add `requestHeaderAllowlist` to the runtime config in `agentcore/agentcore.json`:

```json
"requestHeaderAllowlist": [
    "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id"
]
```

---

## Step 4: Key Changes in `main.py`

- Import `get_memory_session_manager` from `memory.session`
- Pass `session_manager` to the `Agent` constructor
- Extract `session_id` and `user_id` from runtime context in `invoke()`

```python
from memory.session import get_memory_session_manager

def get_or_create_agent(session_id: str, user_id: str):
    ...
    _agent = Agent(
        model=load_model(),
        session_manager=get_memory_session_manager(session_id, user_id),
        ...
    )

@app.entrypoint
async def invoke(payload, context):
    session_id = context.session_id
    user_id = context.request_headers.get('x-amzn-bedrock-agentcore-runtime-custom-user-id', 'default-user')
    agent = get_or_create_agent(session_id, user_id)
    ...
```

---

## Step 5: Deploy (Memory requires cloud deployment)

```bash
agentcore deploy -y -v
```

---

## Step 6: Test Memory Across Sessions

```bash
# Session A — teach the agent about the user
SESSION_A=$(python3 -c 'import uuid; print(uuid.uuid4())')
agentcore invoke "My name is Sarah and I prefer email updates. I recently bought a Smart Watch." \
  --session-id $SESSION_A \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id: Sarah" --stream

# Wait 1-2 minutes for async memory extraction
sleep 2m

# Session B — new session, same user — agent should remember
SESSION_B=$(python3 -c 'import uuid; print(uuid.uuid4())')
agentcore invoke "Do you know anything about me?" \
  --session-id $SESSION_B \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id: Sarah" --stream
```

Expected response from Session B:
```
Yes! I know a few things about you, Sarah:
1. Your name is Sarah
2. You prefer email updates
3. You recently purchased a Smart Watch
```

---

## Memory Strategies

| Strategy | What it captures | Namespace |
|----------|-----------------|-----------|
| SEMANTIC | Facts: names, preferences, order details | `/users/{actorId}/facts` |
| SUMMARIZATION | Compressed conversation history | `/summaries/{actorId}/{sessionId}` |

> Memory extraction is **asynchronous** — wait ~1-2 minutes between sessions.

---

## What Each New Command Does

| Command | What it does |
|---------|-------------|
| `agentcore add memory` | Adds memory config to `agentcore.json` |
| `agentcore deploy -y -v` | Re-deploys updating stack with memory resource |
| `agentcore invoke ... --session-id ... -H ...` | Invokes with session ID and custom user header |

---

---

## Lab 3: AgentCore Gateway

AgentCore Gateway exposes backend tools (Lambda functions) to your agent as MCP tools, so the agent can call them at runtime without embedding the logic locally.

### 3.1 Deploy the Warranty Check Lambda

```bash
# Create IAM execution role for Lambda
aws iam create-role \
  --role-name warranty-check-lambda-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"sts:AssumeRole","Principal":{"Service":"lambda.amazonaws.com"}}]}' \
  --profile anish0637

aws iam attach-role-policy \
  --role-name warranty-check-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile anish0637

# Package and deploy Lambda
cd infrastructure/lambda/warranty_check
zip warranty_lambda.zip handler.py

aws lambda create-function \
  --function-name workshop-warranty-check \
  --runtime python3.12 \
  --role arn:aws:iam::582766763952:role/warranty-check-lambda-role \
  --handler handler.handler \
  --zip-file fileb://warranty_lambda.zip \
  --region us-east-1 \
  --profile anish0637

cd ../../..
```

Lambda ARN: `arn:aws:lambda:us-east-1:582766763952:function/workshop-warranty-check`

### 3.2 Add Gateway and Target via CLI

Run from `/Users/anishkumar/CustomerSupport`:

```bash
export AWS_PROFILE=anish0637
export AWS_DEFAULT_REGION=us-east-1

WARRANTY_LAMBDA_ARN="arn:aws:lambda:us-east-1:582766763952:function:workshop-warranty-check"

# Add gateway configuration to agentcore.json
agentcore add gateway --name my-gateway --runtimes CustomerSupport

# Register Lambda as a gateway target with tool schema
agentcore add gateway-target \
  --type lambda-function-arn \
  --name WarrantyCheck \
  --lambda-arn $WARRANTY_LAMBDA_ARN \
  --tool-schema-file app/CustomerSupport/tool/warranty_schema.json \
  --gateway my-gateway
```

These commands update `agentcore/agentcore.json` with gateway and target config.

### 3.3 Tool Schema

`app/CustomerSupport/tool/warranty_schema.json` defines the `check_warranty` tool exposed to the agent:

```json
[{
  "name": "check_warranty",
  "description": "Check the warranty status of a product by its product ID (e.g. PROD-001).",
  "inputSchema": {
    "type": "object",
    "properties": {
      "product_id": {"type": "string", "description": "The product ID (e.g. PROD-001)"}
    },
    "required": ["product_id"]
  }
}]
```

> `inputSchema` uses `"type": "object"` directly — no nested `"json"` wrapper.

### 3.4 Code Changes

**`app/CustomerSupport/mcp_client/client.py`** — added `get_gateway_mcp_client()`:

```python
def get_gateway_mcp_client() -> MCPClient | None:
    url = os.environ.get("AGENTCORE_GATEWAY_MY_GATEWAY_URL")
    if not url:
        return None   # graceful local degradation
    return MCPClient(lambda: streamablehttp_client(url))
```

**`app/CustomerSupport/main.py`** — key changes:
- Import `get_gateway_mcp_client` from `mcp_client.client`
- Add gateway client to `mcp_clients` list
- Remove `warranty_months` from `PRODUCTS` (now served by Lambda via Gateway)
- `get_product_info` no longer returns warranty months

### 3.5 Deploy

```bash
cd /Users/anishkumar/CustomerSupport
export AWS_PROFILE=anish0637
export AWS_DEFAULT_REGION=us-east-1
agentcore deploy -y -v
```

### 3.6 Test Gateway

```bash
export AWS_PROFILE=anish0637
export AWS_DEFAULT_REGION=us-east-1
cd /Users/anishkumar/CustomerSupport

SESSION_C=$(python3 -c "import uuid; print(uuid.uuid4())")

# Test warranty check via Gateway
agentcore invoke "Check the warranty for product PROD-003" \
  --session-id $SESSION_C \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id: Sarah" \
  --stream

# Combined query
agentcore invoke "What is the price of PROD-001 and is it still under warranty?" \
  --session-id $SESSION_C \
  -H "X-Amzn-Bedrock-AgentCore-Runtime-Custom-User-Id: Sarah" \
  --stream
```

### How Lab 3 Works

```
User prompt
    ↓
Agent (Strands)
    ↓
AgentCore Gateway MCP URL (env: AGENTCORE_GATEWAY_MY_GATEWAY_URL)
    ↓
AgentCore Gateway → invokes Lambda function
    ↓
workshop-warranty-check Lambda
    ↓
Returns warranty status back to agent
```

The env var `AGENTCORE_GATEWAY_MY_GATEWAY_URL` is injected automatically at runtime when deployed — not needed locally.

---

## What Each Lab 3 Command Does

| Command | What it does |
|---------|-------------|
| `agentcore add gateway` | Adds gateway config to `agentcore.json`, associates with runtime |
| `agentcore add gateway-target` | Registers Lambda ARN + tool schema as a callable tool |
| `agentcore deploy -y -v` | Provisions gateway infra and wires env var into runtime container |

---

*Workshop: [AWS Workshop Studio — Getting Started with Amazon Bedrock AgentCore CLI](https://catalog.us-east-1.prod.workshops.aws/)*
