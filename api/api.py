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
