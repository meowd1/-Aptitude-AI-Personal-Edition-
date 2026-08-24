#!/bin/bash
# Checks ollama is running, pulls models if missing, starts backend + frontend

echo "Checking Ollama models (used for embeddings and fallback)..."
ollama list | grep -q "qwen2.5:7b-instruct" || ollama pull qwen2.5:7b-instruct
ollama list | grep -q "nomic-embed-text" || ollama pull nomic-embed-text

echo ""
echo "Note: This app uses OmniRoute by default for LLM completions (http://localhost:20128/v1)."
echo "If OmniRoute is not running, please start it with 'omniroute' in a separate terminal,"
echo "or override LLM_BASE_URL to point directly to Ollama: 'export LLM_BASE_URL=http://localhost:11434/v1'"
echo ""

(cd backend && uvicorn main:app --reload --port 8000) &
(cd frontend && npm run dev) &
wait
