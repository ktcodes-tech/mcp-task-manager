import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
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
        "params": {{ ... }}
    }}"""

    return prompt

def main():
    manifest = load_manifest()
    user_input = input("Ask something: ")

    prompt = build_prompt(manifest, user_input)
    response = call_ollama(prompt)

    print("\n🤖 Agent Response:\n", response)

if __name__ == "__main__":
    main()
