# wechat-personal-chatbot

Fast WeChat personal chatbot using prompt engineering (no model fine-tuning required).

## Features

- Parse WeChat-like chat text history
- Extract representative conversation examples and style profile
- Build few-shot prompt templates from real chat data
- Chat interactively with OpenAI / Claude / Ollama backends

## Files

- `sample_chat_data.txt` - sample WeChat text format
- `data_processor.py` - chat parsing + profile extraction
- `prompt_builder.py` - system prompt and few-shot builder
- `chatbot.py` - backend API client + chat context logic
- `main.py` - CLI entrypoint
- `.env.example` - backend config template
- `requirements.txt` - minimal dependencies

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

- `LLM_BACKEND=openai` or `claude` or `ollama`
- corresponding API key / endpoint values

## Initialize Personal Profile

```bash
python main.py --init sample_chat_data.txt --user 小明
```

This creates `personal_profile.json` with style stats + few-shot examples.

## Start Chat

```bash
python main.py
```

Type `exit` or `quit` to stop.
