import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MCP_URL = "http://localhost:8000/rpc"
MODEL = "llama3"

def load_manifest():
    with open("tool-manifest.json") as f:
        return json.load(f)

def call_ollama(prompt: str):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    })

    if response.status_code != 200:
        raise Exception(f"Ollama error: {response.text}")

    return response.json()["response"]

def parse_agent_response(response: str):
    try:
        start = response.index("{")
        end = response.rindex("}") + 1
        return json.loads(response[start:end])
    except Exception as e:
        print(f"Failed to extract JSON from model output:\n{response}\n\n{e}")
        return { "method": "", "params": { "message": response.strip() } }

def call_mcp(method: str, params: dict):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(MCP_URL, json=payload)
    return response.json()

def build_prompt(manifest, user_input):
    methods = []
    for name, method in manifest["methods"].items():
        methods.append(f"- {name}: {method['description']}")
    tool_summary = "\n".join(methods)

    prompt = f"""You are an AI agent that can call the following tools:

        {tool_summary}

        User said: "{user_input}"

        Reply with JSON: {{
        "method": "<tool_name>",
        "params": {{ "task": "<task_description>" and other parameters (task_id, task_ids, new_task, completed, search_term ONLY) as needed }}
    }}"""

    return prompt

def main():
    manifest = load_manifest()
    user_input = input("Ask something: ")

    prompt = build_prompt(manifest, user_input)
    print("\n🧠 Sending prompt to model...")
    model_output = call_ollama(prompt)

    print("\n🤖 Raw LLM Output:\n", model_output)
    parsed = parse_agent_response(model_output)
    method = parsed["method"]
    params = parsed.get("params", {})

    print(f"\n🔁 Calling MCP method '{method}' with params: {params}")
    mcp_response = call_mcp(method, params)

    print("\n✅ Final Result from MCP Server:")
    print(json.dumps(mcp_response["result"], indent=2))

if __name__ == "__main__":
    main()
