# JobTrackerSG

Ready-to-deploy Flask job tracking app for customs declaration jobs.

## Quick start (local)

1. Create virtualenv and install:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
2. Initialize DB (seeds admin + 25 users):
```bash
export FLASK_APP=app.py
flask initdb
```
3. Run locally:
```bash
python app.py
```

Admin: username `admin`, password `admin123`
Staff: `user01`..`user25` passwords `Pass01!`..`Pass25!`

## Deploy on Render (quick)
1. Push this repo to GitHub.
2. On Render, create a new Web Service connected to repo.
3. Build command: leave empty
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 3`
5. Set environment variable `SECRET_KEY` to a long random string.
6. (Run `flask initdb` once before or include startup script to initialize DB.)

