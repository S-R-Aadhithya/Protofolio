# Protofolio Backend

Agentic RAG portfolio generator — Flask API with multi-agent LLM Council and Mem0 memory.

## Stack
- Python / Flask
- PostgreSQL (user metadata)
- Mem0 (AI memory layer)
- OpenAI GPT (LLM Council)

## Setup
```bash
pip install -r requirements.txt
python run.py
```

## CI/CD
Pipeline runs automatically on push via `.gitlab-ci.yml`:
- **build** — install dependencies
- **test** — lint + unit tests + integration tests
- **deploy** — auto-deploy to Render on `develop`, manual on `main`

## Branch Strategy
`main` → production | `develop` → staging | `feature/*` → development
