# Session Notes — 2026-07-28

## Task (b): i18n system rebuild
Re-created the lightweight translation catalog deleted in the last `git checkout`.
Only the backend was built — no template tags were injected (templates still
ship untranslated Chinese, intentional, requires a follow-up session).

### Files added
- `src/ai_write_x/web/i18n.py` (5 KB) — `t(key, lang, default)` + cache + thread lock + Accept-Language parsing + Jinja env wiring (`register_jinja_env`).
- `src/ai_write_x/web/locales/zh.json`, `zh-CN.json`, `vi.json`, `en.json` — flat dicts, 201 entries each, derived from the existing `translations_complete.json` via `.ai-pipeline/build_locales.py`.

### Files modified
- `src/ai_write_x/web/app.py` (+19 / -1) — `register_jinja_env(templates)` plus two endpoints:
  - `GET /api/i18n/locales` → `{locales: ["zh", "zh-CN", "vi", "en"], default: "zh"}`
  - `GET /api/i18n/translate?key=&lang=` → `{key, lang, value}`

### Verified live
```
200 /api/i18n/locales
200 /api/i18n/translate?key=m_056c9b52&lang=vi → "Vui lòng chọn một danh mục trước"
200 / (UI)
```

## Task (c): wire humanize_script into the generate pipeline

### Bug fix (DNA)
`src/ai_write_x/niches/dna_loader.py:_parse_routing_rules` was loading the
regex strings from YAML without unescaping the YAML double-backslash.
Example: line 200 of `docs/dna/niche-finance-vn.md` had
`"(\\d+)\\s*(nghề|cách|...)"` — the loader stored the two backslashes
verbatim, so `re.search("\\d+", "7 thói quen...")` searched for a literal
`\d+` substring that never appears. Niche-rule scoring quietly fell through
to the base `DNARouter` at confidence 0.75.

**Fix**: added `_unescape_regex()` helper (1-line helper using `s.replace("\\\\", "\\")`,
not `codecs.decode("unicode_escape")` which over-interpreted `\d` as `\r`) and
applied to both `match_keywords` and `hook_priority`.

**Smoke test 8 topics**: niche_rule fires correctly with 77-95% confidence for:
- "7 thói quen tài chính..." → listicle / story / `rule-listicle-numbers`
- "Top 5 cách tiết kiệm..." → listicle / story / `rule-listicle-numbers`
- "Làm gì khi bị áp lực..." → psychology / question / `rule-question-emotional`
- Others → fallback to legacy rules (expected for non-matching patterns).

### Humanize wire-up

#### Files modified
- `src/ai_write_x/config/config.py`:
  - Add `Tuple` to typing import.
  - Add `Config.humanize_enabled: bool = True` and `Config.humanize_hook_type: str = "auto"` in `__init__`.
  - Add module-level `get_humanize_config()` helper.

- `src/ai_write_x/crew_main.py:run()`:
  - After `workflow.execute()` returns, attempt to apply `humanize_script`.
  - On success: mutate `result["formatted_content"].content`, store raw
    payload under `formatted_content_raw`, set `humanize_applied=True`,
    `humanize_hook_type=…`, `ai_tells_detected=[…]`, and rewrite the
    on-disk saved file from `result["save_result"]["path"]`.
  - On failure: log a warning, leave result untouched (the generation
    succeeds even if the humanize pass errors).

#### Untouched on purpose
- `src/ai_write_x/core/humanize_script.py` — module is solid (see `AI_TELL_REPLACEMENTS`, `HOOK_REPLACEMENTS`, etc.). No changes.
- `src/ai_write_x/services/ai/{dna_router,prompt_builder}.py` — already complete.
- `src/ai_write_x/niches/{router,profile,dna_loader}.py` — only the one `_unescape_regex` helper added.

### Smoke test result (mocked workflow)
```
[OK] Config has flags: enabled=True, hook_type=auto
[OK] humanize_pass applied (hook=auto, ai_tells=6, chars 268 -> 226)
[OK] saved file matches humanized content (226 bytes)

BEFORE:                                       AFTER:
| Đầu tiên, tôi sẽ phân tích vấn đề.         | Tôi nói thật nhé: tôi sẽ phân tích vấn đề.
| Trước tiên, bạn cần hiểu rằng...            | bạn cần hiểu rằng đầu tư là một quyết định...
| Tóm lại, việc lập kế hoạch...               | việc lập kế hoạch tài chính sẽ giúp bạn tự do hơn.
| Vì vậy, hãy cùng tìm hiểu...                | Nên cách tiết kiệm tiền hiệu quả.
| Nói cách khác, nên bắt đầu...               | Tức là nên bắt đầu từ những thói quen nhỏ.

[OK] humanize_enabled=False skips pass (raw result, no humanize_applied flag)
```

### Servers running
- shell `700600` (PID 20836) → previous live server, killed
- shell `700601` (PID 18408 → child PID 20112 owns port 8000) → new live server with all three tasks applied

### Files NOT changed (and why)
- Templates under `src/ai_write_x/web/templates/**` — no `{{ t(...) }}` or `data-i18n` tags were added. Out of scope for this session (task (b) was backend-only per your direction).
- `src/ai_write_x/crew_main.py:FinanceScriptCrew` — does not exist; the original
  `ai_write_x_main` flow was left as-is because writing a new 200-line CrewAI
  class from scratch violates your "đừng viết mới" rule.
- Untracked scratch files in `.ai-pipeline/` (build_locales.py, test_*.py,
  smoke_output.txt, etc.) — utility scripts, not part of the repo.

### Known follow-up items (not done)
1. Wire `humanize_enabled` toggle into the UI (config-manager panel).
2. Retrofit `{{ t('m_xxx') }}` into templates so the UI actually shows translations.
3. Build `FinanceScriptCrew` if you want topic/branch/hook routing to drive CrewAI agents separately from the news-driven flow.
4. Update `niche-finance-vn.md` regex `^vì sao\s+.{3,60}\s+(đóng|...)` so topics like "Vì sao giới trẻ ngày càng khó mua nhà" hit `rule-vì-sao-phenomenon` instead of falling through.