from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import os

app = FastAPI()

# In-memory storage for tasks
task_list = []

@app.get("/tool-manifest.json")
def get_manifest():
    manifest_path = os.path.join(os.getcwd(), "tool-manifest.json")
    return FileResponse(manifest_path, media_type="application/json")

@app.post("/rpc")
async def handle_rpc(request: Request):
    data = await request.json()

    method = data.get("method")
    params = data.get("params", {})
    request_id = data.get("id", None)

    if method == "add_task":
        task = params.get("task")
        if task:
            task_list.append(task)
            result = { task_list: task_list, "success": True }
        else:
            result = { "success": False }

    elif method == "list_tasks":
        result = { "tasks": task_list }

    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found"
            },
            "id": request_id
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    })
