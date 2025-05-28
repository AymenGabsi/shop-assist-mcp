# llama_client.py
import os
import requests
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def call_llama_mcp(system_instruction, context_messages, user_input):
    messages = [{"role": "system", "content": system_instruction}] + context_messages
    if user_input:
        messages.append({"role": "user", "content": user_input.strip()})

    print("🧠 MCP Prompt:", messages)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": "llama3-8b-8192", "messages": messages},
    )
    return response.json()["choices"][0]["message"]["content"]