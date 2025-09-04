#!/usr/bin/env python3
"""
intermediate_tool.py

This script acts as an intermediary between ChatGPT and a local shell. It sends
messages to the OpenAI Chat API, extracts commands enclosed in <command> tags
from the assistant’s reply, runs those commands using subprocess, and feeds
the resulting output back into the conversation. See `prompt_instructions.md`
for guidelines that ChatGPT should follow.
"""

import os
import re
import subprocess
import openai

# Load your OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def extract_commands(text: str):
    """Extract shell commands enclosed in <command>...</command> tags."""
    pattern = re.compile(r"<command>(.*?)</command>", re.DOTALL)
    return [cmd.strip() for cmd in pattern.findall(text)]

def run_command(command: str) -> str:
    """Run a shell command and return its output (stdout and stderr)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error executing command: {e}"

def main():
    if not openai.api_key:
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

    # Load system prompt from file or define fallback instructions
    try:
        with open("prompt_instructions.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = (
            "You are a shell assistant. When you want to run a command, "
            "wrap the command inside <command> and </command> tags. "
            "Provide explanations outside of the tags."
        )

    messages = [{"role": "system", "content": system_prompt}]

    print("ChatGPT command bridge started. Type your messages. Ctrl+C to exit.")
    try:
        while True:
            user_message = input("You: ")
            messages.append({"role": "user", "content": user_message})

            # Send the conversation to OpenAI
            response = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
            )

            assistant_content = response["choices"][0]["message"]["content"]
            print(f"GPT: {assistant_content}")
            messages.append({"role": "assistant", "content": assistant_content})

            # Extract and run any commands in the assistant's response
            for cmd in extract_commands(assistant_content):
                print(f"> Running: {cmd}")
                output = run_command(cmd)
                print(output)
                # Append output as a message so the assistant can see results
                messages.append({
                    "role": "tool",
                    "name": "command_output",
                    "content": output,
                })
    except KeyboardInterrupt:
        print("\nExiting.")

if __name__ == "__main__":
    main()
