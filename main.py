from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os
import requests
import json

from agent import load_manifest, build_prompt, call_ollama, parse_agent_response, call_mcp

app = FastAPI()

# In-memory storage for tasks
task_list = []

class Message(BaseModel):
    message: str

@app.get("/tool-manifest.json")
def get_manifest():
    manifest_path = os.path.join(os.getcwd(), "tool-manifest.json")
    return FileResponse(manifest_path, media_type="application/json")

def handle_rpc_call(method: str, params: dict, request_id=None):
    if method == "add_task":
        task = params.get("task")
        if task:
            task_list.append(task)
            result = { "tasks": task_list, "success": True }
        else:
            result = { "success": False }

    elif method == "list_tasks":
        result = { "tasks": task_list }

    else:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found"
            },
            "id": request_id
        }

    return {
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    }

@app.post("/rpc")
async def handle_rpc(request: Request):
    data = await request.json()
    return handle_rpc_call(data.get("method"), data.get("params", {}), data.get("id"))

@app.post("/agent")
async def agent_interface(msg: Message):
    user_input = msg.message

    # Load tool manifest
    manifest = load_manifest()

    # Build prompt
    prompt = build_prompt(manifest, user_input)
    print("\n🧠 Sending prompt to model...")

    # Call Ollama
    model_text = call_ollama(prompt)
    print("\n🤖 Raw LLM Output:\n", model_text)

    parsed = parse_agent_response(model_text)
    print(f"\n🔁 Calling MCP method '{parsed}'")
    rpc_result = handle_rpc_call(parsed["method"], parsed.get("params", {}), request_id=1)

    return {
        "called_method": parsed["method"],
        "params": parsed["params"],
        "mcp_result": rpc_result["result"]
    }