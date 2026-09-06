#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama no está instalado. Instálalo desde https://ollama.com" >&2
  exit 1
fi

ollama pull llama3.2:3b
ollama pull nomic-embed-text

echo "Modelos listos: llama3.2:3b + nomic-embed-text"
