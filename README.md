# Mentis

A chatbot that builds a **Theory of Mind** (ToM) knowledge graph from conversations. It uses large language models (via Ollama) to extract mental states — beliefs, desires, intentions, emotions, and plans — and stores them in a structured knowledge graph using either GraphML or RDF/Turtle format.

> **NOTE** This is an educational project — a practical exploration of ToM and knowledge graphs.

## Features

- **Theory of Mind extraction**: Automatically identifies and tracks mental states from conversation using LLM
- **Knowledge Graph storage**: Persists data in GraphML or RDF/Turtle format
- **Context-aware responses**: Chatbot responses incorporate stored ToM information
- **CLI interface**: Interactive chat with model selection and debug mode

## Requirements

- Python 3.14+
- [Ollama](https://ollama.com/) running locally with at least one model pulled

## Usage

Start an interactive chat session:

```bash
uv run mentis
```

### Command-line options

Run the command below to get information about the available CLI options.

```bash
uv run mentis --help
```

## FAQ

**Q: What does "Mentis" mean?**

A: "Mentis" is Latin for "of mind" — reflecting the project's focus on ToM, which is the ability to attribute mental states (beliefs, intentions, desires, emotions, knowledge) to oneself and others. The name captures the core purpose: building a mental model of conversation participants.
