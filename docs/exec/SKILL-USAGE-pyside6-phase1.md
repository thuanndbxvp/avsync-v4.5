# SKILL USAGE — pyside6-phase1

> Theo skill `.ai-pipeline/skills/code.md`. Log các skill + CodeGraph tool sử dụng theo từng step.

## Phase 0 — Pre-Audit
- **Skill `.ai-pipeline/skills/code.md`** (Tier-2 main) — đọc để nắm 8-step loop
- **Skill `.ai-pipeline/skills/audit.md`** — đọc để hiểu checklist audit
- **Manual grep** trên toàn repo để đối chiếu entry points (run.bat, preflight.py, build_release.bat)
- **Đầu ra**: `docs/plan/AUDIT-REPORT-pyside6-phase1.md` (từ chối code ban đầu, chờ Q&A)

## Phase 1 — Triển khai (đang chờ)
- (đang chờ update theo từng step)

## Phase 2 — Triển khai (đã hoàn tất)
- **Skill `code.md`** — 8-STEP EXECUTION LOOP, copy-paste verbatim từ MSEW
- **Skill `audit.md`** — Phase 1 (smoke test), Phase 2 (MSEW adherence), Phase 5 (anti-hallucination)
- **Skill `anti-hallucination.md`** — check comments giả định (`should work/probably/seems`)
- **Skill `python-project.md`** — import structure & package init
- **CodeGraph**: thử gọi nhưng daemon không khả dụng trong session này → fall back sang manual grep với 2 query (import `ui` và import `app_legacy`)

## Kết quả triển khai
- 7/7 step DONE
- 5 file mới/sửa, 1 file rename
- Linter PASS (AST + py_compile), GUI smoke PASS
- 2 preflight FAIL là pre-existing (LICENSE_ENABLED=False, ffmpeg PATH thiếu), không liên quan Phase 1
