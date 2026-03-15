# code_agent

A CLI coding agent that uses an LLM via [OpenRouter](https://openrouter.ai) to complete tasks using file and shell tools.

## How it works

The agent runs a conversation loop: it sends your prompt to the model, executes any tool calls the model requests, feeds results back, and repeats until the model returns a final response.

**Available tools:**

| Tool | Description |
|------|-------------|
| `read_file` | Read the contents of a file |
| `Write` | Write content to a file |
| `Bash` | Execute a shell command |

New tools can be added by decorating a function with `@tool` in `app/tools/`.

## Setup

**Prerequisites:** Python 3.9+, [uv](https://docs.astral.sh/uv/)

1. Clone the repo and install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_key_here
   ```
   Get a key at [openrouter.ai](https://openrouter.ai).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | API base URL |
| `LLM_MODEL` | `qwen/qwen3-coder:free` | Model to use |

## Usage

```bash
./run.sh -p "your prompt here"
```

**Examples:**

```bash
./run.sh -p "Read main.py and explain what it does"
./run.sh -p "Create a file called hello.py that prints Hello World"
./run.sh -p "List all python files in the current directory"
```
