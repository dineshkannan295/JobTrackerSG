#!/bin/bash
# Simple helper script for initializing DB then starting the app locally (or use in CI)
export FLASK_APP=app.py
pip install -r requirements.txt
flask initdb
# start the app
gunicorn app:app --bind 0.0.0.0:$PORT --workers 3
