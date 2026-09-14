# AgentAPI

[![Join our Discord](https://img.shields.io/badge/Discord-Join%20our%20server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/agora-999382051935506503) [![Subscribe on YouTube](https://img.shields.io/badge/YouTube-Subscribe-red?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@kyegomez3242) [![Connect on LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kye-g-38759a207/) [![Follow on X.com](https://img.shields.io/badge/X.com-Follow-1DA1F2?style=for-the-badge&logo=x&logoColor=white)](https://x.com/kyegomezb)

[![Swarms Framework](https://img.shields.io/badge/Built%20with-Swarms-blue)](https://github.com/kyegomez/swarms)

A minimal, production-ready template for serving a [Swarms](https://github.com/kyegomez/swarms) agent over HTTP with FastAPI. Fork it, change the agent, deploy the container.

## What's inside

```
.
├── api/
│   ├── api.py            # FastAPI app: one Agent, two endpoints
│   └── requirements.txt  # swarms, fastapi, uvicorn
├── Dockerfile            # python:3.12-slim image, serves on port 8080
├── .env.example          # environment variables to copy into .env
└── tests.py              # smoke-test script (see note below)
```

The whole API is `api/api.py`:

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

## Endpoints

| Method | Path      | Body                | Response                              |
|--------|-----------|---------------------|---------------------------------------|
| GET    | `/health` | none                | `{"status": "ok"}`                    |
| POST   | `/run`    | `{"task": "<str>"}` | `{"output": "<agent response>"}`      |

If `task` is missing from the body, `/run` returns `{"error": "Missing 'task' in request body"}`.

Interactive docs are served by FastAPI at `/docs` (Swagger) and `/redoc`.

## Quick start

### 1. Configure environment

```bash
cp .env.example .env
```

The default agent uses `claude-sonnet-4-5`, so `ANTHROPIC_API_KEY` is required. See `.env.example` for the optional variables.

| Variable              | Required | Purpose                                                        |
|-----------------------|----------|----------------------------------------------------------------|
| `ANTHROPIC_API_KEY`   | yes      | Model provider key for the default Claude model                |
| `WORKSPACE_DIR`       | no       | Where swarms writes agent state and logs (default `agent_workspace`) |
| `SWARMS_TELEMETRY_ON` | no       | Set to `false` to disable swarms telemetry                     |

If you change `model_name` to another provider (OpenAI, Groq, Gemini, etc.), set that provider's key instead. Swarms routes model calls through LiteLLM, so any [LiteLLM-supported model name](https://docs.litellm.ai/docs/providers) works.

### 2. Run locally

```bash
pip install -r api/requirements.txt
uvicorn api.api:app --host 0.0.0.0 --port 8080 --reload
```

### 3. Run with Docker

```bash
docker build -t agent-api .
docker run --rm -p 8080:8080 --env-file .env agent-api
```

The image does not bake in any secrets. Pass them at runtime with `--env-file` or `-e`.

### 4. Call it

```bash
curl http://localhost:8080/health

curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Summarize the key ideas behind multi-agent systems in three bullets."}'
```

## Customizing the agent

Everything about the agent lives in the `Agent(...)` constructor in `api/api.py`. Common changes:

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

See the [Swarms Agent docs](https://docs.swarms.world/agents/agent-configuration) for the full list of parameters, including tools, memory, and multi-loop reasoning.

To serve several agents or a swarm, add more endpoints to `api/api.py` and construct the agents at module import time so they are created once per worker, not once per request.

## Deployment notes

- The container listens on port `8080` and runs a single uvicorn process. Put it behind a load balancer and scale horizontally rather than adding workers, since each worker holds its own agent instance.
- The agent is created at import time, so a missing API key will surface on the first `/run` call, not at startup. Hit `/health` and then `/run` once as part of your deploy check.
- `WORKSPACE_DIR` is written to inside the container. Mount a volume if you need agent state or logs to persist across restarts.

## Tests

`tests.py` is a smoke-test script against a running server on `localhost:8080`. It currently targets an older multi-endpoint version of this API (`/v1/agent`, `/v1/agents`, etc.) and needs to be rewritten for the current `/health` and `/run` endpoints before it will pass.

## License

MIT. See [LICENSE](LICENSE).
