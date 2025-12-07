#!/usr/bin/env bash
# quick runner for local development
export $(grep -v '^#' .env | xargs)
uvicorn app.main:app --reload --port 9000
#uvicorn app.main:app --port 9000