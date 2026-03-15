import argparse
import os
import json

from typing import Optional

from openai import OpenAI
from app.tools.utils import TOOLS
from app.tools import file_handler  # noqa
from app.tools import command_handler  # noqa
import settings

API_KEY = settings.API_KEY
BASE_URL = settings.BASE_URL
MODEL = settings.LLM_MODEL


def run_conversation(client: OpenAI, initial_prompt: str) -> None:
    """Run the conversation loop with the AI model."""
    conversation_log = [{"role": "user", "content": initial_prompt}]
    tool_definitions = [t["definition"] for t in TOOLS.values()]

    while True:
        chat = client.chat.completions.create(
            model=MODEL,
            messages=conversation_log,
            tools=tool_definitions,
        )
        if not chat.choices:
            raise RuntimeError("No choices in response")

        response = chat.choices[0].message
        conversation_log.append(response)

        if not response.tool_calls:
            print(response.content)
            break

        for tool_call in response.tool_calls:
            tool_result = executes_tools(tool_call)
            conversation_log.append(tool_result)


def executes_tools(tool_call: dict) -> Optional[dict]:
    """Execute a tool call and return the result of a message"""

    tool_call_id = tool_call.id
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    if function_name not in TOOLS:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"Unknown function: {function_name}",
        }
    result = TOOLS[function_name]["handler"](**function_args)
    return {"role": "tool", "tool_call_id": tool_call.id, "content": result}



def main():
    p = argparse.ArgumentParser(description="AI assistant with file operations")
    p.add_argument("-p", required=True, help="The prompt to send to the AI")
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    run_conversation(client, args.p)

if __name__ == "__main__":
    main()
