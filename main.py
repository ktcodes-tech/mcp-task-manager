from db import SessionLocal, Task, init_db

from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os

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

def add_task(db, params: dict):
    task = params.get("task")
    if task:
        new_task = Task(text=task)
        db.add(new_task)
        db.commit()
        result = { "tasks": db.query(Task).all(), "success": True }
    else:
        result = { "success": False }
    return result

def delete_task(db, params: dict):
    task = db.query(Task).filter(Task.id == params.get("task_id")).first()
    if task:
        db.delete(task)
        db.commit()
        result = { "tasks": db.query(Task).all(), "success": True }
    else:
        result = { "success": False, "error": "Task not found" }
    return result

def list_tasks(db):
    tasks = db.query(Task).all()
    return { "tasks": tasks }

def update_task(db, params: dict):
    task_id = params.get("task_id")
    new_text = params.get("new_task")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task and new_text:
        task.text = new_text
        db.commit()
        result = { "tasks": db.query(Task).all(), "success": True }
    else:
        result = { "success": False, "error": "Task not found or invalid data" }
    return result

def search_tasks(db, params: dict):
    task = params.get("keyword")
    task = db.query(Task).filter(Task.text.contains(task))
    if task:
        return { "tasks": task.all() }
    else:
        return { "error": "Task not found" }
    
def get_task(db, params: dict):
    task_id = params.get("task_id")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        return { "task": task }
    else:
        return { "error": "Task not found" }
    
def clear_tasks(db):
    db.query(Task).delete()
    db.commit()
    return { "success": True, "message": "All tasks cleared" }

def get_task_count(db):
    count = db.query(Task).count()
    return { "task_count": count }


def handle_rpc_call(method: str, params: dict, request_id=None):
    db = SessionLocal()
    if method == "add_task":
        result = add_task(db, params)

    elif method == "list_tasks":
        result = list_tasks(db)

    elif method == "delete_task":
        result = delete_task(db, params)

    elif method == "update_task":
        result = update_task(db, params)

    elif method == "search_tasks":
        result = search_tasks(db, params)

    elif method == "get_task":
        result = get_task(db, params)

    elif method == "clear_tasks":
        result = clear_tasks(db)

    elif method == "get_task_count":
        result = get_task_count(db)

    else:
        result = {  "error": f"Method '{method}' not found", "message": params.get("message", "") }

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

init_db()  # Initialize the database
print("Database initialized and ready to use.")