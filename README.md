# LLM Engineering Labs

> A practical, hands-on collection of notebooks covering LLM integration — from basic completions to production-ready agentic systems.

This repo is the companion resource for the talk **"Intégrez des LLM à vos applications"** by [Your Name], LLM Engineer. It goes beyond the live demos to provide a comprehensive reference for developers looking to integrate LLMs into real applications.

---

## Getting Started

### Prerequisites

- [Deno](https://deno.land/) (for TypeScript notebooks)
- [Python 3.10+](https://www.python.org/) (for Python notebooks)
- An OpenAI API key

### Setup

1. Clone the repo

   ```bash
   git clone https://github.com/yourusername/llm-engineering-labs.git
   cd llm-engineering-labs
   ```

2. Copy the environment file and fill in your API key

   ```bash
   cp .env.example .env
   ```

3. Install the Deno Jupyter kernel (for TypeScript notebooks)

   ```bash
   deno jupyter --install
   ```

4. Install Python dependencies (for Python notebooks)
   ```bash
   pip install openai langchain langchain-openai langgraph pydantic python-dotenv jupyter
   ```

---

## 📚 Notebooks

### 01 — Foundations

| Notebook                       | Description                                    | TS                                                          | Python                                                                                                                                                                                                                                                                             |
| ------------------------------ | ---------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Completion & Prompting         | Basic LLM calls, message roles, system prompts | [▶ TS](01-fondations/ts/completion.ipynb)                   | [▶ py](01-fondations/py/completion.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/01-fondations/py/completion.ipynb)                                     |
| Structured Output — Generation | Generate typed, schema-validated responses     | [▶ TS](01-fondations/ts/structured-output-generation.ipynb) | [▶ py](01-fondations/py/structured-output-generation.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/01-fondations/py/structured-output-generation.ipynb) |
| Structured Output — Extraction | Extract structured data from unstructured text | [▶ TS](01-fondations/ts/structured-output-extraction.ipynb) | [▶ py](01-fondations/py/structured-output-extraction.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/01-fondations/py/structured-output-extraction.ipynb) |
| Chain of Thought               | Step-by-step reasoning for complex tasks       | [▶ TS](01-fondations/ts/chain-of-thought.ipynb)             | [▶ py](01-fondations/py/chain-of-thought.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/01-fondations/py/chain-of-thought.ipynb)                         |

---

### 02 — Augmentation

#### Memory

| Notebook          | Description                                       | TS                                                         | Python                                                                                                                                                                                                                                                                           |
| ----------------- | ------------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| In-context Memory | Managing conversation history and context window  | [▶ TS](02-augmentation/memoire/ts/in-context-memory.ipynb) | [▶ py](02-augmentation/memoire/py/in-context-memory.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/memoire/py/in-context-memory.ipynb) |
| Summary Memory    | Compressing past exchanges into a rolling summary | [▶ TS](02-augmentation/memoire/ts/summary-memory.ipynb)    | [▶ py](02-augmentation/memoire/py/summary-memory.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/memoire/py/summary-memory.ipynb)       |
| Vector Memory     | Long-term memory with semantic retrieval          | [▶ TS](02-augmentation/memoire/ts/vector-memory.ipynb)     | [▶ py](02-augmentation/memoire/py/vector-memory.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/memoire/py/vector-memory.ipynb)         |

#### Function Calling

| Notebook           | Description                                        | TS                                                                 | Python                                                                                                                                                                                                                                                                                           |
| ------------------ | -------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Function Calling   | Tool declaration, execution loop, result injection | [▶ TS](02-augmentation/function-calling/ts/function-calling.ipynb) | [▶ py](02-augmentation/function-calling/py/function-calling.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/function-calling/py/function-calling.ipynb) |
| Multi-tool Calling | Handling multiple tools and parallel calls         | [▶ TS](02-augmentation/function-calling/ts/multi-tool.ipynb)       | [▶ py](02-augmentation/function-calling/py/multi-tool.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/function-calling/py/multi-tool.ipynb)             |

#### RAG

| Notebook          | Description                                           | TS                                                     | Python                                                                                                                                                                                                                                                                   |
| ----------------- | ----------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Naive RAG         | Basic retrieve-augment-generate pipeline              | [▶ TS](02-augmentation/rag/ts/naive-rag.ipynb)         | [▶ py](02-augmentation/rag/py/naive-rag.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/rag/py/naive-rag.ipynb)                 |
| Semantic Chunking | Splitting documents by meaning, not size              | [▶ TS](02-augmentation/rag/ts/semantic-chunking.ipynb) | [▶ py](02-augmentation/rag/py/semantic-chunking.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/rag/py/semantic-chunking.ipynb) |
| Reranking         | Improving retrieval precision with a reranker         | [▶ TS](02-augmentation/rag/ts/reranking.ipynb)         | [▶ py](02-augmentation/rag/py/reranking.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/rag/py/reranking.ipynb)                 |
| HyDE              | Hypothetical Document Embeddings for better retrieval | [▶ TS](02-augmentation/rag/ts/hyde.ipynb)              | [▶ py](02-augmentation/rag/py/hyde.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/02-augmentation/rag/py/hyde.ipynb)                           |

---

### 03 — Agentic Systems

#### Patterns

| Notebook         | Description                                              | TS                                                    | Python                                                                                                                                                                                                                                                                 |
| ---------------- | -------------------------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ReAct Agent      | Reasoning + Acting loop with tool use                    | [▶ TS](03-agentique/patterns/ts/react-agent.ipynb)    | [▶ py](03-agentique/patterns/py/react-agent.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/patterns/py/react-agent.ipynb)       |
| Reflection       | Self-critique and iterative improvement loop             | [▶ TS](03-agentique/patterns/ts/reflection.ipynb)     | [▶ py](03-agentique/patterns/py/reflection.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/patterns/py/reflection.ipynb)         |
| Manager / Worker | Orchestrator dispatching to specialized sub-agents       | [▶ TS](03-agentique/patterns/ts/manager-worker.ipynb) | [▶ py](03-agentique/patterns/py/manager-worker.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/patterns/py/manager-worker.ipynb) |
| Streaming        | Real-time token streaming and intermediate state display | [▶ TS](03-agentique/patterns/ts/streaming.ipynb)      | [▶ py](03-agentique/patterns/py/streaming.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/patterns/py/streaming.ipynb)           |
| Runtime Config   | Dynamic agent configuration at runtime                   | [▶ TS](03-agentique/patterns/ts/runtime-config.ipynb) | [▶ py](03-agentique/patterns/py/runtime-config.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/patterns/py/runtime-config.ipynb) |

#### Use Cases

| Notebook              | Description                                                           | TS                                                            | Python                                                                                                                                                                                                                                                                                 |
| --------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| User Story Agent      | Reflection-based agent for agile user story writing                   | [▶ TS](03-agentique/use-cases/ts/user-story-agent.ipynb)      | [▶ py](03-agentique/use-cases/py/user-story-agent.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/use-cases/py/user-story-agent.ipynb)           |
| Code Review Agent     | Automated code review with structured feedback                        | [▶ TS](03-agentique/use-cases/ts/code-review-agent.ipynb)     | [▶ py](03-agentique/use-cases/py/code-review-agent.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/use-cases/py/code-review-agent.ipynb)         |
| Tech Watch Agent      | Automated technology monitoring and synthesis                         | [▶ TS](03-agentique/use-cases/ts/tech-watch-agent.ipynb)      | [▶ py](03-agentique/use-cases/py/tech-watch-agent.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/use-cases/py/tech-watch-agent.ipynb)           |
| Test Generation Agent | Automated unit test generation from source code                       | [▶ TS](03-agentique/use-cases/ts/test-generation-agent.ipynb) | [▶ py](03-agentique/use-cases/py/test-generation-agent.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/use-cases/py/test-generation-agent.ipynb) |
| RAG + Agent Pipeline  | Combining retrieval-augmented generation with agentic decision-making | [▶ TS](03-agentique/use-cases/ts/rag-agent-pipeline.ipynb)    | [▶ py](03-agentique/use-cases/py/rag-agent-pipeline.ipynb) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yourusername/llm-engineering-labs/blob/main/03-agentique/use-cases/py/rag-agent-pipeline.ipynb)       |

---

## 🎤 Related Talks

- **Intégrez des LLM à vos applications** — From completion to agentic systems _(this repo)_
- **RAG to Riches** — Advanced RAG techniques beyond naive retrieval

---

## 📄 License

[MIT](LICENSE)
