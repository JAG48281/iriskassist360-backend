release: alembic upgrade head && python seed.py
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
