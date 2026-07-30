"""services.config_service — Load/Save config.local.json (M6a).

UI Settings tab + UI Prompt tab + UI Render tab cần share cấu hình:
  - Profiles (style visual profile per channel)
  - API keys (per provider)
  - Provider defaults (provider + model mặc định)
  - Channel (Brand DNA)

File location: <project_root>/config.local.json — NGANG với tab_prompt.py cũ đang
đọc (giữ backward-compat với ai đã có file này).

API:
  ConfigService.instance()  -> singleton
  .load()                  -> dict (đã merged với default fallback)
  .save(data)              -> ghi file + cập nhật cache
  .get(key, default)       -> shortcut
  .set(key, value)         -> shortcut, auto-save
"""
from __future__ import annotations

import copy
import json
import os
from typing import Any


# ----------------------------------------------------------------------------
# Defaults — đảm bảo mọi key UI đọc đều có fallback
# ----------------------------------------------------------------------------
DEFAULT_CONFIG: dict = {
    "profiles": {
        "Người que": "Default stick-figure minimalist style. Bold outlines, simple shapes, vivid colors.",
        "Tâm linh": "Soft pastel mystical vibe. Floating particles, gentle rim light, ethereal mood.",
        "Tài chính (Minimal)": "Clean corporate look. Blue/grey palette, minimalist charts, sharp typography.",
        "Phong cách 3D": "Modern 3D cinematic render. Volumetric lighting, depth-of-field, high detail.",
    },
    "api_keys": {
        "gemini": "",
        "openai": "",
        "anthropic": "",
    },
    "providers": {
        # Mặc định: gemini + model 3.5 flash (rẻ, nhanh)
        "default_provider": "gemini",
        "models": {
            "gemini": "gemini-2.0-flash-exp",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-sonnet-latest",
        },
    },
    "channels": {
        # Brand DNA per channel (user save từ Render tab M5)
        "default": {
            "color_preset": "none",
            "vignette": False,
            "grain": False,
            "logo_pos": "br",
            "logo_shape": "round",
        }
    },
    "voice": {
        "tts_provider": "gtts",
        "language": "vi",
    },
    "subtitle": {
        "font": "Arial Black",
        "size": 52,
        "color": "#FFFFFF",
        "outline_color": "#000000",
        "mode": "word",
    },
}


# Path: project root (cha của services/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.local.json")


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge 2 dict, ưu tiên override; merge recursive với dict lồng nhau."""
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


class ConfigService:
    """Singleton load/save config.local.json."""

    _instance: "ConfigService | None" = None

    def __init__(self):
        self._data: dict = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded = False

    # ----------------------------------------------------------------- Singleton
    @classmethod
    def instance(cls) -> "ConfigService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ----------------------------------------------------------------- IO
    def load(self) -> dict:
        """Đọc config từ file (nếu có) merged với defaults. An toàn khi file missing."""
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                    raw = json.load(f)
                self._data = _deep_merge(DEFAULT_CONFIG, raw)
            except Exception:
                # file corrupted -> dùng defaults + log stderr (UI sẽ thấy nếu connect)
                import sys
                print(f"[ConfigService] WARN: cannot read {CONFIG_PATH}, using defaults",
                      file=sys.stderr)
                self._data = copy.deepcopy(DEFAULT_CONFIG)
        else:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded = True
        return self._data

    def save(self, data: dict | None = None) -> None:
        """Ghi dict hiện tại (hoặc `data` nếu truyền) ra file JSON."""
        payload = copy.deepcopy(data) if data is not None else copy.deepcopy(self._data)
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            if data is not None:
                self._data = payload
        except Exception as e:
            import sys
            print(f"[ConfigService] ERROR saving config: {e}", file=sys.stderr)
            raise

    # ----------------------------------------------------------------- API tiện
    def get(self, key: str, default: Any = None) -> Any:
        """Đọc 1 key hỗ trợ dotted path: 'providers.models.gemini'."""
        if not self._loaded:
            self.load()
        parts = key.split(".")
        cur: Any = self._data
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return default
        return cur

    def set(self, key: str, value: Any, *, auto_save: bool = True) -> None:
        """Set key dotted path; auto_save=True (default) sẽ ghi file ngay."""
        if not self._loaded:
            self.load()
        parts = key.split(".")
        cur = self._data
        for p in parts[:-1]:
            if p not in cur or not isinstance(cur[p], dict):
                cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = value
        if auto_save:
            self.save()

    def reset(self) -> None:
        """Reset về defaults + xoá file (dùng cho Settings > Reset)."""
        self._data = copy.deepcopy(DEFAULT_CONFIG)
        if os.path.isfile(CONFIG_PATH):
            try:
                os.remove(CONFIG_PATH)
            except Exception:
                pass


# Backward-compat helper cho tab_prompt.py cũ vẫn import trực tiếp
def load_config() -> dict:
    """Hàm tiện: trả về dict đã merge defaults. Tương đương ConfigService.instance().load()."""
    return ConfigService.instance().load()