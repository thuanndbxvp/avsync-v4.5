import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

from src.ai_write_x.web.app import app
import uvicorn

uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning", access_log=False)
