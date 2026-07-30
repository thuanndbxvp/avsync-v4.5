"""Split translations_complete.json into per-locale files."""
import json
from pathlib import Path

src = Path("translations_complete.json")
out_dir = Path("src/ai_write_x/web/locales")
out_dir.mkdir(parents=True, exist_ok=True)

with src.open(encoding="utf-8") as fh:
    catalog = json.load(fh)

per_lang = {"zh": {}, "vi": {}, "en": {}, "zh-CN": {}}

for key, translations in catalog.items():
    if not isinstance(translations, dict):
        continue
    for lang in per_lang:
        val = translations.get(lang)
        if val:
            per_lang[lang][key] = val

for lang, data in per_lang.items():
    out = out_dir / f"{lang}.json"
    with out.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"{lang}: {len(data)} entries -> {out}")

# Verify against i18n_keys_used.json
with open("i18n_keys_used.json", encoding="utf-8") as fh:
    used_keys = set(json.load(fh))

for lang in per_lang:
    missing = used_keys - set(per_lang[lang].keys())
    extra = set(per_lang[lang].keys()) - used_keys
    print(f"{lang}: missing={len(missing)} extra={len(extra)}")