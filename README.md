# AgentAPI

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/agora-999382051935506503) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@kyegomez3242) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kye-g-38759a207/) [![Follow on X.com](https://img.shields.io/badge/X.com-Follow-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/kyegomezb)

[![Swarms Framework](https://img.shields.io/badge/Built%20with-Swarms-blue)](https://github.com/kyegomez/swarms)

AgentAPI is a reference implementation for serving a [Swarms](https://github.com/kyegomez/swarms) agent as an HTTP service. It provides a minimal FastAPI application, a container image, and the configuration required to deploy a single agent to production.

## Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Service](#running-the-service)
- [API Reference](#api-reference)
- [Customizing the Agent](#customizing-the-agent)
- [Deployment Considerations](#deployment-considerations)
- [Testing](#testing)
- [License](#license)

## Overview

The service exposes one agent, constructed once at application startup, behind two endpoints: a health check and a task execution endpoint. The complete application is contained in `api/api.py`.

```python
from fastapi import FastAPI
from swarms import Agent

app = FastAPI()

agent = Agent(agent_name="Researcher", model_name="claude-sonnet-4-5", max_loops=1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(body: dict):
    task = body.get("task")
    if task is None:
        return {"error": "Missing 'task' in request body"}
    output = agent.run(task)
    return {"output": output}
```

Repository layout:

| Path                   | Description                                        |
|------------------------|----------------------------------------------------|
| `api/api.py`           | FastAPI application and agent definition           |
| `api/requirements.txt` | Python dependencies (`swarms`, `fastapi`, `uvicorn`) |
| `Dockerfile`           | Container image based on `python:3.12-slim`        |
| `.env.example`         | Template for required environment variables        |
| `tests.py`             | Smoke-test script (see [Testing](#testing))        |

## Requirements

- Python 3.12 or later
- An Anthropic API key for the default model (`claude-sonnet-4-5`)
- Docker (optional, for containerized deployment)

## Installation

```bash
git clone <repository-url>
cd AgentAPIProduction
pip install -r api/requirements.txt
```

## Configuration

Configuration is supplied through environment variables. Copy the template and populate it:

```bash
cp .env.example .env
```

| Variable              | Required | Default           | Description                                                    |
|-----------------------|----------|-------------------|----------------------------------------------------------------|
| `ANTHROPIC_API_KEY`   | Yes      | none              | API key for the default Claude model                           |
| `WORKSPACE_DIR`       | No       | `agent_workspace` | Directory where Swarms writes agent state, logs, and artifacts |
| `SWARMS_TELEMETRY_ON` | No       | `true`            | Set to `false` to disable Swarms telemetry                     |

Swarms routes model calls through LiteLLM. If `model_name` in `api/api.py` is changed to a model from another provider, the corresponding provider key (for example `OPENAI_API_KEY` or `GROQ_API_KEY`) must be set instead. Refer to the [LiteLLM provider list](https://docs.litellm.ai/docs/providers) for supported models and their required variables.

## Running the Service

### Local

```bash
uvicorn api.api:app --host 0.0.0.0 --port 8080 --reload
```

### Docker

```bash
docker build -t agent-api .
docker run --rm -p 8080:8080 --env-file .env agent-api
```

The image contains no credentials. Secrets must be provided at runtime via `--env-file` or individual `-e` flags.

### Verifying the deployment

```bash
curl http://localhost:8080/health

curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Summarize the key ideas behind multi-agent systems in three bullet points."}'
```

## API Reference

Interactive documentation is available at `/docs` (Swagger UI) and `/redoc` once the service is running.

### `GET /health`

Returns the service status. This endpoint does not contact the model provider and is suitable for load balancer health checks.

Response:

```json
{"status": "ok"}
```

### `POST /run`

Executes a task with the configured agent and returns the result.

Request body:

```json
{"task": "string"}
```

Response:

```json
{"output": "string"}
```

If the `task` field is absent, the endpoint returns HTTP 200 with an error payload:

```json
{"error": "Missing 'task' in request body"}
```

## Customizing the Agent

All agent behavior is defined by the `Agent(...)` constructor in `api/api.py`. The following example illustrates commonly adjusted parameters:

```python
agent = Agent(
    agent_name="Researcher",
    system_prompt="You are a meticulous research assistant.",
    model_name="claude-sonnet-4-5",
    max_loops=1,
    temperature=0.3,
    streaming_on=False,
)
```

The full parameter reference, including tools, memory, and multi-step reasoning, is documented in the [Swarms Agent configuration guide](https://docs.swarms.world/agents/agent-configuration).

To serve multiple agents or a swarm, add additional endpoints to `api/api.py`. Construct agents at module import time so that each worker instantiates them once rather than on every request.

## Deployment Considerations

- **Process model.** The container runs a single Uvicorn process on port 8080. Scale horizontally behind a load balancer rather than increasing worker count, since each worker holds an independent agent instance.
- **Startup validation.** The agent is constructed at import time, but a missing or invalid API key is not detected until the first `/run` request. Deployment checks should exercise both `/health` and `/run`.
- **Persistence.** `WORKSPACE_DIR` is written inside the container. Mount a volume at that path if agent state or logs must survive restarts.
- **Error handling.** The `/run` endpoint returns HTTP 200 for a missing `task` field. Callers should inspect the response body rather than relying on status codes alone.

## Testing

`tests.py` is a smoke-test script that issues requests against a running server on `localhost:8080`. It currently targets a previous version of this API with a multi-endpoint surface (`/v1/agent`, `/v1/agents`, and related routes) and must be updated for the current `/health` and `/run` endpoints before it will pass.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
