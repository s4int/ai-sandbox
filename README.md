# ai-sandbox

Scratching the surface of Agentic AI

## Prerequisites

- macOS (OSX)
- [Homebrew](https://brew.sh/) package manager

## Setup Instructions for macOS

### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Ollama

Ollama provides local LLM capabilities for the project.

```bash
brew install ollama
```

Start the Ollama service:

```bash
ollama serve
```

In a new terminal, pull a model (e.g., llama3.1:8b):

```bash
ollama pull llama3.1:8b
```

You can verify the installation:

```bash
ollama list
```

### 3. Install uv

uv is a fast Python package installer and resolver.

```bash
brew install uv
```

Verify the installation:

```bash
uv --version
```

### 4. Clone and Setup the Project

Clone the repository (if you haven't already):

```bash
git clone <repository-url>
cd ai-sandbox
```

Sync all project dependencies:

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Lock dependencies in `uv.lock`

### 5. Run the Project


Run with development tools (e.g., linting):

```bash
uv run ruff check .
uv run ruff format .
```

## Project Structure

- `pyproject.toml` - Project dependencies and configuration
- `.cursor/rules/` - Development guidelines and standards

## Troubleshooting

### Ollama not running

If you get connection errors, make sure Ollama is running:

```bash
ollama serve
```

### uv sync fails

Try clearing the cache and syncing again:

```bash
rm -rf .venv
uv sync
```
