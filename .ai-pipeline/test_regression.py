"""Regression: verify the whole web app + crew_main still imports cleanly."""
import sys
sys.path.insert(0, ".")

# Run the actual app init the same way main.py does
from src.ai_write_x.config.config import Config
from src.ai_write_x.crew_main import run, ai_write_x_run, run_crew_in_process
from src.ai_write_x.web.app import app
from src.ai_write_x.web.i18n import t

config = Config.get_instance()
print(f"[OK] Config: humanize_enabled={config.humanize_enabled}")
print(f"[OK] crew_main: run, ai_write_x_run, run_crew_in_process")
print(f"[OK] FastAPI app: {len(app.routes)} routes")
print(f"[OK] i18n t() works: {t('m_056c9b52', lang='vi')!r}")